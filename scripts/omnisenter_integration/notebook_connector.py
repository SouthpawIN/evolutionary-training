"""
notebook_connector.py — The glue between the notebook, the wiki, the radio, and the pet
========================================================================================

The notebook is the structured state object that flows between all
OmniSenter components. This module provides the connectors that make
the loop close:

  - `export_to_wiki()`        — YAML notebook moments → MD files in ~/wiki/
  - `import_from_wiki()`      — MD files in ~/wiki/ → YAML notebook moments
  - `log_radio_inspiration()` — radio wants to remember a vibe → notebook moment
  - `log_pet_note()`          — pet wants to take a note → notebook moment
  - `read_for_hermes()`       — Hermes wants context for a task → notebook summary
  - `sync_with_wiki_handoff()`— sync notebook ↔ ~/wiki/pet-curated/ (the VA's wiki)

The wiki is the human-readable view. The notebook is the structured,
queryable, summarizable view. The radio and the pet write to the
notebook. The wiki export is automatic (and the pet's existing
wiki-handoff stays the read-API for Hermes).

This module is the orchestrator — every component goes through it.

CLI:
  python3 notebook_connector.py export-wiki
  python3 notebook_connector.py import-wiki
  python3 notebook_connector.py log-radio --vibe "chill lofi" --note "..." [--concepts a,b]
  python3 notebook_connector.py log-pet   --content "..." [--concepts a,b]
  python3 notebook_connector.py for-hermes --query "..."
  python3 notebook_connector.py sync-handoff
  python3 notebook_connector.py status
"""
from __future__ import annotations

import os
import sys
import json
import shutil
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Local imports — make notebook.py discoverable whether invoked as a module
# or as a CLI script.
import os as _os
_HERE = Path(__file__).resolve().parent
# Look for the canonical notebook.py in senter_notebook/ next to us
_SENTER_NB_DIR = _HERE.parent / "senter_notebook"
if _SENTER_NB_DIR.exists() and str(_SENTER_NB_DIR) not in sys.path:
    sys.path.insert(0, str(_SENTER_NB_DIR))
# Also try the local dir (in case the user copies notebook.py next to us)
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import notebook as nb  # the existing scaffolded notebook

# ----------------------------------------------------------------------------
# Paths (with env-var overrides so tests / dev can use temp dirs)
# ----------------------------------------------------------------------------

DEFAULT_WIKI_DIR = Path(os.environ.get("OMNISENTER_WIKI_DIR", "~/.senter/wiki")).expanduser()
DEFAULT_HANDOFF_DIR = Path(os.environ.get("OMNISENTER_HANDOFF_DIR", "~/wiki/pet-curated")).expanduser()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ----------------------------------------------------------------------------
# Wiki export  (notebook YAML → MD files in ~/.../wiki/<date>/)
# ----------------------------------------------------------------------------

