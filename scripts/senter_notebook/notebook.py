"""
notebook.py — Senter's structured state object (the killer feature)
====================================================================

The notebook is the structured state object that flows between Senter
(any model in the Senter family) and Hermes Agent. It's what makes
Senter useful as a long-running auxiliary rather than just a smaller
model. Per memory: "Notebook is the killer feature."

This is a SCAFFOLD (2026-06-08). It implements:
  - the directory layout (sessions, moments, index, embeddings)
  - the YAML schema skeleton for sessions and moments
  - the basic read/write API
  - a privacy-first defaults (chmod 600)

What's NOT yet implemented (deferred to after Stage 1 SFT finishes):
  - FAISS embedding index (.faiss file) — needs the model running
  - LLM-driven summarization (compaction policy) — needs the 8B SFT
  - Audio/image multi-modal storage paths
  - Cross-session relevance ranking
  - Atomic swap of the index

See the full design:
  - wiki/concepts/notebook.md
  - blog/the-notebook-schema.md
  - blog/senter-as-hermes-auxiliary.md

The schema is:

    ~/.senter/notebook/
    ├── sessions/
    │   ├── s_2026-06-07_001.yaml      # session file
    │   └── s_2026-06-07_001/
    │       └── moments/
    │           ├── m_1829.yaml         # individual moment
    │           └── m_1830.yaml
    ├── index.yaml                     # cross-session index
    └── embeddings.faiss               # vector index (FUTURE)

Public API:
  - ensure_layout()          — create dirs if missing, set permissions
  - new_session(task, ...)   — start a session, return session_id
  - end_session(session_id, status) — close a session
  - add_moment(session_id, ...) — append a moment to a session
  - get_session(session_id)  — read a session
  - list_sessions(limit)     — most-recent sessions
  - search_moments(query)    — keyword search across moments (FUTURE: vector)
  - summary()                — quick stats
"""
from __future__ import annotations
import os
import re
import json
import yaml
import stat
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------

DEFAULT_NOTEBOOK_DIR = Path(os.environ.get("SENTER_NOTEBOOK_DIR", "~/.senter/notebook")).expanduser()
SESSIONS_DIRNAME = "sessions"
INDEX_FILENAME = "index.yaml"
EMBEDDINGS_FILENAME = "embeddings.faiss"  # future


def notebook_dir() -> Path:
    """The notebook root. Created on first call with privacy-first perms."""
    p = DEFAULT_NOTEBOOK_DIR
    p.mkdir(parents=True, exist_ok=True)
    # chmod 700 on the root (owner-only)
    p.chmod(stat.S_IRWXU)
    return p


def sessions_dir() -> Path:
    """Directory of session files (YAML)."""
    p = notebook_dir() / SESSIONS_DIRNAME
    p.mkdir(parents=True, exist_ok=True)
    p.chmod(stat.S_IRWXU)
    return p


def moments_dir(session_id: str) -> Path:
    """Per-session moments directory."""
    p = sessions_dir() / session_id / "moments"
    p.mkdir(parents=True, exist_ok=True)
    p.chmod(stat.S_IRWXU)
    return p


def index_path() -> Path:
    return notebook_dir() / INDEX_FILENAME


