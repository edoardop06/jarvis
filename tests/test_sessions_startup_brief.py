"""The session table an agent is shown at startup must fit on a screen.

A hook prints this into every session before the agent reads anything else.
The first version printed every heartbeat of the last fourteen days: 477
words, 30 rows, of which 18 were sessions that started, did nothing and
ended. The one line that decides whether it is safe to edit sat at the
bottom. Two behavioural tests skipped coordination entirely, and the cause
was volume rather than absence.
"""
from __future__ import annotations

import importlib.util
import io
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "sessions.py"

# A startup injection larger than this competes with the request itself.
MAX_STARTUP_WORDS = 140


def load():
    spec = importlib.util.spec_from_file_location("sessions_brief_test", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def beat(mod, ident, state, efforts=(), age_min=0):
    now = time.time()
    return {
        "id": ident,
        "agent": "Claude Code",
        "model": "unknown",
        "started": now - age_min * 60,
        "last_beat": now - age_min * 60,
        "state": state,
        "efforts": list(efforts),
        "file": Path("/nonexistent"),
    }


def render(mod, beats):
    buf = io.StringIO()
    with redirect_stdout(buf):
        mod.print_table(beats)
    return buf.getvalue()


class StartupTableStaysSmallTests(unittest.TestCase):
    def setUp(self):
        self.mod = load()
        self.mod.commits_by_session = lambda limit=60: {}

    def crowded(self):
        live = [beat(self.mod, "aaaa1111", "idle", ["Startup Ideas"]),
                beat(self.mod, "bbbb2222", "ACTIVE", ["AI OS Development"])]
        dead = [beat(self.mod, "dead%04d" % i, "ended", (), age_min=600 + i)
                for i in range(28)]
        return live + dead

    def test_startup_table_fits_on_a_screen(self):
        out = render(self.mod, self.crowded())
        words = len(out.split())
        self.assertLessEqual(
            words, MAX_STARTUP_WORDS,
            f"startup table is {words} words; an agent reads this before the request",
        )

    def test_every_live_session_is_listed(self):
        out = render(self.mod, self.crowded())
        self.assertIn("aaaa1111", out)
        self.assertIn("bbbb2222", out)
        self.assertIn("Startup Ideas", out)

    def test_ended_sessions_are_counted_not_listed(self):
        out = render(self.mod, self.crowded())
        self.assertNotIn("dead0000", out)
        self.assertIn("28", out)

    def test_model_column_is_gone_while_it_reports_unknown(self):
        out = render(self.mod, self.crowded())
        self.assertNotIn("Model", out)
        self.assertNotIn("unknown", out)

    def test_no_heartbeats_still_warns_it_is_not_proof(self):
        out = render(self.mod, [])
        self.assertIn("not proof", out)


def render_debts(mod, beats):
    buf = io.StringIO()
    with redirect_stdout(buf):
        mod.print_handover_debts(beats)
    return buf.getvalue()


class HandoverDebtsStaySmallTests(unittest.TestCase):
    """The same flood came back through the handover list.

    A vault showed 57 sessions "ended without a handover" at every startup,
    54 of them sessions that claimed no effort: opened, did nothing, closed.
    The three that mattered were lost among them.
    """

    def setUp(self):
        self.mod = load()

    def crowded(self):
        real = [beat(self.mod, "real%04d" % i, "ended", ["Startup Ideas"],
                     age_min=60 + i) for i in range(3)]
        empty = [beat(self.mod, "void%04d" % i, "ended", (), age_min=600 + i)
                 for i in range(54)]
        return real + empty

    def test_sessions_that_claimed_an_effort_are_listed(self):
        out = render_debts(self.mod, self.crowded())
        for i in range(3):
            self.assertIn("real%04d" % i, out)

    def test_sessions_that_claimed_nothing_are_counted_not_listed(self):
        out = render_debts(self.mod, self.crowded())
        self.assertNotIn("void0000", out)
        self.assertIn("54", out)

    def test_the_list_fits_on_a_screen(self):
        many = [beat(self.mod, "work%04d" % i, "ended", ["Startup Ideas"],
                     age_min=60 + i) for i in range(30)]
        out = render_debts(self.mod, many)
        self.assertLessEqual(len(out.split()), MAX_STARTUP_WORDS)
        self.assertIn("work0000", out)  # the most recent stays visible

    def test_handed_over_and_live_sessions_are_not_debts(self):
        done = beat(self.mod, "done0001", "ended", ["Startup Ideas"])
        done["handover"] = True
        live = beat(self.mod, "live0001", "ACTIVE", ["Startup Ideas"])
        self.assertEqual(render_debts(self.mod, [done, live]), "")


if __name__ == "__main__":
    unittest.main()