def export_to_wiki(wiki_dir: Path = None, limit: int = 200) -> dict:
    """
    Export recent notebook moments to a wiki-friendly Markdown layout.

    Layout:
        <wiki_dir>/
        ├── index.md                 # auto-generated index of all sessions
        ├── sessions/
        │   ├── s_2026-06-08_001.md  # one file per session
        │   └── ...
        └── moments/
            └── <date>/
                └── m_*.md           # one file per moment

    Returns: { "sessions_written": N, "moments_written": M, "wiki_dir": "..." }
    """
    wiki_dir = Path(wiki_dir or DEFAULT_WIKI_DIR)
    wiki_dir.mkdir(parents=True, exist_ok=True)
    wiki_dir.chmod(0o700)

    sessions = nb.list_sessions(limit=limit)
    sessions_written = 0
    moments_written = 0

    for sess in sessions:
        sid = sess["session_id"]
        task = sess.get("task", "(no task)")
        status = sess.get("task_status", "?")
        created = sess.get("created_at", "")
        # Session file
        session_md = wiki_dir / "sessions" / f"{sid}.md"
        session_md.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            f"# Session {sid}",
            "",
            f"- **Task:** {task}",
            f"- **Status:** {status}",
            f"- **Created:** {created}",
            f"- **Updated:** {sess.get('updated_at', '')}",
            "",
            f"## Stats",
            "",
            f"- Moments: {sess.get('stats', {}).get('moment_count', 0)}",
            f"- Decisions: {sess.get('stats', {}).get('decision_count', 0)}",
            f"- Escalations: {sess.get('stats', {}).get('escalation_count', 0)}",
            "",
        ]
        # Recent moments summary
        recent = sess.get("context", {}).get("recent_moments", [])
        if recent:
            lines += ["## Recent moments", ""]
            for rm in recent:
                lines.append(f"- `{rm.get('moment_id')}` [{rm.get('role', '?')}] importance={rm.get('importance', 0):.2f}")
            lines.append("")
        # Decisions
        decs = sess.get("decisions", []) or []
        if decs:
            lines += ["## Decisions", ""]
            for d in decs:
                lines.append(f"- **{d.get('decided_at', '?')[:19]}** — {d.get('decision', '')}")
                if d.get("rationale"):
                    lines.append(f"  - *Rationale:* {d['rationale']}")
            lines.append("")
        # Escalations
        escs = sess.get("escalations", []) or []
        if escs:
            lines += ["## Escalations", ""]
            for e in escs:
                lines.append(f"- **{e.get('escalated_at', '?')[:19]}** — {e.get('reason', '')}")
                lines.append(f"  - *Request:* {e.get('request', '')}")
                lines.append(f"  - *Status:* {e.get('status', '?')}")
            lines.append("")
        session_md.write_text("\n".join(lines), encoding="utf-8")
        session_md.chmod(0o600)
        sessions_written += 1

        # Moments for this session
        for m in nb.list_moments(sid, limit=1000):
            mid = m["moment_id"]
            date = m["created_at"][:10]  # YYYY-MM-DD
            md_dir = wiki_dir / "moments" / date
            md_dir.mkdir(parents=True, exist_ok=True)
            md = md_dir / f"{sid}_{mid}.md"
            md_lines = [
                f"# {sid}/{mid}",
                "",
                f"- **When:** {m.get('created_at', '')}",
                f"- **Role:** {m.get('role', '?')}",
                f"- **Importance:** {m.get('importance', 0):.2f}",
            ]
            if m.get("concepts"):
                md_lines += [f"- **Concepts:** {', '.join(m['concepts'])}"]
            if m.get("retrieval_keys"):
                md_lines += [f"- **Retrieval keys:** {', '.join(m['retrieval_keys'])}"]
            if m.get("metadata"):
                md_lines += [f"- **Metadata:** `{json.dumps(m['metadata'], ensure_ascii=False)}`"]
            md_lines += ["", "---", "", m.get("content", "")]
            md.write_text("\n".join(md_lines), encoding="utf-8")
            md.chmod(0o600)
            moments_written += 1

    # Index
    idx = wiki_dir / "index.md"
    idx_lines = [
        f"# OmniSenter Notebook → Wiki",
        "",
        f"_Exported: {_now_iso()}_",
        "",
        f"## Sessions ({len(sessions)})",
        "",
    ]
    for s in sessions[:50]:
        idx_lines.append(f"- [{s['session_id']}](./sessions/{s['session_id']}.md) — {s.get('task','')[:60]} [{s.get('task_status','?')}]")
    idx_lines += [
        "",
        f"## Stats",
        f"- Total sessions: {nb.summary().get('total_sessions', 0)}",
        f"- Total moments: {nb.summary().get('total_moments', 0)}",
        f"- Last updated: {nb.summary().get('last_updated', '')}",
        "",
    ]
    idx.write_text("\n".join(idx_lines), encoding="utf-8")
    idx.chmod(0o600)

    return {
        "sessions_written": sessions_written,
        "moments_written": moments_written,
        "wiki_dir": str(wiki_dir),
    }


# ----------------------------------------------------------------------------
# Wiki import  (MD files in ~/.../wiki/moments/ → notebook moments)
# ----------------------------------------------------------------------------

def import_from_wiki(wiki_dir: Path = None) -> dict:
    """
    Re-import wiki-side files (created by external tools) into the notebook.
    Currently a no-op stub — the canonical write path is the notebook itself,
    and the wiki is a read-only view generated by `export_to_wiki`.

    Kept as a function for future use (e.g., importing the pet-curated/
    directory into the notebook when migrating to the unified store).
    """
    return {"imported": 0, "note": "wiki is a read-only view of the notebook; nothing to import"}


# ----------------------------------------------------------------------------
# Convenience: structured logging from the radio and the pet
# ----------------------------------------------------------------------------

