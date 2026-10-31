"""Thin wrapper over the herdr CLI: snapshot reads and token writes."""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from typing import Any, Dict, List, Mapping, Sequence

from .plan import TokenUpdate

LOG = logging.getLogger(__name__)

SOURCE_ID = "herdr-agents-group"
COMMAND_TIMEOUT_SECONDS = 5


class HerdrError(Exception):
    """A herdr CLI call failed, timed out, or returned something unexpected."""


def herdr_binary() -> str:
    candidate = os.environ.get("HERDR_BIN_PATH") or shutil.which("herdr")
    if not candidate:
        raise HerdrError("herdr binary not found: set HERDR_BIN_PATH or put herdr on PATH")
    return candidate


def _run(arguments: Sequence[str]) -> str:
    command = [herdr_binary(), *arguments]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise HerdrError(f"'herdr {arguments[0]} {arguments[1]}' timed out after {COMMAND_TIMEOUT_SECONDS}s") from error
    except OSError as error:
        raise HerdrError(f"could not start {command[0]}: {error}") from error
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise HerdrError(f"'herdr {' '.join(arguments[:2])}' exited {completed.returncode}: {detail[:300]}")
    return completed.stdout


def read_snapshot() -> Dict[str, Any]:
    output = _run(["api", "snapshot"])
    try:
        snapshot = json.loads(output)["result"]["snapshot"]
    except (ValueError, KeyError, TypeError) as error:
        raise HerdrError(f"unexpected 'herdr api snapshot' output: {output[:200]!r}") from error
    if not isinstance(snapshot, dict):
        raise HerdrError("'herdr api snapshot' returned a non-object snapshot")
    return snapshot


def _token_arguments(update: TokenUpdate) -> List[str]:
    arguments: List[str] = []
    for name in update.clear_tokens:
        arguments += ["--clear-token", name]
    for name, value in sorted(update.set_tokens.items()):
        arguments += ["--token", f"{name}={value}"]
    return arguments


def write_pane_tokens(pane_id: str, update: TokenUpdate) -> None:
    _run(["pane", "report-metadata", pane_id, "--source", SOURCE_ID, *_token_arguments(update)])


def write_workspace_tokens(workspace_id: str, update: TokenUpdate) -> None:
    _run(["workspace", "report-metadata", workspace_id, "--source", SOURCE_ID, *_token_arguments(update)])


def reload_config() -> None:
    _run(["server", "reload-config"])


def notify(title: str, body: str) -> None:
    """Best effort: a failed notification must not hide the real outcome."""
    try:
        _run(["notification", "show", title, "--body", body, "--sound", "none"])
    except HerdrError as error:
        LOG.warning("notify.failed", extra={"context": {"title": title, "error": str(error)}})


def current_tokens(items: Sequence[Mapping[str, Any]], id_field: str) -> Dict[str, Mapping[str, Any]]:
    return {item[id_field]: item.get("tokens") or {} for item in items if item.get(id_field)}
