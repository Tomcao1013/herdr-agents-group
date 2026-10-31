import unittest

from agents_group.plan import TokenUpdate, build_plan, diff_tokens


def snapshot(workspaces, agents, panes=()):
    return {"workspaces": list(workspaces), "agents": list(agents), "panes": list(panes)}


def ws(workspace_id, label, tokens=None):
    return {"workspace_id": workspace_id, "label": label, "tokens": tokens or {}}


def ag(pane_id, workspace_id, kind="pi", **fields):
    return {"pane_id": pane_id, "workspace_id": workspace_id, "agent": kind, "cwd": "/x/proj", **fields}


SCENE = snapshot(
    [ws("w1", "[1] wardrobe"), ws("w2", "[2] marking"), ws("w3", "[3] empty")],
    [
        ag("w1:p1", "w1", tokens={"topic": "task1 impl"}),
        ag("w1:p2", "w1", kind="claude"),
        ag("w2:p1", "w2"),
    ],
)
SLOTS = {"w1": 1, "w2": 2, "w3": 3}


class BuildPlanTest(unittest.TestCase):
    def test_build_plan_colors_workspace_label_with_its_slot(self):
        plan = build_plan(SCENE, SLOTS, grouped=True, divider_width=12)
        self.assertEqual(plan.workspace_tokens["w2"], {"ag_w2": "[2] marking"})

    def test_build_plan_writes_name_and_kind_when_name_differs_from_kind(self):
        plan = build_plan(SCENE, SLOTS, grouped=True, divider_width=12)
        self.assertEqual(plan.pane_tokens["w1:p1"], {"ag_n1": "task1 impl", "ag_kind": "pi"})

    def test_build_plan_omits_kind_when_name_is_the_kind(self):
        plan = build_plan(SCENE, SLOTS, grouped=True, divider_width=12)
        self.assertEqual(plan.pane_tokens["w2:p1"], {"ag_n2": "pi"})

    def test_build_plan_puts_next_group_divider_on_last_agent_of_group(self):
        plan = build_plan(SCENE, SLOTS, grouped=True, divider_width=12)
        self.assertEqual(plan.pane_tokens["w1:p2"]["ag_d2"], "── marking ─")

    def test_build_plan_skips_divider_on_last_group(self):
        plan = build_plan(SCENE, SLOTS, grouped=True, divider_width=12)
        self.assertNotIn("ag_d3", plan.pane_tokens["w2:p1"])

    def test_build_plan_skips_dividers_when_not_grouped(self):
        plan = build_plan(SCENE, SLOTS, grouped=False, divider_width=12)
        self.assertEqual(plan.pane_tokens["w1:p2"], {"ag_n1": "claude"})

    def test_build_plan_clears_tokens_on_panes_without_agent(self):
        scene = snapshot([ws("w1", "[1] a")], [], panes=[{"pane_id": "w1:p9", "workspace_id": "w1"}])
        plan = build_plan(scene, {"w1": 1}, grouped=True, divider_width=12)
        self.assertEqual(plan.pane_tokens["w1:p9"], {})

    def test_build_plan_ignores_agent_whose_workspace_has_no_slot(self):
        scene = snapshot([ws("w1", "[1] a")], [ag("w9:p1", "w9")])
        plan = build_plan(scene, {"w1": 1}, grouped=True, divider_width=12)
        self.assertEqual(plan.pane_tokens["w9:p1"], {})


class DiffTokensTest(unittest.TestCase):
    def test_diff_tokens_sets_only_changed_values(self):
        update = diff_tokens({"ag_n1": "a", "ag_kind": "pi"}, {"ag_n1": "b", "ag_kind": "pi"})
        self.assertEqual(update, TokenUpdate(set_tokens={"ag_n1": "b"}, clear_tokens=()))

    def test_diff_tokens_clears_own_tokens_missing_from_desired(self):
        update = diff_tokens({"ag_n1": "a", "ag_d2": "── x"}, {"ag_n1": "a"})
        self.assertEqual(update, TokenUpdate(set_tokens={}, clear_tokens=("ag_d2",)))

    def test_diff_tokens_never_clears_tokens_of_other_plugins(self):
        update = diff_tokens({"topic": "t", "task": "x"}, {})
        self.assertTrue(update.is_empty)

    def test_diff_tokens_treats_missing_current_as_empty(self):
        update = diff_tokens(None, {"ag_n1": "a"})
        self.assertEqual(update.set_tokens, {"ag_n1": "a"})


if __name__ == "__main__":
    unittest.main()
