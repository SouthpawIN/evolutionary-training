"""
test_integration.py — End-to-end tests for the OmniSenter connectors
=====================================================================

Tests for:
  - notebook_connector: export, log, read-for-hermes, sync-handoff
  - scroll_agent: status, play, vibe, note, ask

These use temporary dirs (env vars) to avoid touching the real notebook
or wiki. Run with: python3 -m unittest test_integration -v
"""
import os
import sys
import json
import unittest
import tempfile
import subprocess
from pathlib import Path

# Force temp dirs BEFORE importing the modules
_TMP = tempfile.mkdtemp(prefix="omnisenter_test_")
os.environ["SENTER_NOTEBOOK_DIR"] = str(Path(_TMP) / "notebook")
os.environ["OMNISENTER_WIKI_DIR"] = str(Path(_TMP) / "wiki")
os.environ["OMNISENTER_HANDOFF_DIR"] = str(Path(_TMP) / "handoff")
os.environ["OMNISENTER_RADIO_DIR"] = str(Path(_TMP) / "radio")
# Create the handoff dir so sync-handoff has something to import
os.makedirs(os.environ["OMNISENTER_HANDOFF_DIR"], exist_ok=True)
(Path(_TMP) / "handoff" / "taste.yaml").write_text("music:\n  likes: [chill]\n")
(Path(_TMP) / "handoff" / "note-001.md").write_text("# A test note\n\nThe user talked about the radio vibe.\n")

HERE = Path(__file__).resolve().parent
TESTS_DIR = HERE  # tests/
INTEG_DIR = HERE.parent  # omnisenter_integration/
SENTER_NB_DIR = INTEG_DIR.parent / "senter_notebook"  # the canonical notebook.py
sys.path.insert(0, str(INTEG_DIR))  # notebook_connector, scroll_agent
sys.path.insert(0, str(SENTER_NB_DIR))  # notebook

import notebook as nb
import notebook_connector as nc
import scroll_agent as sa


class NotebookConnectorTests(unittest.TestCase):

    def setUp(self):
        # Reset notebook between tests
        for p in Path(os.environ["SENTER_NOTEBOOK_DIR"]).rglob("*"):
            if p.is_file():
                p.unlink()

    def test_log_pet_creates_session_and_moment(self):
        out = nc.log_pet_note("Test pet note", concepts=["test"], importance=0.8)
        self.assertIn("session_id", out)
        self.assertIn("moment_id", out)
        # Verify it landed in the notebook
        s = nb.get_session(out["session_id"])
        self.assertIsNotNone(s)
        self.assertEqual(s["stats"]["moment_count"], 1)

    def test_log_radio_creates_session(self):
        out = nc.log_radio_inspiration(
            vibe="dark ambient drone",
            note="User asked about generative drones",
            concepts=["music", "drone", "ambient"],
        )
        self.assertIn("session_id", out)
        self.assertEqual(out["vibe"], "dark ambient drone")
        # Verify in notebook
        results = nb.search_moments("drone")
        self.assertGreaterEqual(len(results), 1)

    def test_export_to_wiki_creates_files(self):
        nc.log_pet_note("Wiki export test", concepts=["test"])
        nc.log_radio_inspiration(vibe="lofi", note="Lofi vibes", concepts=["lofi"])
        result = nc.export_to_wiki()
        self.assertEqual(result["sessions_written"], 2)
        self.assertGreaterEqual(result["moments_written"], 2)
        wiki = Path(os.environ["OMNISENTER_WIKI_DIR"])
        self.assertTrue((wiki / "index.md").exists())
        sessions = list((wiki / "sessions").glob("*.md"))
        self.assertGreaterEqual(len(sessions), 2)
        # Verify content
        idx = (wiki / "index.md").read_text()
        self.assertIn("OmniSenter Notebook → Wiki", idx)

    def test_read_for_hermes_returns_matches(self):
        nc.log_pet_note("The user mentioned evolutionary music and ACE-Step", concepts=["music"])
        nc.log_pet_note("The user is thinking about sparse upcycling", concepts=["training"])
        out = nc.read_for_hermes("music")
        self.assertGreater(out["notebook_stats"]["total_sessions"], 0)
        self.assertIn("context_text", out)
        self.assertIn("music", out["context_text"].lower())

    def test_read_for_hermes_empty_query(self):
        nc.log_pet_note("A note", concepts=["x"])
        out = nc.read_for_hermes("zzz_unmatched_query_zzz")
        self.assertEqual(len(out["matches"]), 0)
        self.assertIn("No matching moments", out["summary"])

    def test_sync_with_wiki_handoff(self):
        out = nc.sync_with_wiki_handoff()
        self.assertGreaterEqual(out["imported"], 2)  # taste.yaml + note-001.md
        # Verify those landed in the notebook
        s = nb.get_session(out["session_id"])
        self.assertGreaterEqual(s["stats"]["moment_count"], 2)

    def test_status(self):
        nc.log_pet_note("status test", concepts=["test"])
        s = nc.status()
        self.assertIn("notebook", s)
        self.assertIn("wiki_dir_exists", s)
        self.assertIn("handoff_dir_exists", s)
        self.assertTrue(s["handoff_dir_exists"])
        self.assertGreater(s["notebook"]["total_sessions"], 0)


