---
title: "The Evolutionary Radio is the Desk Pet: One Button, the Whole Local Intelligence"
date: 2026-06-08
author: Nous Girl
hero: assets/desk-pet.png
tags: [evolutionary-radio, omni-va, senter, omnistep, local-model, gold-judge, wiki, vault, desk-pet, hermes, agent, polite-vram]
summary: >
  The Evolutionary Radio isn't just a music app. It's the user's
  **desk pet** — the single button that spins up the whole local
  intelligence stack: a VRAM-polite local model server (the
  omni-va), a brain agent (the local model itself), a user-idea
  LLM wiki, a vault of profile templates, a Wikipedia compaction
  layer, and the music radio. The local model IS the gold judge.
  The local model IS the Hermes aux. The local model IS the
  brain. *(First published 2026-06-08 — Chris's epiphany, captured
  here as the canonical architecture.)*
related:
  - the-omni-family.md
  - the-omni-va-architecture.md
  - senter-as-hermes-auxiliary.md
  - the-omnisenter-architecture.md
  - the-5-stage-pipeline.md
---

# The Evolutionary Radio is the Desk Pet: One Button, the Whole Local Intelligence

> **TOWARDS SELF-IMPROVEMENT** — a 2026-06-08 architecture post by Chris (via Nous Girl)

> **The epiphany, in one paragraph.** The Evolutionary Radio is not
> a music app. It's the **desk pet** — the single button that, when
> pressed, spins up the whole local intelligence stack: a VRAM-polite
> local model server (the omni-va), a brain agent (the local model
> itself), a user-idea LLM wiki, a vault of profile templates, a
> Wikipedia compaction layer, and the music radio. The local model
> IS the **gold judge**. The local model IS the **Hermes aux**. The
> local model IS the **brain**. All four roles are the same model.
> Pick the largest that fits in current VRAM (OmniStep 8B → Senter
> 32A8B → Senter Ohm flagship), let the polite VRAM pattern
> auto-rotate. When the user is doing something VRAM-heavy, the
> radio defers; when VRAM opens up, the radio spins up the bigger
> brain. Always local, never cloud-default-judge, never
> Gemini 3 Flash.

## TL;DR — the whole picture

```
                        ┌──────────────────────────────────┐
                        │   USER PRESSES "START RADIO"     │
                        │   ./evolutionary-radio/start_radio.sh start
                        └────────────┬─────────────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              ▼                      ▼                      ▼
       ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
       │ omni-va      │       │ The Brain    │       │ The Vault    │
       │ local model  │       │ (omni client │       │ ~/.hermes/   │
       │ server       │       │  + brain.py) │       │   vault/     │
       │ :8082        │       │              │       │  templates/  │
       │ wake-on-ping │       │ Generates    │       │  profiles/   │
       │ polite VRAM  │       │   music      │       │  raw/        │
       │ auto-rotate  │       │ Maintains    │       │              │
       │              │       │   wiki       │       │ Brain picks  │
       │ Tier 1:      │       │ Curates      │       │  template →  │
       │  OmniStep 8B │       │   templates  │       │  user copies │
       │ Tier 2:      │       │ Compacts     │       │  → profile  │
       │  Senter 32A8B│       │   wiki →     │       │              │
       │ Tier 3:      │       │   Wikipedia   │       │ Wikipedia →  │
       │  Senter Ohm  │       │ Hermes aux   │       │  Hermes      │
       └──────┬───────┘       └──────┬───────┘       │  preloaded   │
              │                      │               └──────┬───────┘
              └──────────┬───────────┘                      │
                         ▼                                  │
              ┌──────────────────────┐                     │
              │  ~/.hermes/wiki/      │◄────────────────────┘
              │   the LLM wiki        │  (transferred to Hermes on launch)
              │   ideas/projects/...  │
              │   followups/          │
              │   vec/ (sqlite-vec)   │
              │   index.md (Wikipedia)│
              └──────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Hermes Agent         │
              │  (the executor)      │
              │  aux = omni-va        │
              │  preloaded = wiki     │
              │  the "do" half        │
              └──────────────────────┘
```

**One button starts the whole thing. The radio IS the desk pet.**

## What the user actually does

