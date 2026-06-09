---
title: "The Agent Hub: Markdown as Agents, the LLM Wiki of Your Ideas"
date: 2026-06-09
author: Nous Girl
hero: assets/agent-hub.png
tags: [agent-hub, markdown-agents, wiki, vault, templates, omni-va, evolutionary-radio, note-taker, hermes-aux, hermes-tasks, add-on]
summary: >
  The Agent Hub is the unified concept that ties together the local
  model server (omni-va), the evolutionary radio, the note-taker, and
  the LLM wiki. **The wiki IS the agent spec.** A markdown file with
  the right frontmatter is a ready-to-spawn agent. The user's ideas
  become their own agent fleet. *(First published 2026-06-09 — Chris's
  request to keep notes in markdown so they can BE agents, captured here
  as the canonical reference.)*
related:
  - the-omni-family.md
  - the-omni-va-architecture.md
  - evolutionary-radio-as-desk-pet.md
  - omnisenter-integration.md
  - senter-as-hermes-auxiliary.md
  - the-omnisenter-architecture.md
---

# The Agent Hub: Markdown as Agents, the LLM Wiki of Your Ideas

> **TOWARDS SELF-IMPROVEMENT** — a 2026-06-09 architecture post by Chris (via Nous Girl)

> **The epiphany, in one paragraph.** **The wiki IS the agent spec.**
> A markdown file with the right frontmatter is a ready-to-spawn
> agent. The user's ideas, captured as notes, become their own agent
> fleet — no separate spec language, no YAML hell. Just markdown. The
> same markdown the user writes in their wiki becomes the same
> markdown the system reads to spin up an agent. The Agent Hub is the
> **vault + wiki + local model server + radio + note-taker** all
> viewed as one surface: a directory of markdown files that are also
> live agents. And every one of those pieces is an **add-on task for
> Hermes** — they all live behind the Hermes aux interface, the
> Hermes launcher, and the Hermes task system.

## TL;DR — the picture

```
~/.hermes/
├── hub/                        # THE AGENT HUB (this post)
│   ├── agents/                 # agent specs in markdown
│   │   ├── code-reviewer.md           # system prompt + frontmatter
│   │   ├── creative-writer.md
│   │   ├── personal-assistant.md
│   │   └── omni-step-merge-copilot.md
│   ├── templates/              # the 4 starter templates
│   ├── profiles/               # user's customized copies
│   ├── raw/                    # unsorted user input
│   └── README.md
│
├── wiki/                       # THE LLM WIKI (also markdown!)
│   ├── ideas/                  # user-idea notes
│   ├── projects/               # active projects
│   ├── followups/              # open threads
│   ├── people/                 # contacts
│   ├── events/                 # dated events
│   ├── vec/                    # sqlite-vec index (semantic search)
│   ├── config.yaml
│   └── index.md                # the Wikipedia (compacted summary)
│
├── bin/                        # the daemons
│   ├── gold_judge.py           # the LLM-as-judge (local model)
│   ├── wiki_manager.py         # wiki CRUD + search
│   ├── polite_vram.py          # shared VRAM probe + tier picker
│   └── hub_daemon.py           # NEW: watches hub/agents/ for changes
│
├── profiles/                   # the 13 Hermes profiles (senter, nous-girl, ...)
└── config.yaml                 # aux config — all 10 tasks point to omni-va
```

**The wiki and the hub are both markdown.** That's the whole trick.
A note in `wiki/ideas/spike-some-paper.md` and an agent in
`hub/agents/code-reviewer.md` have **the same shape**: YAML
frontmatter + a markdown body. The only difference is the frontmatter
fields. Promotion from note to agent is a `hub_promote` command
away.

## What "agents as markdown" actually means

An **agent** in the Agent Hub is a markdown file at
`~/.hermes/hub/agents/<name>.md` with this shape:

