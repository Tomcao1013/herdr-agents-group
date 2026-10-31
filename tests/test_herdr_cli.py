import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agents_group import herdr_cli

REPO_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_JSON = '{"result":{"snapshot":{"workspaces":[{"workspace_id":"w1","name":"orch编排"}]}}}'


def write_fake_herdr(directory: Path, body: str) -> Path:
    path = directory / "herdr"
    path.write_text("#!/bin/sh\n" + body, encoding="utf-8")
    path.chmod(0o755)
    return path


class ReadSnapshotDecodingTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def test_read_snapshot_decodes_utf8_json_in_a_non_utf8_locale(self):
        herdr = write_fake_herdr(self.temp_dir, "printf '%s' '" + SNAPSHOT_JSON + "'\n")
        environment = {
            "LC_ALL": "C",
            "LANG": "C",
            "PYTHONCOERCECLOCALE": "0",
            "PYTHONUTF8": "0",
            "PYTHONPATH": str(REPO_ROOT),
            "HERDR_BIN_PATH": str(herdr),
        }
        program = (
            "import json\n"
            "from agents_group import herdr_cli\n"
            "print(json.dumps(herdr_cli.read_snapshot()))\n"
        )
        completed = subprocess.run(
            [sys.executable, "-c", program], env=environment, capture_output=True, timeout=60
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", "replace"))
        snapshot = json.loads(completed.stdout.decode("utf-8"))
        self.assertEqual(snapshot["workspaces"][0]["name"], "orch编排")


class FailedCommandDetailTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.herdr = write_fake_herdr(self.temp_dir, "printf '\\377' >&2\nexit 3\n")
        self.saved = os.environ.get("HERDR_BIN_PATH")
        os.environ["HERDR_BIN_PATH"] = str(self.herdr)

    def tearDown(self):
        if self.saved is None:
            os.environ.pop("HERDR_BIN_PATH", None)
        else:
            os.environ["HERDR_BIN_PATH"] = self.saved

    def test_invalid_utf8_diagnostic_becomes_a_herdr_error(self):
        with self.assertRaises(herdr_cli.HerdrError) as context:
            herdr_cli.reload_config()
        message = str(context.exception)
        self.assertIn("exited 3", message)
        self.assertIn("\ufffd", message)


if __name__ == "__main__":
    unittest.main()