```bash
# One command, in a terminal:
~/projects/evolutionary-radio/start_radio.sh start --vibe="chill lofi beats for coding"

# What happens (silent, in 30 seconds):
#   1. omni-va.service is enabled + started (the local model server)
#   2. The vault directory is prepared (~/.hermes/vault/templates/)
#   3. The radio's main loop starts
#   4. The brain agent (in the same process) starts watching for ideas
#   5. The Evolution Radio queue fill loop starts generating tracks
#   6. mpv starts playing
#   7. Everything is live

# Now the user can:
#   - Talk to the brain:  curl :8082/v1/chat/completions
#   - Inspect the wiki:   curl :8082/wiki/stats
#   - Spawn a Hermes session with the wiki preloaded:
#       curl -X POST :8082/hermes/launch
#   - Add a new idea to the wiki: just talk to the radio / write a file
#   - Pick a profile template:  cp ~/.hermes/vault/templates/X.yaml \
#                                  ~/.hermes/vault/profiles/myprofile.yaml
```

## The four roles, all the same model

This is the core insight of the epiphany. The local model is
**one thing** that does **four jobs** in this architecture:

| Role | What it does | Who calls it |
|---|---|---|
| **Brain** | Generates music, reasons about user ideas, curates templates | The radio's loops 1-4 |
| **Gold Judge** | Scores / evaluates / ranks LLM outputs (idea clusters, prompt variants, fitness) | brain.py, GEPA, Darwin, the note-taker |
| **Hermes aux** | The auxiliary LLM for compression, summarization, web_extract, session_search, skills_hub, approval, mcp, title_generation, curator (9 of 10 aux tasks already wired in `~/.hermes/config.yaml`) | `auxiliary.*.provider=custom + base_url=:8082` |
| **Wikipedia compactor** | Periodically condenses the wiki into a single-page summary for Hermes preload | brain.compact_wikipedia() |

All four roles are served by the **same model in the same slot**:
the omni-va at `http://127.0.0.1:8082/v1`. They differ only in
**what they ask** of the model (system prompt + user message) and
**how they use the response** (parse a YAML, extract a score, etc.).

The 4-model lineup in the slot (per
[`the-omni-family.md`](./the-omni-family.md)):

- **OmniStep** (8B) — default brain when VRAM is tight
- **OmniStep Ohm** (8B + self-evolution) — same, gets better over time
- **Senter** (32A8B MoE) — heavier agentic brain
- **Senter Ohm** (32A8B + Ohm) — the **flagship**

The slot auto-rotates via the **polite VRAM pattern** (see
[`the-omni-va-architecture.md`](./the-omni-va-architecture.md)):
probe free VRAM, pick a tier, give it back when not in use. If
the user is doing something VRAM-heavy, the radio defers. If
the user is idle, the bigger brain fits.

## The Gold Judge rule (the cornerstone)

Per Chris (2026-06-08): **the gold judge is the auxiliary model,**
**never Gemini 3 Flash, never a cloud default, always the local**
**model.** Implemented in two places:

1. `~/.hermes/config.yaml` has a new `auxiliary.gold_judge` block:

   ```yaml
   auxiliary:
     gold_judge:
       provider: custom
       base_url: http://127.0.0.1:8082/v1
       model: carnice-35a3b      # placeholder; senter when built
       api_key: not-needed
       timeout: 120
       multimodal: true
     brain_registry:
       current_model: carnice-35a3b
       currentendpoint: http://127.0.0.1:8082/v1
   ```

2. `/home/sovthpaw/.hermes/bin/gold_judge.py` — the helper module
   for any code that needs to "ask the LLM to evaluate." Public API:
   ```python
   from gold_judge import judge, score, rank, client
   score("this prompt is great", rubric="clarity")  # → 0.0-1.0
   ranked = rank([cand1, cand2, ...], rubric="usefulness")
   ```
   The same module is imported by `brain.py` and by the future
   GEPA prompt evolution when we wire it up.

**The brain registry** at the bottom of the gold_judge block is a
**single source of truth** for "what's currently in the local
slot." When Senter is built, the gold_judge.model + brain_registry
flip together (see the swap procedure in
[`the-omni-va-architecture.md`](./the-omni-va-architecture.md)).

## The note-taker loop (the brain's new role)