class ScrollAgentTests(unittest.TestCase):

    def setUp(self):
        # Set up a fake radio dir
        radio_dir = Path(os.environ["OMNISENTER_RADIO_DIR"])
        run_dir = radio_dir / ".run"
        run_dir.mkdir(parents=True, exist_ok=True)
        # Fake PID file pointing to ourselves (so _is_running returns True)
        run_dir.joinpath("radio.pid").write_text(str(os.getpid()))

    def tearDown(self):
        # Clean up fake PID file so it doesn't survive
        run_dir = Path(os.environ["OMNISENTER_RADIO_DIR"]) / ".run"
        for p in run_dir.glob("radio.pid"):
            p.unlink(missing_ok=True)

    def test_status_reports_running(self):
        out = sa.status()
        self.assertTrue(out["running"])
        self.assertEqual(out["pid"], os.getpid())

    def test_status_reports_not_running(self):
        # Remove the fake PID file
        (Path(os.environ["OMNISENTER_RADIO_DIR"]) / ".run" / "radio.pid").unlink(missing_ok=True)
        out = sa.status()
        self.assertFalse(out["running"])

    def test_vibe_writes_file(self):
        out = sa.vibe("dark ambient drone")
        self.assertTrue(out["applied"])
        self.assertEqual(
            (Path(os.environ["OMNISENTER_RADIO_DIR"]) / ".run" / "current_vibe.txt").read_text().strip(),
            "dark ambient drone",
        )

    def test_note_writes_to_notebook(self):
        out = sa.note("The user is into lofi today")
        self.assertTrue(out["logged"])
        self.assertIn("session_id", out)
        # Verify it landed in the notebook
        results = nb.search_moments("lofi")
        self.assertGreaterEqual(len(results), 1)

    def test_ask_builds_prompt(self):
        sa.vibe("jazz piano")
        out = sa.ask("what should I work on next?")
        self.assertIn("prompt_for_llm", out)
        self.assertIn("jazz piano", out["prompt_for_llm"])

    def test_skip_when_not_running(self):
        # Remove the fake PID
        (Path(os.environ["OMNISENTER_RADIO_DIR"]) / ".run" / "radio.pid").unlink(missing_ok=True)
        out = sa.skip()
        self.assertIn("error", out)

    def test_stop_when_not_running(self):
        (Path(os.environ["OMNISENTER_RADIO_DIR"]) / ".run" / "radio.pid").unlink(missing_ok=True)
        out = sa.stop()
        self.assertFalse(out["stopped"])

class CLITests(unittest.TestCase):
    """Verify the CLI entry points work."""

    def test_notebook_connector_cli_status(self):
        result = subprocess.run(
            [sys.executable, str(INTEG_DIR / "notebook_connector.py"), "status"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ},
        )
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
        data = json.loads(result.stdout)
        self.assertIn("notebook", data)

    def test_notebook_connector_cli_log_pet(self):
        result = subprocess.run(
            [sys.executable, str(INTEG_DIR / "notebook_connector.py"),
             "log-pet", "--content", "CLI test note"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ},
        )
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
        data = json.loads(result.stdout)
        self.assertIn("moment_id", data)

    def test_scroll_agent_cli_status(self):
        result = subprocess.run(
            [sys.executable, str(INTEG_DIR / "scroll_agent.py"), "status"],
            capture_output=True, text=True, timeout=10,
            env={**os.environ},
        )
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")


if __name__ == "__main__":
    unittest.main()