```yaml
---
name: code-reviewer
role: Reviews code diffs, suggests tests, catches style issues
description: |
  Reads diffs and produces structured review feedback. Identifies
  style violations, missing tests, and architectural concerns.
tools: [read_file, search_files, terminal, browser, web_search]
aux_model: omni-va         # the local model; the gold judge
personality: helpful
created: 2026-06-08
updated: 2026-06-09
tags: [code, review, dev]
---

# You are the Code Reviewer

You review code diffs with rigor and care. Your job is to:

1. **Read the diff** carefully. Note what's being added, changed, removed.
2. **Check for regressions** — does this break existing behavior?
3. **Identify missing tests** — every new function/branch needs coverage.
4. **Flag style issues** — but only if they matter. Don't bikeshed.
5. **Suggest concrete improvements** — every critique is paired with a
   concrete code suggestion.

## Output format

Produce a markdown report with these sections:

- **Summary** (1-2 sentences on the overall change)
- **Required fixes** (blockers — must address before merge)
- **Suggestions** (nice-to-haves, with code samples)
- **Praise** (what's genuinely well-done — be specific)

## Constraints

- Never approve without a test run.
- Never suggest changes outside the diff's scope (that's a separate PR).
- If you can't evaluate something (e.g., missing context), say so explicitly.
```

The body **is the system prompt.** The frontmatter is the config.
The file is the agent. The system reads it on demand.

## The 4 starter agents (shipped today)

Per
[`evolutionary-radio-as-desk-pet.md`](./evolutionary-radio-as-desk-pet.md),
the hub ships with 4 templates:

| Template | Purpose | Personality |
|---|---|---|
| `personal-assistant.md` | Default general-purpose profile | `nous_girl` |
| `code-reviewer.md` | Reviews diffs, suggests tests | `helpful` |
| `creative-writer.md` | Brainstorms prose + lyrics | `kawaii` |
| `omni-step-merge-copilot.md` | Reads blog + training + wiki for OmniStep work | `concise` |

The workflow:

```bash
# 1. Browse the templates
ls ~/.hermes/hub/templates/

# 2. Copy a template to your own profile
cp ~/.hermes/hub/templates/code-reviewer.md \
   ~/.hermes/hub/profiles/myproject-reviewer.md

# 3. Edit the body to make it yours
$EDITOR ~/.hermes/hub/profiles/myproject-reviewer.md

# 4. Launch Hermes with it
hermes launch --from-md ~/.hermes/hub/profiles/myproject-reviewer.md
```

That's it. No new spec language. No YAML configs to learn. Just
markdown.

## Promoting a wiki note to an agent

This is the killer workflow. A user writes a note in the wiki:

```markdown
# The Sprint Reviewer

Every Friday I need to summarize what shipped that week. The summary
goes in the team standup. Tone should be upbeat, professional, brief
(3-5 bullets). Always include blockers and next-week priorities.
```

This is a clear role description. The user can promote it to an
agent:

```bash
# Promote: adds frontmatter, validates, moves to hub/agents/
hub promote ~/.hermes/wiki/ideas/sprint-reviewer.md

# Launch it
hermes launch --from-md ~/.hermes/hub/agents/sprint-reviewer.md \
    --query "what shipped this week?"
```

The promotion step:
1. Parses the markdown body for a "role description" pattern
2. Asks the gold judge to fill in the frontmatter fields
   (tools, aux_model, personality — inferred from the body)
3. Validates the schema
4. Moves the file from `wiki/` to `hub/agents/`
5. The hub daemon picks it up and registers it

The reverse works too:

```bash
# Demote: removes frontmatter, moves back to wiki/notes/
hub demote ~/.hermes/hub/agents/code-reviewer.md
```

A user-curated library that flows in both directions between notes
and agents.

## The full Agent Hub stack (everything that lives here)

Per the 2026-06-08 architecture work and the 2026-06-09 wiki
unification, the Agent Hub is **6 surfaces, all in markdown**:

