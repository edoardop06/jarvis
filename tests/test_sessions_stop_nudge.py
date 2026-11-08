"""A session that changed a project should leave its project note current.

Eleven sessions in one vault ended in a single week without a handover, and
both project notes read a month old while the work itself was a day old. The
next agent starts from the note, so it started from a month ago. The Stop hook
asks once, when a session first leaves a changed project, and never again for
the same project.
"""
from __future__ import annotations

import importlib.util
import json
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "sessions.py"


def load():
    spec = importlib.util.spec_from_file_location("sessions_stop_test", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StopNudgeTests(unittest.TestCase):
    def setUp(self):
        self.mod = load()
        self.tmp = tempfile.TemporaryDirectory()
        self.mod.BEATS = Path(self.tmp.name)
        self.changed = {"Startup Ideas"}
        self.mod.changed_efforts = lambda beat: [
            e for e in beat.get("efforts", []) if e in self.changed]

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, **extra):
        beat = {"id": "abcd1234", "started": time.time() - 600,
                "last_beat": time.time(), "handover": False}
        beat.update(extra)
        (self.mod.BEATS / "abcd1234.json").write_text(json.dumps(beat))

    def stop(self, **data):
        data.setdefault("session_id", "abcd1234")
        return self.mod.stop_nudge(data)

    def test_asks_when_a_changed_project_has_no_handover(self):
        self.write(efforts=["Startup Ideas"])
        reason = self.stop()
        self.assertIsNotNone(reason)
        self.assertIn("Startup Ideas", reason)

    def test_asks_only_once_for_the_same_project(self):
        self.write(efforts=["Startup Ideas"])
        self.assertIsNotNone(self.stop())
        self.assertIsNone(self.stop())

    def test_asks_again_for_a_new_project(self):
        self.changed.add("Second")
        self.write(efforts=["Startup Ideas"])
        self.stop()
        self.write(efforts=["Startup Ideas", "Second"], nudged=["Startup Ideas"])
        reason = self.stop()
        self.assertIn("Second", reason)

    def test_silent_when_the_project_was_only_read(self):
        self.write(efforts=["Read Only"])
        self.assertIsNone(self.stop())

    def test_silent_after_a_handover(self):
        self.write(efforts=["Startup Ideas"], handover=True)
        self.assertIsNone(self.stop())

    def test_silent_while_already_continuing_from_a_stop_hook(self):
        self.write(efforts=["Startup Ideas"])
        self.assertIsNone(self.stop(stop_hook_active=True))

    def test_silent_without_a_heartbeat(self):
        self.assertIsNone(self.stop(session_id="nobody00"))


if __name__ == "__main__":
    unittest.main()