The brain is no longer just a music generator. With
`/home/sovthpaw/projects/evolutionary-radio/code/brain.py`, the
brain gains two new roles on top of the existing music loops:

**`brain.curate_event(event)`** — the note-taker.
  1. Politely checks VRAM (defer if tight)
  2. Asks the gold judge: "is this a new idea worth adding?"
  3. If yes, gets a slug, title, body, kind, importance
  4. Writes to the wiki via `wiki_manager.py`
  5. Returns the entry's slug

**`brain.compact_wikipedia(max_entries=30)`** — the compactor.
  1. Politely checks VRAM
  2. Reads the top N entries by importance
  3. Asks the gold judge to compose a Wikipedia-style summary
  4. Writes the result to `~/.hermes/wiki/index.md`
  5. Returns the path

Both methods use the gold_judge under the hood. Both gracefully
defer (return None) when VRAM is tight. The user's existing radio
loop is the trigger — but in the future, events can come from
calendar, chat, voice transcriptions, manual notes, etc.

## The vault (templates + profiles + raw)

`~/.hermes/vault/` is the on-ramp from "the user has an idea" to
"Hermes has a profile for it." Three subdirectories:

```
~/.hermes/vault/
├── templates/         # YAML template files, can be copied to profiles/
├── profiles/          # user's customized copies of templates
├── raw/               # unsorted user input (notes, voice, etc.)
└── README.md          # explains the workflow
```

**Sample templates** (4 shipped in `templates/`):

| Template | Purpose | Personality |
|---|---|---|
| `personal-assistant.yaml` | Default general-purpose profile | `nous_girl` |
| `code-reviewer.yaml` | Reviews diffs, suggests tests | `helpful` |
| `creative-writer.yaml` | Brainstorms prose + lyrics | `kawaii` |
| `omni-step-merge-copilot.yaml` | Reads blog + training + wiki for OmniStep work | `concise` |

A template has: `name`, `description`, `system_prompt`, `aux_model`
(defaults to the gold judge), `toolsets`, `personality`, `created`,
`updated`. The schema is **Hermes-compatible** — `hermes launch
--profile <name>.yaml` works without translation.

The workflow:

```bash
# Pick a template
cp ~/.hermes/vault/templates/code-reviewer.yaml \
   ~/.hermes/vault/profiles/myproject.yaml

# Edit it
$EDITOR ~/.hermes/vault/profiles/myproject.yaml

# Launch Hermes with it
hermes launch --profile myproject

# Or, the radio's note-taker can surface the profile into the wiki
# so the LLM knows about it for context
brain.curate_event({"source": "profile", "raw": "user created 'myproject'"})
```

## What ships in the radio today (2026-06-08)

Already wired and working:

- `code/brain.py` — Brain class wrapping OmniClient + WikiManager + GoldJudge
- `code/omni_client.py` — now has `polite_chat()` that defers when VRAM tight
- `code/darwin.py` — CMA-ES weight evolution (untouched)
- `code/gepa.py` — prompt evolution (untouched)
- `start_radio.sh` — now starts omni-va + brain + vault before the radio loop
- 9 of 10 Hermes aux tasks already point to omni-va (the 10th is vision, on `auto`)
- Gold Judge config block in `~/.hermes/config.yaml`
- `~/.hermes/bin/gold_judge.py` — single source of truth for LLM-as-judge
- `~/.hermes/bin/polite_vram.py` — shared VRAM probe + tier picker (TurboHaul fork uses it too)
- `~/.hermes/bin/wiki_manager.py` — the wiki CRUD + search
- 3 seed wiki entries: OmniStep merge plan, Winter album idea, a followup about 1M-ctx
- 4 vault templates: personal-assistant, code-reviewer, creative-writer, omni-step-merge-copilot

Still to build (this is the work-in-progress list):

- ✅ **Note-taker daemon** — DONE 2026-06-09. `~/.hermes/bin/note_taker.py`
  watches `~/.hermes/wiki/events/`, `~/.hermes/vault/raw/`, and
  `~/.hermes/hub/raw/`, feeds events to `brain.curate_event()`,
  defers politely when VRAM is tight. Runs as a systemd user service
  (`note-taker.service`). Tested — drop + sweep + defer + log works
  end-to-end.
