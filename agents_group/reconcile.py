"""One idempotent pass: read the snapshot, then write only the tokens that changed."""

from __future__ import annotations

import fcntl
import logging
import time
from pathlib import Path
from typing import Callable, Dict, Mapping

from . import herdr_cli
from .colors import PALETTE, assign_slots, load_slots, save_slots
from .plan import Plan, build_plan, diff_tokens

LOG = logging.getLogger(__name__)

MAX_PASSES_PER_RUN = 5


def _apply(plan: Plan, snapshot: Mapping, writer_pane: Callable, writer_workspace: Callable) -> Dict[str, int]:
    """Send every needed update; one failing pane is logged and does not stop the others."""
    counts = {"written": 0, "failed": 0}
    targets = [
        (plan.workspace_tokens, herdr_cli.current_tokens(snapshot.get("workspaces") or [], "workspace_id"), writer_workspace),
        (plan.pane_tokens, herdr_cli.current_tokens(snapshot.get("panes") or [], "pane_id"), writer_pane),
    ]
    for desired_by_id, current_by_id, writer in targets:
        for target_id, desired in desired_by_id.items():
            update = diff_tokens(current_by_id.get(target_id), desired)
            if update.is_empty:
                continue
            try:
                writer(target_id, update)
                counts["written"] += 1
            except herdr_cli.HerdrError as error:
                counts["failed"] += 1
                LOG.error("tokens.write_failed", extra={"context": {"target": target_id, "error": str(error)}})
    return counts


def reconcile_once(slots_path: Path, grouped: bool, divider_width: int) -> Dict[str, int]:
    started = time.monotonic()
    snapshot = herdr_cli.read_snapshot()
    workspace_ids = [w["workspace_id"] for w in snapshot.get("workspaces") or [] if w.get("workspace_id")]
    slots = assign_slots(load_slots(slots_path), workspace_ids, len(PALETTE))
    save_slots(slots_path, slots)
    plan = build_plan(snapshot, slots, grouped=grouped, divider_width=divider_width)
    counts = _apply(plan, snapshot, herdr_cli.write_pane_tokens, herdr_cli.write_workspace_tokens)
    LOG.info(
        "reconcile.done",
        extra={"context": {**counts, "workspaces": len(workspace_ids), "ms": round((time.monotonic() - started) * 1000)}},
    )
    return counts


def clear_all(snapshot: Mapping) -> Dict[str, int]:
    """Remove every token this plugin owns, keeping other plugins' tokens."""
    empty = Plan(
        workspace_tokens={w: {} for w in herdr_cli.current_tokens(snapshot.get("workspaces") or [], "workspace_id")},
        pane_tokens={p: {} for p in herdr_cli.current_tokens(snapshot.get("panes") or [], "pane_id")},
    )
    return _apply(empty, snapshot, herdr_cli.write_pane_tokens, herdr_cli.write_workspace_tokens)


def run_coalesced(state_dir: Path, run_pass: Callable[[], object]) -> None:
    """Run passes under a lock; events arriving meanwhile only mark a pending flag.

    The lock holder keeps draining the flag, and re-checks it after releasing,
    so a burst of events costs at most a few passes instead of one per event.
    """
    state_dir.mkdir(parents=True, exist_ok=True)
    pending = state_dir / "pending"
    pending.touch()
    passes = 0
    with open(state_dir / "reconcile.lock", "w") as lock:
        while pending.exists() and passes < MAX_PASSES_PER_RUN:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return
            try:
                while pending.exists() and passes < MAX_PASSES_PER_RUN:
                    pending.unlink(missing_ok=True)
                    passes += 1
                    run_pass()
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)
    if pending.exists():
        LOG.warning("reconcile.pass_limit", extra={"context": {"passes": passes}})
