# The Agent Hub

> **The unified vault + wiki + local model server + radio + note-taker.**
> See the full blog post:
> [`../../blog/the-agent-hub-markdown-as-agents.md`](../../blog/the-agent-hub-markdown-as-agents.md)
>
> **Status (2026-06-09):** 🟢 **designed, mostly built, hub_daemon pending.**
> The 4 starter templates + vault + wiki + gold judge + polite_vram
> are all in place at `~/.hermes/`. The `hub_daemon.py` runtime
> (~200 lines) is the next concrete build — it watches
> `hub/agents/*.md`, validates frontmatter, registers agents, and
> spawns on `hub launch` calls. The `hub promote` / `hub demote` CLI
> for note↔agent round-trips is part of the same daemon.

## Definition

The **Agent Hub** is the unified surface that turns **markdown files
into live agents**. It bundles six markdown-only surfaces (hub
agents, hub templates, hub profiles, hub raw, wiki ideas, wiki
projects) behind one runtime (`hub_daemon.py`) and one CLI
(`hub list | launch | promote | demote | show | validate`). Every
piece is opt-in; the user can start with one and grow.

The core idea: **the wiki IS the agent spec.** A note in
`~/.hermes/wiki/ideas/` with a clear role description can be
promoted to an agent in `~/.hermes/hub/agents/` with a single
command. The file shape doesn't change. The frontmatter is the
only difference.

## The 6 markdown surfaces

| Surface | Path | Who writes | Who reads |
|---|---|---|---|
| **Hub agents** | `~/.hermes/hub/agents/*.md` | user (or `hub promote`) | Hermes, the gold judge |
| **Hub templates** | `~/.hermes/hub/templates/*.md` | seeded by the project | user (copy to profile) |
| **Hub profiles** | `~/.hermes/hub/profiles/*.md` | user (customized) | Hermes |
| **Hub raw** | `~/.hermes/hub/raw/*.md` | user (unsorted input) | the note-taker daemon |
| **Wiki ideas** | `~/.hermes/wiki/ideas/*.md` | the note-taker, the user | Hermes (with `--wiki` preload) |
| **Wiki projects** | `~/.hermes/wiki/projects/*.md` | the note-taker, the user | Hermes |

All 6 surfaces are markdown. All 6 are git-trackable. All 6 are
LLM-readable.

## The agent schema (the frontmatter contract)

Every agent markdown file has YAML frontmatter:

```yaml
---
name: code-reviewer
role: Reviews code diffs, suggests tests, catches style issues
description: |
  Reads diffs and produces structured review feedback. ...
tools: [read_file, search_files, terminal, browser, web_search]
aux_model: omni-va         # the local model; the gold judge
personality: helpful
created: 2026-06-08
updated: 2026-06-09
tags: [code, review, dev]
---
```

The body **is the system prompt.** The hub daemon parses this
frontmatter, validates the fields, and registers the agent.

**Required fields:** `name`, `role`, `description`, `tools`,
`aux_model`, `personality`. **Optional:** `created`, `updated`,
`tags`.

The `hub_daemon.py` validates the schema. Bad files are flagged
but not deleted; the daemon logs a warning and skips them.

## The 4 starter agents (shipped 2026-06-08)

Per the [`evolutionary-radio-as-desk-pet.md`](../../blog/evolutionary-radio-as-desk-pet.md)
post, the hub ships with 4 templates:

| Template | Purpose | Personality |
|---|---|---|
| `personal-assistant.md` | Default general-purpose | `nous_girl` |
| `code-reviewer.md` | Reviews diffs, suggests tests | `helpful` |
| `creative-writer.md` | Brainstorms prose + lyrics | `kawaii` |
| `omni-step-merge-copilot.md` | Reads blog + training + wiki for OmniStep | `concise` |

The user can copy any of these to `~/.hermes/hub/profiles/`,
customize the body, and launch with `hub launch <name>`.

## The hub_daemon (the runtime)

`~/.hermes/bin/hub_daemon.py` is the slim background process. It:

1. Watches `~/.hermes/hub/agents/` for new/modified files
   (inotify preferred; 5-second poll fallback)
2. Validates each agent's frontmatter against the schema
3. Registers valid agents in an in-memory index
4. Spawns on `hub launch <name>` calls (delegates to `hermes`)
5. Logs every spawn to `~/.hermes/hub/logs/<date>.jsonl`

**Estimated size:** ~200 lines Python (similar to `wiki_manager.py`).
Runs as a systemd user service (`agent-hub.service`).

CLI:

