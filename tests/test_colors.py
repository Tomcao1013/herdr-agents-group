import json
import tempfile
import unittest
from pathlib import Path

from agents_group.colors import assign_slots, load_slots, save_slots, state_path


class AssignSlotsTest(unittest.TestCase):
    def test_assign_slots_gives_new_workspaces_lowest_free_slot_in_order(self):
        self.assertEqual(assign_slots({}, ["w1", "w2", "w3"], 6), {"w1": 1, "w2": 2, "w3": 3})

    def test_assign_slots_keeps_previous_slot_when_order_changes(self):
        self.assertEqual(assign_slots({"w2": 1}, ["w1", "w2"], 6), {"w1": 2, "w2": 1})

    def test_assign_slots_releases_slot_of_closed_workspace(self):
        self.assertEqual(assign_slots({"w1": 1, "w2": 2}, ["w2", "w3"], 6), {"w2": 2, "w3": 1})

    def test_assign_slots_reuses_least_used_slot_when_palette_is_full(self):
        previous = {"w1": 1, "w2": 2, "w3": 3}
        self.assertEqual(assign_slots(previous, ["w1", "w2", "w3", "w4"], 3)["w4"], 1)

    def test_assign_slots_reassigns_out_of_range_slot(self):
        self.assertEqual(assign_slots({"w1": 9}, ["w1"], 6), {"w1": 1})

    def test_assign_slots_reassigns_non_integer_slot(self):
        self.assertEqual(assign_slots({"w1": "x"}, ["w1"], 6), {"w1": 1})

    def test_assign_slots_does_not_mutate_previous(self):
        previous = {"w1": 1}
        assign_slots(previous, ["w2"], 6)
        self.assertEqual(previous, {"w1": 1})


class SlotStateFileTest(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp())

    def test_state_path_differs_per_session_socket(self):
        first = state_path(self.directory, "/a/herdr.sock")
        second = state_path(self.directory, "/b/herdr.sock")
        self.assertNotEqual(first, second)

    def test_save_then_load_returns_same_slots(self):
        path = self.directory / "slots.json"
        save_slots(path, {"w1": 2})
        self.assertEqual(load_slots(path), {"w1": 2})

    def test_load_slots_returns_empty_when_file_is_missing(self):
        self.assertEqual(load_slots(self.directory / "missing.json"), {})

    def test_load_slots_returns_empty_when_file_is_corrupt(self):
        path = self.directory / "slots.json"
        path.write_text("{not json", encoding="utf-8")
        self.assertEqual(load_slots(path), {})

    def test_load_slots_returns_empty_when_slots_field_has_wrong_type(self):
        path = self.directory / "slots.json"
        path.write_text(json.dumps({"version": 1, "slots": [1, 2]}), encoding="utf-8")
        self.assertEqual(load_slots(path), {})


if __name__ == "__main__":
    unittest.main()
