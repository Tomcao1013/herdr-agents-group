"""Entry point for herdr events and actions."""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Sequence

from . import herdr_cli
from .colors import PALETTE, state_path
from .config_block import ConfigConflictError, install_block, is_grouped, render_block, uninstall_block
from .reconcile import clear_all, reconcile_once, run_coalesced

LOG = logging.getLogger("agents_group")

DIVIDER_WIDTH = 20
DEFAULT_CONFIG_PATH = Path.home() / ".config" / "herdr" / "config.toml"
NOTIFY_TITLE = "Agents group"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {"level": record.levelname.lower(), "event": record.getMessage(), **getattr(record, "context", {})}
        return json.dumps(entry, ensure_ascii=False)


def _setup_logging() -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    LOG.addHandler(handler)
    LOG.setLevel(logging.INFO)


def config_path() -> Path:
    override = os.environ.get("HERDR_CONFIG_PATH")
    return Path(override) if override else DEFAULT_CONFIG_PATH


def state_dir() -> Path:
    override = os.environ.get("HERDR_PLUGIN_STATE_DIR")
    return Path(override) if override else Path(tempfile.gettempdir()) / "herdr-agents-group"


def _read_config() -> str:
    try:
        return config_path().read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _write_config_with_backup(new_text: str) -> Path:
    """Back up the current config, then replace it atomically."""
    target = config_path()
    backup = target.with_name(f"{target.name}.bak-agents-group-{time.strftime('%Y%m%d-%H%M%S')}")
    if target.exists():
        backup.write_bytes(target.read_bytes())
    temporary = target.with_name(f".{target.name}.agents-group.tmp")
    temporary.write_text(new_text, encoding="utf-8")
    os.replace(temporary, target)
    return backup


def reconcile() -> None:
    slots = state_path(state_dir(), os.environ.get("HERDR_SOCKET_PATH", "default"))
    grouped = is_grouped(_read_config())
    run_coalesced(state_dir(), lambda: reconcile_once(slots, grouped=grouped, divider_width=DIVIDER_WIDTH))


def install_layout() -> None:
    current = _read_config()
    try:
        updated = install_block(current, render_block(PALETTE))
    except ConfigConflictError as error:
        herdr_cli.notify(NOTIFY_TITLE, f"Layout not installed: {error}")
        raise
    if updated == current:
        herdr_cli.notify(NOTIFY_TITLE, "Sidebar layout is already up to date.")
        return
    backup = _write_config_with_backup(updated)
    herdr_cli.reload_config()
    reconcile()
    herdr_cli.notify(NOTIFY_TITLE, f"Sidebar layout installed. Backup: {backup.name}")


def uninstall_layout() -> None:
    current = _read_config()
    updated = uninstall_block(current)
    if updated == current:
        herdr_cli.notify(NOTIFY_TITLE, "No plugin layout found in config.toml.")
        return
    backup = _write_config_with_backup(updated)
    herdr_cli.reload_config()
    clear_all(herdr_cli.read_snapshot())
    herdr_cli.notify(NOTIFY_TITLE, f"Sidebar layout removed. Backup: {backup.name}")


def clear_tokens() -> None:
    counts = clear_all(herdr_cli.read_snapshot())
    herdr_cli.notify(NOTIFY_TITLE, f"Cleared plugin tokens on {counts['written']} items.")


COMMANDS = {
    "reconcile": reconcile,
    "install-layout": install_layout,
    "uninstall-layout": uninstall_layout,
    "clear": clear_tokens,
}


def main(argv: Sequence[str]) -> int:
    _setup_logging()
    command = argv[0] if argv else "reconcile"
    handler = COMMANDS.get(command, reconcile)
    try:
        handler()
    except (herdr_cli.HerdrError, ConfigConflictError, OSError) as error:
        LOG.error("command.failed", extra={"context": {"command": command, "error": str(error)}})
        return 1
    return 0