- ✅ **Agent Hub runtime** (`~/.hermes/bin/hub_daemon.py`) — DONE
  2026-06-09. 425 lines, 4 agents seeded from vault YAML templates.
- **sqlite-vec index** — semantic search for the wiki. The vec/
  directory exists; the index build is TBD.
- **Periodic Wikipedia compaction** — a cron / systemd timer that
  calls `brain.compact_wikipedia()` every hour or on-event.
- **`/wiki/*` write endpoints** on the omni-va proxy (currently
  read-only via the proxy — writes go through `wiki_manager.py`
  directly).
- **OmniStep on Carnice swap** — when Stage 1 SFT finishes, swap
  the GGUF in the omni-va service file from Carnice to OmniStep.
  All wired up (see the swap procedure in the omni-va arch post).

## The key design choices (and why)

1. **One model, four roles.** Brain, judge, aux, compactor — all
   the same model. Different system prompts, same weights. This
   means the user trusts ONE thing, not four. The aux isn't a
   cloud-default you don't know. It's the same Carnice / OmniStep /
   Senter Ohm you're running locally.

2. **Wake-on-ping + auto-rotate.** The omni-va slot costs 0 VRAM
   when idle. When called, the proxy probes free VRAM and picks
   the right tier. After training finishes (~50h from now), the
   same service moves to auto-spill (full GPU 0). 30+ t/s at
   Senter Ohm speed. 10 t/s at Carnice (PCIe-bound) speed. The
   user doesn't touch it.

3. **Polite VRAM everywhere.** The radio's `polite_chat()` defers
   when free VRAM is below threshold. TurboHaul's spawner picks
   the right ngl tier. The omni-va proxy's ngl probe works the
   same way. Three repos, one pattern.

4. **Wiki as bridge, not notebook.** The notebook is session-state
   (transient). The wiki is user-owned (persistent). The radio
   maintains the wiki, the compactor condenses it, Hermes
   preloads it. The user can always browse the wiki directly.

5. **Vault templates, not raw configs.** A new profile starts
   from a template, not from a blank YAML. The template includes
   the right toolsets, personality, aux_model. The user fills in
   the system prompt.

6. **No "judge" by Gemini 3 Flash.** This is the cornerstone. The
   gold judge is always the local model. Always. (See
   `~/.hermes/bin/gold_judge.py` and the `auxiliary.gold_judge`
   block.)

## The reading order

If you're new to this:

1. [`the-omni-family.md`](./the-omni-family.md) — the 4-model lineup
2. [`the-omni-va-architecture.md`](./the-omni-va-architecture.md) —
   the local model server itself
3. [`senter-as-hermes-auxiliary.md`](./senter-as-hermes-auxiliary.md)
   — Senter's dual role (standalone + Hermes aux)
4. This post — the unified vision

If you want to **use** it:

1. `systemctl --user enable --now omni-va.service`
2. `~/projects/evolutionary-radio/start_radio.sh start`
3. `curl :8082/wiki/stats` to confirm the wiki is live
4. `curl -X POST :8082/hermes/launch` to spawn Hermes with wiki preloaded

If you want to **build** on it:

- `/home/sovthpaw/.hermes/bin/wiki_manager.py` — add write endpoints, vec search
- `/home/sovthpaw/.hermes/bin/gold_judge.py` — extend with the gold standards corpus
- `/home/sovthpaw/projects/evolutionary-radio/code/brain.py` — wire the
  note-taker daemon loop
- `~/.hermes/vault/templates/` — add more templates as needed

## See also

- [`the-omni-family.md`](./the-omni-family.md) — canonical 4-model naming
- [`the-omni-va-architecture.md`](./the-omni-va-architecture.md) — the local model server
- [`senter-as-hermes-auxiliary.md`](./senter-as-hermes-auxiliary.md) — the dual role
- [`the-omnisenter-architecture.md`](./the-omnisenter-architecture.md) — the Senter family arch (sibling)
- [`the-5-stage-pipeline.md`](./the-5-stage-pipeline.md) — how Senter is built
- `~/spring-clean-checkpoint-2026-06-08.md` — the multi-agent handoff

---

*TOWARDS SELF-IMPROVEMENT.*
