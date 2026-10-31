"""The marked block this plugin owns inside the user's herdr config.toml."""

from __future__ import annotations

import re
from typing import Sequence

BEGIN_MARKER = "# >>> herdr-agents-group >>>"
END_MARKER = "# <<< herdr-agents-group <<<"
OWNED_TABLES = ("ui.sidebar.agents", "ui.sidebar.spaces")
PRIORITY_SORT = re.compile(r'^\s*agent_panel_sort\s*=\s*"priority"', re.MULTILINE)


class ConfigConflictError(Exception):
    """The config already has something the block would clash with; nothing was written."""


def _table_header(table: str) -> re.Pattern:
    parts = r"\s*\.\s*".join(re.escape(part) for part in table.split("."))
    return re.compile(rf"^\s*\[\s*{parts}\s*\]", re.MULTILINE)


def _slots(prefix: str, palette: Sequence[str], style: str) -> str:
    return ", ".join(
        f'{{ token = "${prefix}{slot}", fg = "{color}"{style} }}'
        for slot, color in enumerate(palette, start=1)
    )


def render_block(palette: Sequence[str]) -> str:
    """Sidebar rows: one color slot per palette entry; herdr hides the empty ones."""
    names = _slots("ag_n", palette, "")
    dividers = _slots("ag_d", palette, ", dim = true")
    workspaces = _slots("ag_w", palette, ", bold = true")
    return "\n".join(
        [
            "# Managed by the herdr-agents-group plugin. Edit the plugin, not this block.",
            "[ui.sidebar.agents]",
            "row_gap = 0",
            "rows = [",
            f'  ["state_icon", {names}, {{ token = "$ag_kind", dim = true }}],',
            f"  [{dividers}],",
            "]",
            "",
            "[ui.sidebar.spaces]",
            "rows = [",
            f'  ["state_icon", {workspaces}],',
            '  ["branch", "git_status"],',
            "]",
        ]
    )


def _split(text: str):
    """(before, block, after) around the markers, or None when there is no block."""
    begin = text.find(BEGIN_MARKER)
    if begin == -1:
        return None
    end = text.find(END_MARKER, begin)
    if end == -1:
        raise ConfigConflictError(f"found '{BEGIN_MARKER}' without '{END_MARKER}'; fix config.toml by hand")
    after_start = end + len(END_MARKER)
    if text[after_start:after_start + 1] == "\n":
        after_start += 1
    return text[:begin], text[begin:after_start], text[after_start:]


def uninstall_block(text: str) -> str:
    parts = _split(text)
    if parts is None:
        return text
    before, _, after = parts
    return before.rstrip("\n") + "\n" + after if before.strip() else after


def install_block(text: str, block: str) -> str:
    """Add or replace the marked block; refuse if the user defines the same tables elsewhere."""
    outside = uninstall_block(text)
    for table in OWNED_TABLES:
        if _table_header(table).search(outside):
            raise ConfigConflictError(
                f"config.toml already defines [{table}] outside the plugin block; "
                "remove or merge it, then run the install action again"
            )
    base = outside if outside.endswith("\n") or not outside else outside + "\n"
    return f"{base}\n{BEGIN_MARKER}\n{block}\n{END_MARKER}\n"


def is_grouped(text: str) -> bool:
    """False when the agents panel uses the priority queue, where workspace groups don't exist."""
    return PRIORITY_SORT.search(text) is None
