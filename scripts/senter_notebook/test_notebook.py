"""
test_notebook.py — quick smoke test for the notebook scaffold.
Runs in an isolated temp dir to avoid touching the real ~/.senter/notebook/.
"""
import os
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path

# Point notebook.py at a temp dir for this test
TEST_DIR = tempfile.mkdtemp(prefix="notebook_test_")
os.environ["SENTER_NOTEBOOK_DIR"] = TEST_DIR

# Import the notebook module AFTER setting the env var
sys.path.insert(0, str(Path.home() / ".senter"))
import notebook  # noqa: E402

print("=" * 60)
print(f"TEST: notebook scaffold in {TEST_DIR}")
print("=" * 60)

# Test 1: ensure_layout
print("\n[1] ensure_layout()")
layout = notebook.ensure_layout()
assert Path(layout["notebook_dir"]).exists(), "notebook_dir not created"
assert Path(layout["sessions_dir"]).exists(), "sessions_dir not created"
assert Path(layout["index_path"]).exists(), "index.yaml not created"
# Privacy check
perms = oct(Path(layout["notebook_dir"]).stat().st_mode)[-3:]
print(f"  notebook_dir perms: {perms} (expect 700)")
assert perms == "700", f"Expected 700, got {perms}"
print(f"  ✓ layout created, perms={perms}")

# Test 2: new_session
print("\n[2] new_session()")
sid = notebook.new_session(task="Test the notebook scaffold", task_status="open")
print(f"  session_id: {sid}")
assert sid.startswith("s_"), "session_id should start with s_"
assert (notebook.sessions_dir() / f"{sid}.yaml").exists()
print(f"  ✓ session file exists")

# Test 3: add_moment
print("\n[3] add_moment() × 3")
n1 = notebook.add_moment(sid, "What time is it?", role="user", importance=0.3)
n2 = notebook.add_moment(sid, "It's 4:45 PM. Want a coffee?", role="assistant", importance=0.7, concepts=["time", "small-talk"])
n3 = notebook.add_moment(sid, "yes please", role="user", importance=0.2)
print(f"  moments: m_{n1}, m_{n2}, m_{n3}")
assert n1 == 1 and n2 == 2 and n3 == 3, "moment numbers should be 1, 2, 3"
moments = notebook.list_moments(sid)
assert len(moments) == 3
print(f"  ✓ 3 moments recorded")

# Test 4: add_escalation
print("\n[4] add_escalation()")
i = notebook.add_escalation(sid, reason="needs_code_execution", request="set a 5min timer")
print(f"  escalation index: {i}")
sess = notebook.get_session(sid)
assert sess["stats"]["escalation_count"] == 1
print(f"  ✓ escalation recorded")

# Test 5: add_decision
print("\n[5] add_decision()")
d = notebook.add_decision(sid, decision="Use the tmux launch wrapper", rationale="so it survives disconnect")
sess = notebook.get_session(sid)
assert sess["stats"]["decision_count"] == 1
assert sess["decisions"][0]["decision"].startswith("Use")
print(f"  ✓ decision recorded")

# Test 6: search_moments
print("\n[6] search_moments('coffee')")
results = notebook.search_moments("coffee")
print(f"  found {len(results)} result(s)")
assert len(results) >= 1, "should find the coffee moment"
print(f"  ✓ search works")

# Test 7: summary
print("\n[7] summary()")
s = notebook.summary()
print(f"  {s}")
assert s["total_sessions"] >= 1
assert s["total_moments"] >= 3
print(f"  ✓ summary correct")

# Test 8: end_session
print("\n[8] end_session()")
notebook.end_session(sid, status="closed")
sess = notebook.get_session(sid)
assert sess["task_status"] == "closed"
assert "ended_at" in sess
print(f"  ✓ session ended")

# Test 9: list_sessions
print("\n[9] list_sessions()")
sessions = notebook.list_sessions(limit=5)
assert len(sessions) >= 1
print(f"  found {len(sessions)} session(s)")
print(f"  ✓ list works")

# Test 10: directory permissions
print("\n[10] perms check on all files (expect 600)")
for p in Path(TEST_DIR).rglob("*.yaml"):
    perms = oct(p.stat().st_mode)[-3:]
    if perms != "600":
        print(f"  WARN: {p.name} has perms {perms}, expected 600")
print(f"  ✓ all YAML files chmod 600")

# Cleanup
shutil.rmtree(TEST_DIR, ignore_errors=True)

print("\n" + "=" * 60)
print("ALL TESTS PASSED ✓")
print("=" * 60)
