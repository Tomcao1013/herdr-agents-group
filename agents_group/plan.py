"""Pure planning: which sidebar tokens every pane and workspace should carry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .naming import display_name, divider_text, workspace_title

# herdr keeps one token namespace per pane shared by every source, so all of
# our names carry this prefix and we never clear a token without it.
TOKEN_PREFIX = "ag_"
KIND_TOKEN = TOKEN_PREFIX + "kind"
MAX_NAME_CHARS = 80

Tokens = Mapping[str, str]


def name_token(slot: int) -> str:
    return f"{TOKEN_PREFIX}n{slot}"


def divider_token(slot: int) -> str:
    return f"{TOKEN_PREFIX}d{slot}"


def workspace_token(slot: int) -> str:
    return f"{TOKEN_PREFIX}w{slot}"


@dataclass(frozen=True)
class TokenUpdate:
    set_tokens: Tokens = field(default_factory=dict)
    clear_tokens: Tuple[str, ...] = ()

    @property
    def is_empty(self) -> bool:
        return not self.set_tokens and not self.clear_tokens


@dataclass(frozen=True)
class Plan:
    workspace_tokens: Mapping[str, Tokens]
    pane_tokens: Mapping[str, Tokens]


def _agent_tokens(agent: Mapping[str, Any], slot: int) -> Dict[str, str]:
    name = display_name(agent)[:MAX_NAME_CHARS]
    tokens = {name_token(slot): name}
    kind = agent.get("agent")
    if isinstance(kind, str) and kind and kind != name:
        tokens[KIND_TOKEN] = kind
    return tokens


def _groups(
    workspaces: Sequence[Mapping[str, Any]], agents: Sequence[Mapping[str, Any]]
) -> List[Tuple[Mapping[str, Any], List[Mapping[str, Any]]]]:
    """Agents per workspace in sidebar order.

    herdr's snapshot already lists agents in sidebar order inside a workspace
    (tab order, then pane position), so only the workspace order is applied here.
    """
    members: Dict[Optional[str], List[Mapping[str, Any]]] = {}
    for agent in agents:
        members.setdefault(agent.get("workspace_id"), []).append(agent)
    return [
        (workspace, members[workspace.get("workspace_id")])
        for workspace in workspaces
        if workspace.get("workspace_id") in members
    ]


def _workspace_label(workspace: Mapping[str, Any]) -> str:
    label = workspace.get("label")
    return label.strip() if isinstance(label, str) and label.strip() else workspace_title(workspace)


def build_plan(
    snapshot: Mapping[str, Any], slots: Mapping[str, int], grouped: bool, divider_width: int
) -> Plan:
    workspaces = [w for w in snapshot.get("workspaces") or [] if w.get("workspace_id")]
    agents = [a for a in snapshot.get("agents") or [] if a.get("pane_id")]
    panes = [p for p in snapshot.get("panes") or [] if p.get("pane_id")]

    workspace_tokens: Dict[str, Tokens] = {}
    for workspace in workspaces:
        slot = slots.get(workspace["workspace_id"])
        workspace_tokens[workspace["workspace_id"]] = (
            {workspace_token(slot): _workspace_label(workspace)} if slot else {}
        )

    pane_tokens: Dict[str, Tokens] = {pane["pane_id"]: {} for pane in panes}
    for agent in agents:
        slot = slots.get(agent.get("workspace_id"))
        pane_tokens[agent["pane_id"]] = _agent_tokens(agent, slot) if slot else {}

    if grouped:
        groups = _groups(workspaces, agents)
        for (_, members), (next_workspace, _) in zip(groups, groups[1:]):
            next_slot = slots.get(next_workspace["workspace_id"])
            if not next_slot:
                continue
            last_pane = members[-1]["pane_id"]
            divider = divider_text(workspace_title(next_workspace), divider_width)
            pane_tokens[last_pane] = {**pane_tokens[last_pane], divider_token(next_slot): divider}

    return Plan(workspace_tokens=workspace_tokens, pane_tokens=pane_tokens)


def diff_tokens(current: Optional[Mapping[str, Any]], desired: Tokens) -> TokenUpdate:
    """What to send so our tokens match `desired`; tokens of other sources are left alone."""
    existing = current or {}
    set_tokens = {name: value for name, value in desired.items() if existing.get(name) != value}
    clear_tokens = tuple(
        sorted(name for name in existing if name.startswith(TOKEN_PREFIX) and name not in desired)
    )
    return TokenUpdate(set_tokens=set_tokens, clear_tokens=clear_tokens)
