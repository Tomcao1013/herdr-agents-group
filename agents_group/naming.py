"""Display names for agent rows and workspace dividers."""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any, Mapping, Optional

PI_TITLE_PREFIX = "π - "
PI_TITLE_BARE = "π"
UNKNOWN_KIND = "agent"
TITLE_SEPARATOR = " - "
RULE = "─"
ELLIPSIS = "…"
DIVIDER_LEAD = RULE * 2 + " "
JUMP_NUMBER_PREFIX = re.compile(r"^\[\d+\]\s*")


def display_width(text: str) -> int:
    """Terminal columns used by text: wide and fullwidth characters take two."""
    return sum(2 if unicodedata.east_asian_width(char) in ("W", "F") else 1 for char in text)


def _directory_names(agent: Mapping[str, Any]) -> frozenset:
    paths = (agent.get("cwd"), agent.get("foreground_cwd"))
    return frozenset(os.path.basename(path.rstrip("/")) for path in paths if path)


def _strip_directory_suffix(text: str, directories: frozenset) -> str:
    """Drop a trailing ' - <dir>' (and a text that is only '<dir>'): color already says the project."""
    if text in directories:
        return ""
    for directory in directories:
        suffix = TITLE_SEPARATOR + directory
        if directory and text.endswith(suffix):
            return text[: -len(suffix)].strip()
    return text


def _clean_title(title: str) -> str:
    if title == PI_TITLE_BARE:
        return ""
    if title.startswith(PI_TITLE_PREFIX):
        return title[len(PI_TITLE_PREFIX):].strip()
    return title


def _non_blank(value: Optional[object]) -> str:
    return value.strip() if isinstance(value, str) else ""


def display_name(agent: Mapping[str, Any]) -> str:
    """Name shown for an agent: topic, then cleaned terminal title, then agent kind."""
    directories = _directory_names(agent)
    tokens = agent.get("tokens") or {}
    topic = _strip_directory_suffix(_non_blank(tokens.get("topic")), directories)
    if topic:
        return topic
    title = _clean_title(_non_blank(agent.get("terminal_title_stripped")))
    title = _strip_directory_suffix(title, directories)
    if title:
        return title
    return _non_blank(agent.get("agent")) or UNKNOWN_KIND


def workspace_title(workspace: Mapping[str, Any]) -> str:
    """Workspace label without the '[n] ' jump-number prefix."""
    title = JUMP_NUMBER_PREFIX.sub("", _non_blank(workspace.get("label")))
    return title or f"workspace {workspace.get('number', '?')}"


def _truncate(text: str, max_width: int) -> str:
    if display_width(text) <= max_width:
        return text
    kept = []
    used = 0
    for char in text:
        width = display_width(char)
        if used + width > max_width - 1:
            break
        kept.append(char)
        used += width
    return "".join(kept) + ELLIPSIS


def divider_text(name: str, width: int) -> str:
    """'── name ────' padded with rule characters to exactly `width` columns."""
    name_budget = width - display_width(DIVIDER_LEAD) - 2
    label = _truncate(name, max(name_budget, 1))
    head = f"{DIVIDER_LEAD}{label} "
    return head + RULE * max(width - display_width(head), 1)