```bash
hub list                       # all registered agents
hub show <name>                # one agent's spec
hub launch <name> --query "…"  # spawn it
hub promote <wiki-note>        # note → agent
hub demote <agent>             # agent → wiki note
hub validate                   # check all agents in hub/
hub search "query"             # semantic search across wiki + hub
```

## How the wiki IS the agent spec (the promotion workflow)

```
User thinks a thought
    ↓
Manual write or note-taker daemon captures it
    ↓
~/.hermes/wiki/ideas/spike-some-paper.md
    ↓
User decides "this is an agent I want to run"
    ↓
hub promote ~/.hermes/wiki/ideas/spike-some-paper.md
    ↓
   1. Parse markdown body for role description
   2. Ask gold judge to fill frontmatter (tools, aux_model, personality)
   3. Validate schema
    ↓
~/.hermes/hub/agents/spike-some-paper.md
    ↓
hub_daemon picks it up, registers, ready to launch
    ↓
hub launch spike-some-paper --query "…"
```

The reverse (`hub demote`) takes an agent back to a wiki note,
stripping the frontmatter and moving the file.

## The 4 add-on tasks for Hermes (per Chris 2026-06-09)

Per Chris's framing, all the local-intelligence pieces are
**add-on tasks for Hermes** — they live behind the Hermes aux
interface, the Hermes launcher, and the Hermes task system.

| Add-on | Lives at | How Hermes invokes it |
|---|---|---|
| **Evolutionary Radio** | `~/projects/evolutionary-radio/` | `scroll_agent.py` skill |
| **Local Model Server (omni-va)** | `omni-va.service` | `auxiliary.*.provider=custom + base_url=:8082` |
| **Note-taker** | `~/.hermes/bin/` (daemon TBD) | `--wiki` preload on Hermes launch |
| **Agent Hub** | `~/.hermes/hub/` | `hermes launch --from-md <path>` |

The Hub is the **integrator** — it ties the other 3 add-ons to a
markdown-only surface that the user can grow organically.

## The LLM wiki (the deeper vision)

The wiki at `~/.hermes/wiki/` is the **LLM wiki of the user's
ideas**. It's:

- **Persistent** (lives across sessions, across process restarts)
- **User-owned** (not a notebook export; the user can edit any
  file directly)
- **Curated** (the note-taker daemon asks the gold judge before
  adding entries, prunes stale ideas, clusters related notes)
- **LLM-readable** (markdown, with structure the LLM can parse)
- **Opt-in to Hermes** (`hermes launch --wiki ~/.hermes/wiki`
  prepends the catalog to a fresh session's system prompt)

The note-taker is **not** the pet. The pet is the Live2D face on
top. The note-taker is the writer behind the wiki.

## The gold judge (the cornerstone)

Per Chris (2026-06-08): **the gold judge is the local model,
always, never Gemini 3 Flash, never a cloud default.** The
`~/.hermes/bin/gold_judge.py` module is the single source of truth
for "which LLM evaluates things." The `auxiliary.gold_judge` block
in `~/.hermes/config.yaml` pins the model to the omni-va slot at
`:8082/v1` with the current `brain_registry.current_model`.

The brain registry tracks "what's currently in the local slot."
When the user swaps Carnice → OmniStep → Senter → Senter Ohm, the
gold judge follows automatically.

## Why markdown?

1. **The wiki is already markdown** (per Chris 2026-06-09)
2. **The user already knows markdown** — no new spec language
3. **The LLM already knows markdown** — can read + write agents
4. **Markdown is diffable and git-trackable** — agent fleet = git repo
5. **Promotion/demotion is free** — note ↔ agent is a `mv` + frontmatter

## See also

- Blog post (canonical): [`../../blog/the-agent-hub-markdown-as-agents.md`](../../blog/the-agent-hub-markdown-as-agents.md)
- Wiki entity: [OmniStep (the agent)](../entities/omni-step.md)
- Master spec: `~/.hermes/hub/agents/omni-step.md`
- Blog (the desk-pet vision): [`../../blog/evolutionary-radio-as-desk-pet.md`](../../blog/evolutionary-radio-as-desk-pet.md)
- Blog (older integration post): [`../../blog/omnisenter-integration.md`](../../blog/omnisenter-integration.md)
- Concept: [Omni VA[](../concepts/omni-va.md) — the local model server slot (the body)
- Concept: [Omni[](../concepts/omni.md) — the umbrella multimodal family
- Concept: [Senter[](../concepts/senter.md) — the agentic family
- Concept: [Hermes auxiliary[](../concepts/hermes-auxiliary.md) — how the slot serves Hermes
- Repo: [`SouthpawIN/evolutionary-training`](https://github.com/SouthpawIN/evolutionary-training) — main blog repo