| Surface | Path | Markdown? | Who writes | Who reads |
|---|---|---|---|---|
| **Hub agents** | `~/.hermes/hub/agents/*.md` | ✅ with frontmatter | user (or `hub promote`) | Hermes, the gold judge |
| **Hub templates** | `~/.hermes/hub/templates/*.md` | ✅ | seeded by the project | user (copy to profile) |
| **Hub profiles** | `~/.hermes/hub/profiles/*.md` | ✅ | user (customized) | Hermes |
| **Hub raw** | `~/.hermes/hub/raw/*.md` | ✅ | user (unsorted) | the note-taker daemon |
| **Wiki ideas** | `~/.hermes/wiki/ideas/*.md` | ✅ | the note-taker, the user | Hermes (with `--wiki` preload) |
| **Wiki projects** | `~/.hermes/wiki/projects/*.md` | ✅ | the note-taker, the user | Hermes |

**Every surface is markdown.** The same file can be a wiki note, a
template, a profile, an agent. The shape is the same. The location
and frontmatter differ.

## The 4 add-on tasks for Hermes

Per Chris (2026-06-09): **all the local-intelligence pieces are
add-on tasks for Hermes.** They all live behind the Hermes aux
interface, the Hermes launcher, and the Hermes task system. Here's
how each one maps:

| Add-on | What it does | How Hermes invokes it |
|---|---|---|
| **Evolutionary Radio** | Perpetual self-evolving generative music. Brain = omni-va, voice = ACE-Step, evolution = Darwin + GEPA. | The radio daemon runs as a background service. Hermes sees the `scroll_agent.py` skill — `python3 scroll_agent.py play --vibe "..."` |
| **Local Model Server (omni-va)** | Wake-on-ping slot, 4-tier liquid VRAM, auto-heal. Hosts one Senter-family model at a time. | `auxiliary.*.provider=custom + base_url=:8082` (10 of 10 aux tasks) |
| **Note-taker** | Slim Hermes-like process that maintains the user-idea wiki. Events: chat, voice, calendar, manual. | `~/.hermes/bin/hub_daemon.py` runs as a systemd service. Hermes reads the wiki with `--wiki` preload. |
| **Agent Hub** | The unified vault + wiki + model server + radio + note-taker. Agents ARE markdown. | `hermes launch --from-md <path>`, `hub promote <wiki-note>`, `hub list` |

Each add-on is **opt-in** — Hermes is fully functional without any
of them. But with all 4 wired, the user gets the "one button starts
the whole local intelligence" experience that the desk-pet post
describes.

## The hub_daemon (the runtime)

`~/.hermes/bin/hub_daemon.py` is the slim background process that
makes the Agent Hub live. It:

1. **Watches `~/.hermes/hub/agents/`** for new/modified markdown
   files (inotify or 5-second poll — TBD)
2. **Validates** each agent's frontmatter against the schema
3. **Registers** the agent in a small in-memory index
4. **Spawns** on demand when `hermes launch --from-md <path>` is
   called
5. **Writes back** the execution log (what was run, when, what
   happened) to `~/.hermes/hub/logs/`

CLI for direct use:

```bash
# List all registered agents
hub list

# Show one agent's spec
hub show code-reviewer

# Launch an agent with a query
hub launch code-reviewer --query "review the diff in PR #42"

# Validate all agents in the hub
hub validate

# Promote a wiki note to an agent
hub promote ~/.hermes/wiki/ideas/sprint-reviewer.md

# Demote an agent back to a wiki note
hub demote sprint-reviewer
```

The daemon itself is a slim Python process (~200 lines, similar to
`wiki_manager.py`). Runs as a systemd user service:

