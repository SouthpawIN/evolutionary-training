"""
scroll_agent.py — The new Hermes Agent tool for controlling the radio
========================================================================

The "scroll" agent is the user-facing tool for interacting with the
Evolutionary Radio. It exposes the radio's controls as a clean CLI
that Hermes Agent can call as a function.

Usage from Hermes:
    python3 scroll_agent.py status
    python3 scroll_agent.py play --vibe "chill lofi beats for coding"
    python3 scroll_agent.py skip
    python3 scroll_agent.py pause
    python3 scroll_agent.py resume
    python3 scroll_agent.py vibe "dark ambient drone"
    python3 scroll_agent.py note "user just talked about X"  # logs to notebook
    python3 scroll_agent.py ask "what's the user thinking about?"  # LLM-curated prompt

Architecture:
    Hermes (any profile)  →  scroll_agent.py  →  evolutionary-radio (IPC: PID + port)
                                                →  notebook (via notebook_connector)

The scroll agent is the lightweight voice-driven control surface. The
heavy lifting (Darwin, GEPA, ACE-Step generation) stays in the radio.

This module is INTENTIONALLY thin. The radio's existing `start_radio.sh`
and `radio.py` are the source of truth for actual playback. The scroll
agent just gives Hermes a way to talk to them.
"""
from __future__ import annotations

import os
import sys
import json
import time
import signal
import argparse
import subprocess
from pathlib import Path
from typing import Any, Optional

# Default paths (all env-overridable)
DEFAULT_RADIO_DIR = Path(os.environ.get(
    "OMNISENTER_RADIO_DIR",
    str(Path(__file__).resolve().parents[3] / "evolutionary-radio"),
)).expanduser()
DEFAULT_PID_FILE = DEFAULT_RADIO_DIR / ".run" / "radio.pid"
DEFAULT_IPC_FILE = DEFAULT_RADIO_DIR / ".run" / "radio.ipc"
DEFAULT_VIBE_FILE = DEFAULT_RADIO_DIR / ".run" / "current_vibe.txt"
DEFAULT_LOG_FILE = DEFAULT_RADIO_DIR / "logs" / "scroll.log"


def _log(msg: str) -> None:
    """Append a line to the scroll log (best-effort)."""
    try:
        DEFAULT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DEFAULT_LOG_FILE, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass


def _read_pid() -> Optional[int]:
    if not DEFAULT_PID_FILE.exists():
        return None
    try:
        return int(DEFAULT_PID_FILE.read_text().strip())
    except Exception:
        return None


def _is_running(pid: Optional[int]) -> bool:
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _send_ipc(command: str) -> dict:
    """
    Send a JSON command to the radio's IPC socket. Falls back to writing
    a command file if the IPC socket isn't set up.
    """
    ipc = DEFAULT_IPC_FILE
    cmd_file = DEFAULT_RADIO_DIR / ".run" / "pending_cmd.json"
    cmd_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {"cmd": command, "ts": time.time()}
    cmd_file.write_text(json.dumps(payload))
    return {"queued": True, "cmd_file": str(cmd_file), "command": command}


# ----------------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------------

def status() -> dict:
    pid = _read_pid()
    running = _is_running(pid)
    vibe = None
    if DEFAULT_VIBE_FILE.exists():
        vibe = DEFAULT_VIBE_FILE.read_text().strip()
    return {
        "running": running,
        "pid": pid,
        "vibe": vibe,
        "pid_file": str(DEFAULT_PID_FILE),
        "ipc_file": str(DEFAULT_IPC_FILE),
        "vibe_file": str(DEFAULT_VIBE_FILE),
        "timestamp": time.time(),
    }