# ----------------------------------------------------------------------------
# Time helpers
# ----------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_compact() -> str:
    """2026-06-08T16-45-30Z — filesystem-safe timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def _now_date_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ----------------------------------------------------------------------------
# ID helpers
# ----------------------------------------------------------------------------

def _slugify(s: str, max_len: int = 60) -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "-", s.strip().lower())
    s = re.sub(r"-+", "-", s).strip("-")
    return (s or "session")[:max_len]


def _next_session_seq(today: str) -> int:
    """Find the next session sequence number for today (001, 002, ...)."""
    pattern = re.compile(rf"^s_{re.escape(today)}_(\d{{3}})$")
    used = []
    for p in sessions_dir().glob(f"s_{today}_*.yaml"):
        m = pattern.match(p.stem)
        if m:
            used.append(int(m.group(1)))
    return (max(used) + 1) if used else 1


def _next_moment_seq(session_id: str) -> int:
    """Find the next moment number for a session."""
    pattern = re.compile(r"^m_(\d+)$")
    used = []
    for p in moments_dir(session_id).glob("m_*.yaml"):
        m = pattern.match(p.stem)
        if m:
            used.append(int(m.group(1)))
    return (max(used) + 1) if used else 1


# ----------------------------------------------------------------------------
# Layout
# ----------------------------------------------------------------------------

def ensure_layout() -> dict:
    """Make sure the directory layout exists. Idempotent. Returns a status dict."""
    notebook_dir()
    sessions_dir()
    ip = index_path()
    if not ip.exists():
        ip.write_text(yaml.safe_dump({
            "schema_version": 1,
            "created_at": _now_iso(),
            "last_updated": _now_iso(),
            "total_sessions": 0,
            "total_moments": 0,
            "last_session_id": None,
        }, sort_keys=False, allow_unicode=True), encoding="utf-8")
        ip.chmod(stat.S_IRUSR | stat.S_IWUSR)
    return {
        "notebook_dir": str(notebook_dir()),
        "sessions_dir": str(sessions_dir()),
        "index_path": str(index_path()),
        "exists": True,
    }


# ----------------------------------------------------------------------------
# Session API
# ----------------------------------------------------------------------------

def new_session(task: str, task_status: str = "open", context: dict | None = None) -> str:
    """
    Start a new session. Returns the session_id (e.g. "s_2026-06-08_001").

    The session file is written to sessions_dir()/s_<date>_<seq>.yaml
    and a fresh moments/ subdir is created.
    """
    ensure_layout()
    today = _now_date_compact()
    seq = _next_session_seq(today)
    session_id = f"s_{today}_{seq:03d}"
    fm = {
        "session_id": session_id,
        "task": task,
        "task_status": task_status,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "context": context or {
            "raw_history_size": 0,
            "condensed_history": "",
            "recent_moments": [],
        },
        "decisions": [],
        "pending": [],
        "escalations": [],
        "links": [],
        "stats": {
            "moment_count": 0,
            "decision_count": 0,
            "escalation_count": 0,
        },
        "schema_version": 1,
    }
    out = sessions_dir() / f"{session_id}.yaml"
    out.write_text(yaml.safe_dump(fm, sort_keys=False, allow_unicode=True), encoding="utf-8")
    out.chmod(stat.S_IRUSR | stat.S_IWUSR)
    moments_dir(session_id)  # create the moments subdir
    _update_index(session_id=session_id, delta_sessions=+1, delta_moments=0)
    return session_id


def end_session(session_id: str, status: str = "closed") -> None:
    """Mark a session as closed/completed/failed."""
    path = sessions_dir() / f"{session_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Session {session_id} not found")
    with open(path) as f:
        fm = yaml.safe_load(f) or {}
    fm["task_status"] = status
    fm["ended_at"] = _now_iso()
    fm["updated_at"] = _now_iso()
    path.write_text(yaml.safe_dump(fm, sort_keys=False, allow_unicode=True), encoding="utf-8")


def get_session(session_id: str) -> Optional[dict]:
    """Read a session by id. Returns None if not found."""
    path = sessions_dir() / f"{session_id}.yaml"
    if not path.exists():
        return None
    with open(path) as f:
        return yaml.safe_load(f)


def list_sessions(limit: int = 20, status: str | None = None) -> list[dict]:
    """List recent sessions, newest first. Optional status filter."""
    out = []
    for p in sorted(sessions_dir().glob("s_*.yaml"), reverse=True):
        with open(p) as f:
            fm = yaml.safe_load(f) or {}
        if status is not None and fm.get("task_status") != status:
            continue
        out.append(fm)
        if len(out) >= limit:
            break
    return out


# ----------------------------------------------------------------------------
# Moment API
# ----------------------------------------------------------------------------

def add_moment(
    session_id: str,
    content: str,
    *,
    role: str = "user",          # user | assistant | tool | system
    importance: float = 0.5,     # 0.0 to 1.0
    concepts: list[str] | None = None,
    retrieval_keys: list[str] | None = None,
    metadata: dict | None = None,
) -> int:
    """
    Append a moment to a session. Returns the moment number.

    A moment is a single unit of conversation/state: a user prompt,
    an assistant reply, a tool result, or a system note. Each moment
    has structured metadata (concepts, retrieval keys, importance) so
    the notebook can be queried and summarized later.
    """
    seq = _next_moment_seq(session_id)
    moment_id = f"m_{seq}"
    fm = {
        "moment_id": moment_id,
        "session_id": session_id,
        "created_at": _now_iso(),
        "role": role,
        "content": content,
        "importance": max(0.0, min(1.0, importance)),
        "concepts": concepts or [],
        "retrieval_keys": retrieval_keys or [],
        "metadata": metadata or {},
        "decay_rate": 0.01,  # 1% per day (matches compaction policy)
        "schema_version": 1,
    }
    out = moments_dir(session_id) / f"{moment_id}.yaml"
    out.write_text(yaml.safe_dump(fm, sort_keys=False, allow_unicode=True), encoding="utf-8")
    out.chmod(stat.S_IRUSR | stat.S_IWUSR)
    # update session stats
    sp = sessions_dir() / f"{session_id}.yaml"
    if sp.exists():
        with open(sp) as f:
            sf = yaml.safe_load(f) or {}
        sf["stats"]["moment_count"] = sf["stats"].get("moment_count", 0) + 1
        sf["updated_at"] = _now_iso()
        # add to recent_moments (cap at 10)
        rm = sf.setdefault("context", {}).setdefault("recent_moments", [])
        rm.append({"moment_id": moment_id, "role": role, "importance": fm["importance"]})
        sf["context"]["recent_moments"] = rm[-10:]
        sp.write_text(yaml.safe_dump(sf, sort_keys=False, allow_unicode=True), encoding="utf-8")
    _update_index(session_id=session_id, delta_sessions=0, delta_moments=+1)
    return seq


def list_moments(session_id: str, limit: int = 100) -> list[dict]:
    """List moments for a session, newest first."""
    out = []
    for p in sorted(moments_dir(session_id).glob("m_*.yaml"), reverse=True):
        with open(p) as f:
            out.append(yaml.safe_load(f))
        if len(out) >= limit:
            break
    return out


def search_moments(query: str, limit: int = 20) -> list[dict]:
    """
    Keyword search across all moments. Naive (linear scan + substring
    match) — fine for hundreds of moments, will need FAISS for scale.

    Returns matching moments sorted by importance * recency.
    """
    q = query.lower()
    candidates = []
    for sess_p in sessions_dir().glob("s_*.yaml"):
        session_id = sess_p.stem
        for mp in moments_dir(session_id).glob("m_*.yaml"):
            with open(mp) as f:
                fm = yaml.safe_load(f) or {}
            haystack = (
                fm.get("content", "")
                + " "
                + " ".join(fm.get("concepts", []))
                + " "
                + " ".join(fm.get("retrieval_keys", []))
            ).lower()
            if q in haystack:
                candidates.append(fm)
    # sort: importance * (1 / age_in_seconds)
    now = time.time()
    def score(m):
        age_s = now - datetime.fromisoformat(m["created_at"]).timestamp()
        return m.get("importance", 0.5) / max(age_s, 1)
    candidates.sort(key=score, reverse=True)
    return candidates[:limit]


# ----------------------------------------------------------------------------
# Escalations (in-session)
# ----------------------------------------------------------------------------

def add_escalation(session_id: str, reason: str, request: str, context: dict | None = None) -> int:
    """Record an escalation request in the session. Returns escalation index."""
    sp = sessions_dir() / f"{session_id}.yaml"
    if not sp.exists():
        raise FileNotFoundError(f"Session {session_id} not found")
    with open(sp) as f:
        sf = yaml.safe_load(f) or {}
    escs = sf.setdefault("escalations", [])
    esc = {
        "escalated_at": _now_iso(),
        "reason": reason,
        "request": request,
        "context": context or {},
        "status": "pending",
    }
    escs.append(esc)
    sf["stats"]["escalation_count"] = sf["stats"].get("escalation_count", 0) + 1
    sf["updated_at"] = _now_iso()
    sp.write_text(yaml.safe_dump(sf, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return len(escs) - 1


def add_decision(session_id: str, decision: str, rationale: str = "") -> int:
    """Record a decision (the "D" in ADR — Architecture Decision Record)."""
    sp = sessions_dir() / f"{session_id}.yaml"
    if not sp.exists():
        raise FileNotFoundError(f"Session {session_id} not found")
    with open(sp) as f:
        sf = yaml.safe_load(f) or {}
    decs = sf.setdefault("decisions", [])
    decs.append({
        "decided_at": _now_iso(),
        "decision": decision,
        "rationale": rationale,
    })
    sf["stats"]["decision_count"] = sf["stats"].get("decision_count", 0) + 1
    sf["updated_at"] = _now_iso()
    sp.write_text(yaml.safe_dump(sf, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return len(decs) - 1


# ----------------------------------------------------------------------------
# Index helpers
# ----------------------------------------------------------------------------

def _update_index(session_id: str, delta_sessions: int, delta_moments: int) -> None:
    ip = index_path()
    if not ip.exists():
        ensure_layout()
    with open(ip) as f:
        idx = yaml.safe_load(f) or {}
    idx["total_sessions"] = idx.get("total_sessions", 0) + delta_sessions
    idx["total_moments"] = idx.get("total_moments", 0) + delta_moments
    idx["last_updated"] = _now_iso()
    if delta_sessions > 0:
        idx["last_session_id"] = session_id
    ip.write_text(yaml.safe_dump(idx, sort_keys=False, allow_unicode=True), encoding="utf-8")
    ip.chmod(stat.S_IRUSR | stat.S_IWUSR)


def summary() -> dict:
    """Quick stats about the notebook."""
    idx_path = index_path()
    if not idx_path.exists():
        ensure_layout()
    with open(idx_path) as f:
        idx = yaml.safe_load(f) or {}
    return {
        "notebook_dir": str(notebook_dir()),
        "total_sessions": idx.get("total_sessions", 0),
        "total_moments": idx.get("total_moments", 0),
        "last_session_id": idx.get("last_session_id"),
        "last_updated": idx.get("last_updated"),
    }


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: notebook.py [ensure|new|add|list|get|summary|search|end] [args...]")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "ensure":
        print(json.dumps(ensure_layout(), indent=2))
    elif cmd == "new":
        task = sys.argv[2] if len(sys.argv) > 2 else "(no task)"
        sid = new_session(task=task)
        print(sid)
    elif cmd == "add":
        session_id = sys.argv[2]
        content = sys.stdin.read() if not sys.stdin.isatty() else "(no content)"
        n = add_moment(session_id, content)
        print(f"m_{n}")
    elif cmd == "list":
        for s in list_sessions():
            print(f"  {s['session_id']}  [{s.get('task_status','?')}]  {s.get('task','')[:60]}")
    elif cmd == "get":
        s = get_session(sys.argv[2])
        print(yaml.safe_dump(s, sort_keys=False, allow_unicode=True) if s else "(not found)")
    elif cmd == "summary":
        print(json.dumps(summary(), indent=2))
    elif cmd == "search":
        q = sys.argv[2] if len(sys.argv) > 2 else ""
        for m in search_moments(q):
            print(f"  {m['session_id']}/{m['moment_id']}  [{m.get('role','?')}]  {m.get('content','')[:80]}")
    elif cmd == "end":
        end_session(sys.argv[2], status=sys.argv[3] if len(sys.argv) > 3 else "closed")
        print(f"ended {sys.argv[2]}")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
