"""Workspace color slots: first come, first served, remembered across runs."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, Mapping

LOG = logging.getLogger(__name__)

# rose, foam, iris from rose-pine, then green, blue, sand at similar saturation.
# love, gold and pine are left out on purpose: the status icons already use them.
PALETTE = ("#ebbcba", "#9ccfd8", "#c4a7e7", "#a6da95", "#8aadf4", "#e2c08d")
STATE_VERSION = 1
SESSION_KEY_LENGTH = 12


def _is_valid_slot(value: object, palette_size: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= palette_size


def assign_slots(
    previous: Mapping[str, object], workspace_ids: Iterable[str], palette_size: int
) -> Dict[str, int]:
    """Keep each open workspace's slot; give new ones the lowest free slot, or the least used one."""
    if palette_size < 1:
        raise ValueError(f"palette_size must be at least 1, got {palette_size}")
    ordered_ids = list(dict.fromkeys(workspace_ids))
    kept = {
        workspace_id: previous[workspace_id]
        for workspace_id in ordered_ids
        if _is_valid_slot(previous.get(workspace_id), palette_size)
    }
    usage = Counter(kept.values())
    assigned: Dict[str, int] = dict(kept)
    for workspace_id in ordered_ids:
        if workspace_id in assigned:
            continue
        slot = min(range(1, palette_size + 1), key=lambda candidate: (usage[candidate], candidate))
        assigned[workspace_id] = slot
        usage[slot] += 1
    return assigned


def session_key(socket_path: str) -> str:
    """Short stable key so each herdr session keeps its own slot file."""
    return hashlib.sha256(socket_path.encode("utf-8")).hexdigest()[:SESSION_KEY_LENGTH]


def state_path(directory: Path, socket_path: str) -> Path:
    return Path(directory) / f"slots-{session_key(socket_path)}.json"


def load_slots(path: Path) -> Dict[str, int]:
    """Read remembered slots; a missing or damaged file just means colors get reassigned."""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as error:
        LOG.warning("slots.unreadable", extra={"context": {"path": str(path), "error": str(error)}})
        return {}
    slots = raw.get("slots") if isinstance(raw, dict) else None
    if not isinstance(slots, dict):
        LOG.warning("slots.malformed", extra={"context": {"path": str(path)}})
        return {}
    return {
        key: value
        for key, value in slots.items()
        if isinstance(key, str) and isinstance(value, int) and not isinstance(value, bool)
    }


def save_slots(path: Path, slots: Mapping[str, int]) -> None:
    """Write atomically so a crash mid-write never leaves a half file behind."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"version": STATE_VERSION, "slots": dict(slots)}, indent=2, sort_keys=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=target.parent, prefix=target.name, suffix=".tmp", delete=False
    ) as handle:
        handle.write(payload)
        temporary = handle.name
    os.replace(temporary, target)