def log_radio_inspiration(
    vibe: str,
    note: str,
    *,
    concepts: list[str] | None = None,
    session_id: str | None = None,
    importance: float = 0.6,
    metadata: dict | None = None,
) -> dict:
    """
    Log a radio observation to the notebook.

    The radio uses this to remember what vibe it just played, what the
    user engaged with, what inspired them. Each call creates a new
    session if one isn't open, and appends a moment to it.
    """
    if not session_id:
        session_id = nb.new_session(
            task=f"Radio: {vibe}",
            task_status="open",
            context={"source": "evolutionary-radio", "vibe": vibe},
        )
    meta = {"source": "evolutionary-radio", "vibe": vibe}
    if metadata:
        meta.update(metadata)
    seq = nb.add_moment(
        session_id,
        note,
        role="system",
        importance=importance,
        concepts=concepts or ["music", "vibe", vibe.lower().split()[0] if vibe else "unknown"],
        retrieval_keys=["radio", "vibe", vibe.lower() if vibe else ""],
        metadata=meta,
    )
    return {"session_id": session_id, "moment_id": f"m_{seq}", "vibe": vibe}


def log_pet_note(
    content: str,
    *,
    concepts: list[str] | None = None,
    session_id: str | None = None,
    importance: float = 0.7,
    role: str = "user",
    metadata: dict | None = None,
) -> dict:
    """
    Log a pet observation (a thought, a question, a user message) to the notebook.

    The pet (Omni VA) uses this to record what the user said, what it
    asked, what inspired them. The voice assistant's main job is to
    maintain this notebook.
    """
    if not session_id:
        session_id = nb.new_session(
            task="Pet note",
            task_status="open",
            context={"source": "omni-va"},
        )
    meta = {"source": "omni-va"}
    if metadata:
        meta.update(metadata)
    seq = nb.add_moment(
        session_id,
        content,
        role=role,
        importance=importance,
        concepts=concepts or [],
        retrieval_keys=[],
        metadata=meta,
    )
    return {"session_id": session_id, "moment_id": f"m_{seq}"}


def read_for_hermes(query: str, limit: int = 20) -> dict:
    """
    Read the notebook for Hermes Agent context.

    Returns a compact text summary of the most relevant recent moments
    matching the query, suitable for dropping into a Hermes prompt as
    pre-context.
    """
    matches = nb.search_moments(query, limit=limit)
    summary = nb.summary()
    if not matches:
        return {
            "summary": f"No matching moments for query '{query}'.",
            "notebook_stats": summary,
            "matches": [],
            "context_text": (
                f"OmniSenter notebook has {summary.get('total_sessions', 0)} sessions, "
                f"{summary.get('total_moments', 0)} moments. No matches for '{query}'."
            ),
        }
    # Build a context block Hermes can consume
    blocks = [
        f"OmniSenter notebook context for query: '{query}'",
        f"({len(matches)} matches; notebook has {summary.get('total_sessions', 0)} sessions, "
        f"{summary.get('total_moments', 0)} moments total)",
        "",
    ]
    for m in matches:
        ts = m.get("created_at", "")[:19]
        role = m.get("role", "?")
        content = (m.get("content", "") or "").strip()[:300]
        imp = m.get("importance", 0)
        concepts = ", ".join(m.get("concepts", []) or []) or "-"
        blocks += [
            f"### {m['session_id']}/{m['moment_id']}  ({ts}, {role}, imp={imp:.2f})",
            f"Concepts: {concepts}",
            f"{content}",
            "",
        ]
    return {
        "summary": f"{len(matches)} matches.",
        "notebook_stats": summary,
        "matches": matches,
        "context_text": "\n".join(blocks),
    }


# ----------------------------------------------------------------------------
# Sync with the pet's existing wiki handoff (the read-API for Hermes)
# ----------------------------------------------------------------------------