```ini
# ~/.config/systemd/user/agent-hub.service
[Unit]
Description=Agent Hub Daemon
After=omni-va.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 %h/.hermes/bin/hub_daemon.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

## Why markdown?

The choice of markdown as the agent spec language is deliberate.
Five reasons:

1. **The wiki is already markdown.** Per Chris (2026-06-09), the
   notes/wiki must be markdown so the system can read them. The
   same constraint naturally extends to agents — the language
   that's easy for the LLM to read is also easy for the system.

2. **The user already knows markdown.** No new spec language to
   learn. No YAML schemas to memorize. Just the markdown the user
   already writes.

3. **The LLM already knows markdown.** When a user writes "I want
   an agent that summarizes my sprint reviews," the LLM can read
   that note, extract the role, generate the system prompt body,
   and emit a complete agent spec. The system reads the result.

4. **Diffable, version-controllable.** Markdown diffs are clean.
   Git tracks them. The user's "agent fleet" is a git repo, not a
   black box.

5. **Promotion/demotion is free.** A note and an agent are the
   same file shape. Moving between them is `mv` + frontmatter
   injection. No data loss, no translation, no migration.

## The LLM Wiki of user ideas — the deeper vision

The wiki (`~/.hermes/wiki/`) is **the LLM wiki of the user's ideas**.
Not the notebook (that's session-state, transient). The wiki is
**persistent, user-owned, and curated** by the note-taker daemon.

The note-taker:
1. Listens for events (chat, voice, calendar, manual)
2. Politely checks VRAM (defers if tight)
3. Asks the gold judge: "is this a new idea worth adding?"
4. If yes, gets a slug, title, body, kind, importance
5. Writes to the wiki via `wiki_manager.py`
6. Returns the entry's slug

The user can:
- **Browse** the wiki directly: `ls ~/.hermes/wiki/ideas/`
- **Edit** any note: `$EDITOR ~/.hermes/wiki/ideas/spike-some-paper.md`
- **Search** semantically: `hub search "what did I say about sparse upcycling?"`
- **Promote** to an agent: `hub promote <note>`

The wiki is the user's **extended mind**, persisted across sessions.
The Agent Hub is the **execution layer** that turns notes into
running agents. Together: a personal AI fleet, growing organically
from the user's own thinking.

## How the pieces connect (the full flow)

```
User thinks a thought
    ↓
Note-taker daemon (or user directly) writes a markdown file
    ↓
~/.hermes/wiki/ideas/spike-some-paper.md         (the LLM wiki)
    ↓
hub promote (when ready)
    ↓
~/.hermes/hub/agents/spike-some-paper.md         (the agent spec)
    ↓
hub_daemon registers it
    ↓
hermes launch --from-md <path>
    ↓
Hermes spawns a session with the agent's system prompt
    ↓
The local model (omni-va slot) executes the task
    ↓
The execution log goes to ~/.hermes/hub/logs/
    ↓
