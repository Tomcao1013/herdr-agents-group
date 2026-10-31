import tempfile
import unittest
from pathlib import Path

from agents_group.reconcile import MAX_PASSES_PER_RUN, run_coalesced


class RunCoalescedTest(unittest.TestCase):
    def setUp(self):
        self.state_dir = Path(tempfile.mkdtemp())

    def test_run_coalesced_runs_one_pass_for_one_event(self):
        calls = []
        run_coalesced(self.state_dir, lambda: calls.append(1))
        self.assertEqual(len(calls), 1)

    def test_run_coalesced_runs_again_when_event_arrives_during_pass(self):
        calls = []

        def run_pass():
            calls.append(1)
            if len(calls) == 1:
                (self.state_dir / "pending").touch()

        run_coalesced(self.state_dir, run_pass)
        self.assertEqual(len(calls), 2)

    def test_run_coalesced_stops_at_pass_limit_under_endless_events(self):
        calls = []

        def run_pass():
            calls.append(1)
            (self.state_dir / "pending").touch()

        run_coalesced(self.state_dir, run_pass)
        self.assertEqual(len(calls), MAX_PASSES_PER_RUN)


if __name__ == "__main__":
    unittest.main()