def sync_with_wiki_handoff(handoff_dir: Path = None) -> dict:
    """
    Mirror the pet's existing wiki-handoff directory into the notebook
    (one-way: handoff → notebook, so the notebook is the unified store).

    The handoff dir structure (per the pet's wiki_handoff.py):
        ~/wiki/pet-curated/
        ├── *.md / *.yaml    # curated notes
        ├── escalations/     # pending escalations to Hermes
        └── taste.yaml       # the radio's taste profile
    """
    handoff_dir = Path(handoff_dir or DEFAULT_HANDOFF_DIR)
    if not handoff_dir.exists():
        return {"imported": 0, "note": f"handoff dir not found: {handoff_dir}"}

    imported = 0
    sid = nb.new_session(
        task="Pet-curated wiki handoff sync",
        task_status="open",
        context={"source": "wiki-handoff-sync", "handoff_dir": str(handoff_dir)},
    )
    for p in sorted(handoff_dir.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix not in (".md", ".yaml", ".yml", ".txt"):
            continue
        rel = p.relative_to(handoff_dir)
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        nb.add_moment(
            sid,
            content[:2000],  # cap to avoid huge pastes
            role="tool",
            importance=0.5,
            concepts=["handoff", "pet-curated"],
            retrieval_keys=[p.stem],
            metadata={"path": str(rel), "source": "wiki-handoff"},
        )
        imported += 1
    return {"imported": imported, "session_id": sid, "handoff_dir": str(handoff_dir)}


# ----------------------------------------------------------------------------
# Status
# ----------------------------------------------------------------------------

def status() -> dict:
    """Quick health check across notebook + wiki + handoff."""
    s = nb.summary()
    wiki = DEFAULT_WIKI_DIR
    handoff = DEFAULT_HANDOFF_DIR
    return {
        "notebook": s,
        "wiki_dir_exists": wiki.exists(),
        "wiki_dir": str(wiki),
        "handoff_dir_exists": handoff.exists(),
        "handoff_dir": str(handoff),
        "timestamp": _now_iso(),
    }


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="notebook_connector",
        description="The OmniSenter notebook ↔ wiki ↔ radio ↔ pet connector.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("export-wiki", help="Export notebook moments to a wiki MD tree")
    sub.add_parser("import-wiki", help="(no-op stub) Import wiki into notebook")
    sub.add_parser("status", help="Show notebook + wiki + handoff status")

    p_log_r = sub.add_parser("log-radio", help="Log a radio observation")
    p_log_r.add_argument("--vibe", required=True)
    p_log_r.add_argument("--note", required=True)
    p_log_r.add_argument("--concepts", default="", help="comma-separated concepts")
    p_log_r.add_argument("--importance", type=float, default=0.6)
    p_log_r.add_argument("--session-id", default=None)

    p_log_p = sub.add_parser("log-pet", help="Log a pet observation")
    p_log_p.add_argument("--content", required=True)
    p_log_p.add_argument("--concepts", default="")
    p_log_p.add_argument("--importance", type=float, default=0.7)
    p_log_p.add_argument("--role", default="user", choices=["user", "assistant", "system", "tool"])
    p_log_p.add_argument("--session-id", default=None)

    p_h = sub.add_parser("for-hermes", help="Build a Hermes context block from the notebook")
    p_h.add_argument("--query", required=True)
    p_h.add_argument("--limit", type=int, default=20)
    p_h.add_argument("--text-only", action="store_true", help="just print the context text")

    sub.add_parser("sync-handoff", help="Sync the pet-curated wiki handoff → notebook")

    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.cmd == "export-wiki":
        print(json.dumps(export_to_wiki(), indent=2))
    elif args.cmd == "import-wiki":
        print(json.dumps(import_from_wiki(), indent=2))
    elif args.cmd == "status":
        print(json.dumps(status(), indent=2))
    elif args.cmd == "log-radio":
        concepts = [c.strip() for c in args.concepts.split(",") if c.strip()]
        out = log_radio_inspiration(
            vibe=args.vibe, note=args.note, concepts=concepts,
            importance=args.importance, session_id=args.session_id,
        )
        print(json.dumps(out, indent=2))
    elif args.cmd == "log-pet":
        concepts = [c.strip() for c in args.concepts.split(",") if c.strip()]
        out = log_pet_note(
            content=args.content, concepts=concepts,
            importance=args.importance, role=args.role, session_id=args.session_id,
        )
        print(json.dumps(out, indent=2))
    elif args.cmd == "for-hermes":
        out = read_for_hermes(args.query, limit=args.limit)
        if args.text_only:
            print(out["context_text"])
        else:
            print(json.dumps(out, indent=2))
    elif args.cmd == "sync-handoff":
        print(json.dumps(sync_with_wiki_handoff(), indent=2))
    else:
        print(f"Unknown command: {args.cmd}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