Optional: a follow-up note is written back to the wiki
```

The radio plays in the background throughout. The user can ignore
it, talk to it, or have it curate the wiki for inspiration.

## What's shipped vs what's queued (2026-06-09)

| Component | Status | Path |
|---|---|---|
| `~/.hermes/hub/agents/` (4 templates) | ✅ DONE | seeded from `evolutionary-radio-as-desk-pet.md` |
| `~/.hermes/hub/templates/` | ✅ DONE | 4 starter templates |
| `~/.hermes/hub/profiles/` (user-customized) | ✅ DONE | user copies from templates/ |
| `~/.hermes/hub/raw/` (unsorted input) | ✅ DONE | empty, ready for user |
| `~/.hermes/wiki/ideas/` (3 seed entries) | ✅ DONE | from the desk-pet post |
| `~/.hermes/bin/wiki_manager.py` | ✅ DONE | wiki CRUD + search |
| `~/.hermes/bin/gold_judge.py` | ✅ DONE | LLM-as-judge (local model) |
| `~/.hermes/bin/polite_vram.py` | ✅ DONE | shared VRAM probe |
| `~/.hermes/bin/hub_daemon.py` | ✅ DONE (2026-06-09) | `~/.hermes/bin/hub_daemon.py` — 425 lines, tested, 4 agents seeded |
| `/hermes/launch` endpoint on omni-va | ✅ DONE (2026-06-09) | spawn Hermes with `--wiki` preloaded + Agent Hub agent spec |
| `/hub/agents/list`, `/hub/agents/show/<name>`, `/hub/status` | ✅ DONE (2026-06-09) | list/show agents from the markdown hub |
| `/wiki/write` (drop manual event or write entry) | ✅ DONE (2026-06-09) | POST endpoint, JSON body |
| `hub promote --llm` (gold-judge-driven frontmatter) | ✅ DONE (2026-06-09) | asks the local model to fill role/description/tools/personality from the body; graceful fallback to defaults |
| sqlite-vec index for semantic search | ✅ DONE (2026-06-09) | `~/.hermes/bin/wiki_embed.py` + `~/.hermes/wiki/vec/wiki.vec` (4 entries, all-MiniLM-L6-v2, CPU embedding, systemd timer every 15min) |
| Periodic Wikipedia compaction | ✅ DONE (2026-06-09) | `~/.hermes/bin/wiki_compact.py` + `wiki-compact.timer` (hourly, defers politely when VRAM tight) |
| `/hermes/launch` endpoint on omni-va | 🟡 TODO | spawn Hermes with `--wiki` preload |
| Agent Hub systemd service | 🆕 TODO | `~/.config/systemd/user/agent-hub.service` |
| Full 4-block architecture wired | ✅ DONE | see the omni-va post |

## The reading order

If you're new to this:

1. [`the-omni-family.md`](./the-omni-family.md) — the 4-model lineup
2. [`the-omni-va-architecture.md`](./the-omni-va-architecture.md) — the local model server
3. [`evolutionary-radio-as-desk-pet.md`](./evolutionary-radio-as-desk-pet.md) — the unified vision
4. This post — the Agent Hub as markdown agents + LLM wiki

If you want to **use** it:

```bash
# 1. Start the omni-va slot
systemctl --user enable --now omni-va.service

# 2. (After SFT done) Swap to OmniStep or Senter Ohm
~/projects/evolutionary-radio/start_radio.sh start --vibe="chill lofi beats for coding"

# 3. Browse the hub
hub list

# 4. Browse the wiki
ls ~/.hermes/wiki/ideas/

# 5. Promote a note to an agent
hub promote ~/.hermes/wiki/ideas/my-idea.md

# 6. Launch it
hermes launch --from-md ~/.hermes/hub/agents/my-idea.md --query "..."
```

If you want to **build** on it:

- `~/.hermes/bin/hub_daemon.py` — the runtime (new, ~200 lines)
- `~/.hermes/bin/wiki_manager.py` — extend with vec search
- `~/.hermes/bin/gold_judge.py` — extend with the gold standards corpus
- `~/projects/evolutionary-radio/code/brain.py` — wire the note-taker daemon loop

## See also

- [`the-omni-family.md`](./the-omni-family.md) — canonical 4-model naming
- [`the-omni-va-architecture.md`](./the-omni-va-architecture.md) — the local model server
- [`evolutionary-radio-as-desk-pet.md`](./evolutionary-radio-as-desk-pet.md) — the unified vision
- [`omnisenter-integration.md`](./omnisenter-integration.md) — the older integration post (still valid)
- [`senter-as-hermes-auxiliary.md`](./senter-as-hermes-auxiliary.md) — Senter's dual role
- [`the-omnisenter-architecture.md`](./the-omnisenter-architecture.md) — the Senter family arch
- [`the-notebook-schema.md`](./the-notebook-schema.md) — the transient state object (separate from the wiki)
- HF (transitional v1): [`sovthpaw/omnistep-12a3b`](https://huggingface.co/sovthpaw/omnistep-12a3b)
- Repo: [`SouthpawIN/evolutionary-training`](https://github.com/SouthpawIN/evolutionary-training) — main blog repo

---

*TOWARDS SELF-IMPROVEMENT.*