def play(vibe: str = "chill lofi beats for coding") -> dict:
    """Start the radio with a given vibe (if not running), or change vibe."""
    DEFAULT_VIBE_FILE.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_VIBE_FILE.write_text(vibe)
    pid = _read_pid()
    if _is_running(pid):
        # Just change the vibe on the running radio
        return _send_ipc(f"vibe:{vibe}")
    # Start the radio
    start_script = DEFAULT_RADIO_DIR / "start_radio.sh"
    if not start_script.exists():
        return {"error": f"start_radio.sh not found at {start_script}"}
    if not os.access(start_script, os.X_OK):
        os.chmod(start_script, 0o755)
    # Detach
    subprocess.Popen(
        [str(start_script), "start", f"--vibe={vibe}"],
        cwd=str(DEFAULT_RADIO_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )
    _log(f"play vibe={vibe!r}")
    return {"started": True, "vibe": vibe, "script": str(start_script)}


def skip() -> dict:
    """Skip the current track."""
    pid = _read_pid()
    if not _is_running(pid):
        return {"error": "radio not running"}
    _send_ipc("skip")
    return {"skipped": True}


def pause() -> dict:
    pid = _read_pid()
    if not _is_running(pid):
        return {"error": "radio not running"}
    _send_ipc("pause")
    return {"paused": True}


def resume() -> dict:
    pid = _read_pid()
    if not _is_running(pid):
        return {"error": "radio not running"}
    _send_ipc("resume")
    return {"resumed": True}


def stop() -> dict:
    pid = _read_pid()
    if not _is_running(pid):
        return {"stopped": False, "reason": "not running"}
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError as e:
        return {"stopped": False, "error": str(e)}
    return {"stopped": True, "pid": pid}


def vibe(new_vibe: str) -> dict:
    """Change the radio's current vibe (without restarting)."""
    DEFAULT_VIBE_FILE.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_VIBE_FILE.write_text(new_vibe)
    _send_ipc(f"vibe:{new_vibe}")
    _log(f"vibe {new_vibe!r}")
    return {"vibe": new_vibe, "applied": True}


def note(text: str) -> dict:
    """
    Log a free-form note to the notebook (via notebook_connector).
    Used when Hermes wants to record what the user just said that
    inspired the current vibe, or a thought the pet had.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import notebook_connector
        out = notebook_connector.log_pet_note(
            content=text,
            concepts=["radio", "scroll-agent"],
            importance=0.6,
            role="assistant",
            metadata={"source": "scroll-agent"},
        )
        return {"logged": True, **out}
    except Exception as e:
        return {"logged": False, "error": str(e)}


def ask(question: str) -> dict:
    """
    Use the local LLM to reflect on the current radio context and the
    notebook, then return a thoughtful follow-up question or insight
    to inspire the user. This is the "commenting agent" mentioned in
    the OmniSenter vision.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    context = {"question": question, "vibe": None, "notebook_hits": 0}
    try:
        import notebook_connector
        hits = notebook_connector.read_for_hermes(question, limit=5)
        context["notebook_hits"] = len(hits.get("matches", []))
        context["notebook_context"] = hits.get("context_text", "")[:800]
    except Exception as e:
        context["notebook_error"] = str(e)

    vibe = None
    if DEFAULT_VIBE_FILE.exists():
        vibe = DEFAULT_VIBE_FILE.read_text().strip()
    context["vibe"] = vibe

    # If a local model server is running (e.g. via southpaw-server),
    # we'd call it here. For now, return a structured prompt that
    # Hermes can complete.
    return {
        "prompt_for_llm": (
            f"You are the OmniSenter commenting agent. The user is listening to "
            f"vibe: '{vibe or '(none set)'}'. The user just asked/mentioned: "
            f"'{question}'.\n\nRecent notebook context (top {context['notebook_hits']} hits):\n"
            f"{context.get('notebook_context', '(none)')}\n\n"
            f"Generate a single thoughtful follow-up question OR a 1-paragraph "
            f"reflection that helps the user flesh out their ideas. Be concise, warm, "
            f"curious. No bullet points."
        ),
        "context": context,
    }


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="scroll_agent",
        description="Hermes Agent tool for controlling the OmniSenter radio.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Show radio status")
    sub.add_parser("skip", help="Skip current track")
    sub.add_parser("pause", help="Pause playback")
    sub.add_parser("resume", help="Resume playback")
    sub.add_parser("stop", help="Stop the radio")

    p_play = sub.add_parser("play", help="Start the radio (or change vibe if running)")
    p_play.add_argument("--vibe", default="chill lofi beats for coding")

    p_vibe = sub.add_parser("vibe", help="Change the current vibe")
    p_vibe.add_argument("new_vibe")

    p_note = sub.add_parser("note", help="Log a free-form note to the notebook")
    p_note.add_argument("text")

    p_ask = sub.add_parser("ask", help="Build a reflection prompt from notebook + vibe")
    p_ask.add_argument("question")

    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.cmd == "status":  out = status()
    elif args.cmd == "play":  out = play(args.vibe)
    elif args.cmd == "skip":  out = skip()
    elif args.cmd == "pause": out = pause()
    elif args.cmd == "resume": out = resume()
    elif args.cmd == "stop":  out = stop()
    elif args.cmd == "vibe":  out = vibe(args.new_vibe)
    elif args.cmd == "note":  out = note(args.text)
    elif args.cmd == "ask":   out = ask(args.question)
    else: print(f"Unknown: {args.cmd}", file=sys.stderr); return 1
    print(json.dumps(out, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
