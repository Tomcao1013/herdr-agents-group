import unittest

from agents_group.config_block import (
    BEGIN_MARKER,
    END_MARKER,
    ConfigConflictError,
    install_block,
    is_grouped,
    render_block,
    uninstall_block,
)
from agents_group.colors import PALETTE

USER_CONFIG = '[theme]\nname = "rose-pine"\n\n[ui]\nstatus_indicators = "symbols"\n'


class RenderBlockTest(unittest.TestCase):
    def test_render_block_defines_a_styled_slot_for_every_palette_color(self):
        block = render_block(PALETTE)
        for slot, color in enumerate(PALETTE, start=1):
            self.assertIn(f'{{ token = "$ag_n{slot}", fg = "{color}" }}', block)
            self.assertIn(f'{{ token = "$ag_w{slot}", fg = "{color}", bold = true }}', block)

    def test_render_block_keeps_branch_row_of_default_spaces_layout(self):
        self.assertIn('["branch", "git_status"]', render_block(PALETTE))


class InstallBlockTest(unittest.TestCase):
    def test_install_block_appends_marked_block_and_keeps_user_config(self):
        text = install_block(USER_CONFIG, "BLOCK")
        self.assertTrue(text.startswith(USER_CONFIG))
        self.assertIn(f"{BEGIN_MARKER}\nBLOCK\n{END_MARKER}\n", text)

    def test_install_block_replaces_existing_block_instead_of_duplicating(self):
        once = install_block(USER_CONFIG, "OLD")
        twice = install_block(once, "NEW")
        self.assertEqual(twice.count(BEGIN_MARKER), 1)
        self.assertIn("NEW", twice)
        self.assertNotIn("OLD", twice)

    def test_install_block_refuses_when_user_already_defines_agents_rows(self):
        config = USER_CONFIG + "\n[ui.sidebar.agents]\nrow_gap = 1\n"
        with self.assertRaises(ConfigConflictError):
            install_block(config, "BLOCK")

    def test_install_block_refuses_when_user_already_defines_spaces_rows(self):
        config = USER_CONFIG + "\n  [ ui.sidebar.spaces ]\n"
        with self.assertRaises(ConfigConflictError):
            install_block(config, "BLOCK")

    def test_install_block_adds_newline_when_config_lacks_trailing_newline(self):
        text = install_block("a = 1", "BLOCK")
        self.assertTrue(text.startswith("a = 1\n"))

    def test_install_block_refuses_when_end_marker_is_missing(self):
        with self.assertRaises(ConfigConflictError):
            install_block(USER_CONFIG + BEGIN_MARKER + "\n", "BLOCK")


class UninstallBlockTest(unittest.TestCase):
    def test_uninstall_block_restores_original_config(self):
        self.assertEqual(uninstall_block(install_block(USER_CONFIG, "BLOCK")), USER_CONFIG)

    def test_uninstall_block_leaves_config_without_block_unchanged(self):
        self.assertEqual(uninstall_block(USER_CONFIG), USER_CONFIG)


class IsGroupedTest(unittest.TestCase):
    def test_is_grouped_true_by_default(self):
        self.assertTrue(is_grouped(USER_CONFIG))

    def test_is_grouped_false_when_priority_sort_is_configured(self):
        self.assertFalse(is_grouped('[ui]\nagent_panel_sort = "priority"\n'))

    def test_is_grouped_ignores_commented_setting(self):
        self.assertTrue(is_grouped('[ui]\n# agent_panel_sort = "priority"\n'))


if __name__ == "__main__":
    unittest.main()
