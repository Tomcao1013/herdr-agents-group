import unittest

from agents_group.naming import display_name, display_width, divider_text, workspace_title


def agent(**fields):
    base = {"pane_id": "w1:p1", "agent": "pi", "cwd": "/Users/u/code/wardrobe-app", "tokens": {}}
    return {**base, **fields}


class DisplayNameTest(unittest.TestCase):
    def test_display_name_uses_topic_without_directory_suffix_when_topic_is_set(self):
        subject = agent(tokens={"topic": "task1 impl - wardrobe-app"}, terminal_title_stripped="π - other")
        self.assertEqual(display_name(subject), "task1 impl")

    def test_display_name_cleans_pi_title_when_topic_is_missing(self):
        subject = agent(terminal_title_stripped="π - task1 impl - wardrobe-app")
        self.assertEqual(display_name(subject), "task1 impl")

    def test_display_name_falls_back_to_kind_when_title_is_only_the_directory(self):
        subject = agent(terminal_title_stripped="π - wardrobe-app")
        self.assertEqual(display_name(subject), "pi")

    def test_display_name_keeps_custom_title_without_prefix(self):
        subject = agent(agent="claude", terminal_title_stripped="Herder panel agent visualization plugin")
        self.assertEqual(display_name(subject), "Herder panel agent visualization plugin")

    def test_display_name_falls_back_to_kind_when_topic_is_blank(self):
        subject = agent(tokens={"topic": "   "})
        self.assertEqual(display_name(subject), "pi")

    def test_display_name_returns_agent_when_kind_is_unknown(self):
        subject = agent(agent=None)
        self.assertEqual(display_name(subject), "agent")

    def test_display_name_ignores_task_token(self):
        subject = agent(tokens={"task": "a whole prompt pasted by another plugin"})
        self.assertEqual(display_name(subject), "pi")

    def test_display_name_strips_foreground_directory_suffix(self):
        subject = agent(cwd="/tmp", foreground_cwd="/x/marking-ai", terminal_title_stripped="π - fix - marking-ai")
        self.assertEqual(display_name(subject), "fix")

    def test_display_name_handles_missing_tokens_field(self):
        subject = agent(tokens=None, terminal_title_stripped="T16 lead")
        self.assertEqual(display_name(subject), "T16 lead")


class WorkspaceTitleTest(unittest.TestCase):
    def test_workspace_title_strips_jump_number_prefix(self):
        self.assertEqual(workspace_title({"label": "[2] marking", "number": 2}), "marking")

    def test_workspace_title_falls_back_to_number_when_label_is_empty(self):
        self.assertEqual(workspace_title({"label": "  ", "number": 3}), "workspace 3")


class DividerTextTest(unittest.TestCase):
    def test_divider_text_pads_to_width_with_rule_characters(self):
        self.assertEqual(divider_text("marking", 20), "── marking " + "─" * 9)

    def test_divider_text_counts_wide_characters_as_two_columns(self):
        text = divider_text("编排", 12)
        self.assertEqual(text, "── 编排 " + "─" * 4)
        self.assertEqual(display_width(text), 12)

    def test_divider_text_truncates_long_names_with_ellipsis(self):
        text = divider_text("a-very-long-workspace-name", 20)
        self.assertEqual(text, "── a-very-long-wo… ─")
        self.assertEqual(display_width(text), 20)


if __name__ == "__main__":
    unittest.main()
