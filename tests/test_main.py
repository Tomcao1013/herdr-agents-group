import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from agents_group.main import main

SNAPSHOT_JSON = '{"result":{"snapshot":{"panes":[],"workspaces":[]}}}'
USER_CONFIG = '[theme]\nname = "rose-pine"\n'
NOTIFY_PREFIX = "notification show Agents group --body "
NOTIFY_SUFFIX = " --sound none"


def write_fake_herdr(directory: Path, snapshot: str) -> Path:
    script = "\n".join(
        [
            "#!/bin/sh",
            'case "$1" in',
            "  notification) printf '%s\\n' \"$*\" >> \"$HERDR_LOG\" ;;",
            "  api) printf '%s' '" + snapshot + "' ;;",
            "esac",
            "",
        ]
    )
    path = directory / "herdr"
    path.write_text(script, encoding="utf-8")
    path.chmod(0o755)
    return path


class ActionTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = self.temp_dir / "config.toml"
        self.log = self.temp_dir / "herdr.log"
        self.log.touch()
        self.environment = {
            "HERDR_BIN_PATH": str(write_fake_herdr(self.temp_dir, SNAPSHOT_JSON)),
            "HERDR_CONFIG_PATH": str(self.config),
            "HERDR_PLUGIN_STATE_DIR": str(self.temp_dir / "state"),
            "HERDR_LOG": str(self.log),
        }
        self.saved = {key: os.environ.get(key) for key in self.environment}
        os.environ.update(self.environment)

    def tearDown(self):
        for key, value in self.saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def run_command(self, command):
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = main([command])
        return code, stderr.getvalue()

    def notification_bodies(self):
        bodies = []
        for line in self.log.read_text(encoding="utf-8").splitlines():
            if line.startswith(NOTIFY_PREFIX) and line.endswith(NOTIFY_SUFFIX):
                bodies.append(line[len(NOTIFY_PREFIX):-len(NOTIFY_SUFFIX)])
        return bodies

    def backup_names(self):
        return sorted(path.name for path in self.temp_dir.iterdir() if ".bak-agents-group-" in path.name)

    def log_events(self, stderr):
        return [json.loads(line) for line in stderr.splitlines() if line.startswith("{")]

    def test_install_layout_without_existing_config_reports_no_backup(self):
        code, _ = self.run_command("install-layout")
        self.assertEqual(code, 0)
        self.assertEqual(self.notification_bodies(), ["Sidebar layout installed."])
        self.assertEqual(self.backup_names(), [])
        self.assertIn("[ui.sidebar.agents]", self.config.read_text(encoding="utf-8"))

    def test_install_layout_with_existing_config_notifies_the_backup_it_wrote(self):
        self.config.write_text(USER_CONFIG, encoding="utf-8")
        code, _ = self.run_command("install-layout")
        self.assertEqual(code, 0)
        bodies = self.notification_bodies()
        self.assertEqual(len(bodies), 1)
        self.assertTrue(bodies[0].startswith("Sidebar layout installed. Backup: "), bodies[0])
        name = bodies[0][len("Sidebar layout installed. Backup: "):]
        self.assertRegex(name, r"^config\.toml\.bak-agents-group-\d{8}-\d{6}$")
        self.assertEqual((self.temp_dir / name).read_bytes(), USER_CONFIG.encode("utf-8"))

    def test_uninstall_layout_notifies_the_backup_it_wrote(self):
        self.config.write_text(USER_CONFIG, encoding="utf-8")
        self.assertEqual(self.run_command("install-layout")[0], 0)
        installed = self.config.read_bytes()
        self.log.write_text("", encoding="utf-8")
        code, _ = self.run_command("uninstall-layout")
        self.assertEqual(code, 0)
        bodies = self.notification_bodies()
        self.assertEqual(len(bodies), 1)
        self.assertTrue(bodies[0].startswith("Sidebar layout removed. Backup: "), bodies[0])
        name = bodies[0][len("Sidebar layout removed. Backup: "):]
        self.assertEqual((self.temp_dir / name).read_bytes(), installed)
        self.assertEqual(self.config.read_bytes(), USER_CONFIG.encode("utf-8"))

    def test_non_utf8_config_fails_without_writing_or_notifying(self):
        self.config.write_bytes(b"\xff\xfe[theme]\n")
        code, stderr = self.run_command("install-layout")
        self.assertEqual(code, 1)
        self.assertEqual(self.config.read_bytes(), b"\xff\xfe[theme]\n")
        self.assertEqual(self.backup_names(), [])
        self.assertEqual(self.notification_bodies(), [])
        self.assertNotIn("Traceback", stderr)
        events = self.log_events(stderr)
        self.assertEqual(
            [(event["level"], event["event"], event["command"]) for event in events],
            [("error", "command.failed", "install-layout")],
        )

    def test_reconcile_with_non_utf8_config_fails_with_a_structured_event(self):
        self.config.write_bytes(b"\xff\xfe")
        code, stderr = self.run_command("reconcile")
        self.assertEqual(code, 1)
        self.assertNotIn("Traceback", stderr)
        events = self.log_events(stderr)
        self.assertEqual(
            [(event["level"], event["event"], event["command"]) for event in events],
            [("error", "command.failed", "reconcile")],
        )


if __name__ == "__main__":
    unittest.main()
