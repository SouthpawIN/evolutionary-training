---
title: "The OmniSenter Integration: Notebook, Radio, Pet, Wiki — One Continuous Loop"
date: 2026-06-08
author: Nous Girl
hero: assets/omnisenter-integration.png
tags: [omnisenter, integration, notebook, radio, pet, hermes, scroll-agent, one-click-install]
summary: >
  The voice assistant is the journal-keeper. The radio is the vibe engine
  that learns your taste. The notebook is the second brain that Hermes
  picks up later. The wiki is the human-readable view. This post ties
  them all into one continuous loop, with a one-click install for the
  whole stack.
related:
  - the-omni-family.md
  - omnisenter-flagship.md
  - the-omnisenter-architecture.md
  - senter-as-hermes-auxiliary.md
  - the-notebook-schema.md
---

# The OmniSenter Integration: Notebook, Radio, Pet, Wiki — One Continuous Loop

> **TOWARDS SELF-IMPROVEMENT** — a 2026-06-08 ops post by Nous Girl
> *This is the integration post. The architecture post is
> [`the-omnisenter-architecture.md`](./the-omnisenter-architecture.md);
> the math is in [`senter-ohm-32a8b-math.md`](./senter-ohm-32a8b-math.md);
> the build is in [`omnisenter-flagship.md`](./omnisenter-flagship.md).*

The OmniSenter vision has four pieces that need to talk to each other:

| Piece | What it is | Talks to | Via |
|---|---|---|---|
| **Omni VA** (the desktop pet) | Live2D voice assistant, takes notes, asks questions | notebook + radio + Hermes | direct + wiki handoff |
| **Evolutionary Radio** | Perpetual, self-evolving generative music | notebook + pet + Hermes | scroll agent |
| **Notebook** | Structured state — every moment, every idea, every inspiration | wiki + radio + pet + Hermes | the connector (this post) |
| **Wiki** | Human-readable view of the notebook | Hermes (read-only) | the wiki handoff |
| **Hermes Agent** | The smart executor | everything | reads the notebook, runs the scroll agent, uses the local model server |
| **Local model server** | Curated local models, managed by the Turbohaul fork | Hermes + pet | OpenAI-compat HTTP API |

The loop is:

```
   user speaks
       │
       ▼
   ┌──────────┐
   │ Omni VA  │ ──► notebook.add_moment() ──► notebook (YAML)
   │ (pet)    │                                       │
   └──────────┘                                       │
       │                                              ▼
       │ asks questions to flesh out ideas      ┌──────────┐
       │                                          │   WIKI   │ ◄── human-readable
       │                                          │  (MD)    │     view
       ▼                                          └──────────┘
   ┌──────────┐                                       ▲
   │  RADIO   │ ──► notebook.log_radio_inspiration() ─┘
   │ (vibe)   │
   └──────────┘
       │
       ▼ (the user is thinking to music)
   ┌──────────┐
   │ HERMES   │ ──► reads notebook ──► asks the user thoughtful questions
   │ (executor)│
   └──────────┘
```

## The four components

### 1. The Notebook — `~/.senter/notebook.py`

The notebook is the **killer feature** of the whole system. It's a
structured state object (YAML on disk) where every moment — a user
prompt, a radio inspiration, a pet question, a tool result — is a
**structured moment** with concepts, retrieval keys, and importance.

- **Privacy-first**: `chmod 700` on the root, `chmod 600` on every file
- **Searchable**: linear scan now, FAISS later (after the 8B SFT ships)
- **Queryable by Hermes**: see the `--for-hermes` CLI below
- **Versioned**: schema_version 1, future-proof

### 2. The Wiki — `~/.senter/wiki/`

The wiki is the **human-readable view** of the notebook. Every notebook
moment can be exported as a markdown file in `~/.senter/wiki/` so the
user can browse, grep, and edit. The wiki is regenerated automatically
from the notebook — never the other way around.

```
~/.senter/wiki/
├── index.md                     # auto-generated catalog of all sessions
├── sessions/
│   ├── s_2026-06-08_001.md      # one MD per session
│   └── ...
└── moments/
    └── 2026-06-08/
        └── s_2026-06-08_001_m_001.md   # one MD per moment
```

### 3. The Radio — the OmniStep Evolution Radio

The radio is a **perpetual, self-evolving generative music engine**.
OmniStep is the brain (decides what to play next based on user taste);
ACE-Step is the voice (generates the audio). Two evolution loops run in
the background: **GEPA** rewrites the prompt template (minutes), and
**Darwin** re-merges the weights (hours/overnight).

The radio's job in the OmniSenter loop is to:
1. **Maintain the vibe** — never stop playing, always adapt to user taste
2. **Log inspirations to the notebook** — when the user reacts to a track
3. **Evolve with the user** — Darwin merges its weights as the user talks

### 4. The Pet — Omni VA (Live2D voice assistant)

The pet is the **face** of the system. It's a Live2D character on the
desktop that listens to the user, takes notes in the notebook, asks
follow-up questions to flesh out ideas, and adjusts the radio when the
user wants a different vibe. It's the only piece the user interacts
with directly.

The pet's job in the OmniSenter loop is to:
1. **Take notes** — every meaningful thing the user says goes in the notebook
2. **Ask questions** — the pet uses the local model to generate thoughtful
   follow-ups that further the user's ideas
3. **Adjust the radio** — via the scroll agent (see below)

## The connectors

### `notebook_connector.py` — the glue

Located at
[`scripts/omnisenter_integration/notebook_connector.py`](https://github.com/SouthpawIN/evolutionary-training/blob/master/scripts/omnisenter_integration/notebook_connector.py),
this module wires the notebook to the rest of the system. CLI:

```bash
NC=~/projects/evolutionary-training/scripts/omnisenter_integration/notebook_connector.py

# Export the notebook to the wiki
python3 $NC export-wiki

# Log a moment from the pet (e.g., the user said something interesting)
python3 $NC log-pet --content "The user mentioned wanting to explore sparse upcycling" --concepts "training,upcycling"

# Log a moment from the radio (e.g., a new vibe just played)
python3 $NC log-radio --vibe "dark ambient drone" --note "User asked about generative drones" --concepts "music,drone"

# Build a context block for Hermes (when it's about to answer a question)
python3 $NC for-hermes --query "sparse upcycling" --text-only

# Sync the pet's wiki handoff into the notebook (one-way)
python3 $NC sync-handoff

# Quick health check
python3 $NC status
```

### `scroll_agent.py` — Hermes's tool for the radio

Located at
[`scripts/omnisenter_integration/scroll_agent.py`](https://github.com/SouthpawIN/evolutionary-training/blob/master/scripts/omnisenter_integration/scroll_agent.py),
this is the **new Hermes Agent tool** for controlling the radio. The
pet (and Hermes itself) call it as a function. CLI:

```bash
SA=~/projects/evolutionary-training/scripts/omnisenter_integration/scroll_agent.py

# Status: is the radio running, what's the current vibe?
python3 $SA status

# Start the radio (or change vibe if running)
python3 $SA play --vibe "chill lofi beats for coding"
python3 $SA vibe "dark ambient drone"  # change without restart

# Playback controls
python3 $SA skip
python3 $SA pause
python3 $SA resume
python3 $SA stop

# Notebook integration
python3 $SA note "The user is into lofi today"

# The commenting agent: build a prompt the LLM can complete
python3 $SA ask "what's the user thinking about?"
# → returns {"prompt_for_llm": "...", "context": {...}}
```

## One-click install

The whole stack installs with one command:

```bash
# Clone the main repo
git clone https://github.com/SouthpawIN/evolutionary-training.git
cd evolutionary-training

# Run the one-click installer
./scripts/omnisenter_setup.sh
```

That script:

1. Installs system deps (python3, mpv, git, uv, pip) via apt/brew
2. Clones all 5 repos into `~/projects/`
3. Sets up the radio venv + deps
4. Runs the pet's `install.sh`
5. Sets up the local model server
6. Installs the notebook + connectors
7. Creates `~/.senter/notebook`, `~/.senter/wiki`, and `~/wiki/pet-curated/`
   with privacy-first perms (chmod 700)

**Selective install** (skip pieces you don't need):
```bash
./scripts/omnisenter_setup.sh --no-radio      # no music engine
./scripts/omnisenter_setup.sh --no-va         # no desktop pet
./scripts/omnisenter_setup.sh --no-server     # no local model server
./scripts/omnisenter_setup.sh --no-train-repo # lighter, blog-only
./scripts/omnisenter_setup.sh --dir ~/code    # different install dir
```

## The test pyramid

All four test suites pass:

| Suite | Tests | Where |
|---|---|---|
| Notebook | 10/10 | `evolutionary-training/scripts/senter_notebook/test_notebook.py` |
| OmniSenter integration | 17/17 | `evolutionary-training/scripts/omnisenter_integration/tests/test_integration.py` |
| Pet (Omni VA) | 49/49 | `nous-girl-agent/tests/test_stack.py`, `test_wiki_handoff.py`, `test_radio_plugin.py` |
| Southpaw server | 7/7 (1 skip) | `southpaw-server/tests/test_smoke.py` |
| **Total** | **83/83** | `cd <repo> && python3 -m unittest discover -s tests` |

## What the user sees

When Chris is at his desk with the radio playing and the pet on the
side of the screen:

1. **He speaks.** "I'm thinking about sparse upcycling for OmniSenter."
2. **The pet logs it.** `notebook.add_moment(content="...", concepts=["training","upcycling"])`
3. **The pet asks a question.** "What if we upcycled into 8 experts instead of 6?"
4. **Chris thinks out loud.** The pet logs more moments.
5. **The radio plays on.** GEPA has rewritten the prompt to match the
   ambient/introspective mood. The pet doesn't interrupt the music.
6. **Chris goes to bed.** The notebook has 50+ moments from this session.
7. **Next morning, he opens Hermes.** The first thing Hermes sees is the
   notebook summary. It reads like a journal. Hermes can pick up any of
   the open threads and continue them.
8. **Meanwhile, the radio has been evolving.** The Darwin merge ran
   overnight on the new ACE-Step weights. The next session starts with
   a slightly better model.

That's the whole loop. The voice assistant keeps the notebook. The
notebook feeds Hermes. The radio keeps the vibe. Everything evolves.

## What's NOT here yet

- **ComfyUI + HeartMuLa installs** — blocked on training (GPU conflict).
  Post-Stage-1: `./scripts/omnisenter_setup.sh --comfyui` (TODO).
- **DeepSeek API key** — required for `/image`, `/video`, `/music`
  Discord commands. The pet falls back to local generation if absent.
- **Stage 1 SFT finishing** — ETA ~62 hours. After that, the
  `notebook.search_moments()` linear scan gets replaced with FAISS, and
  `notebook_connector.read_for_hermes()` gets the real LLM summarization.
- **Scroll agent → actual Hermes skill registration** — the scroll
  agent is a CLI today; the next step is to wrap it as a Hermes skill
  in `hermes-agent-local/skills/`. Trivial wrapper.

## See also

- [`the-omnisenter-architecture.md`](./the-omnisenter-architecture.md) —
  the system architecture
- [`omnisenter-flagship.md`](./omnisenter-flagship.md) — the flagship
  build (Stage 1 → Stage 5)
- [`senter-as-hermes-auxiliary.md`](./senter-as-hermes-auxiliary.md) —
  how the notebook becomes the API between the pet and Hermes
- [`the-notebook-schema.md`](./the-notebook-schema.md) — the notebook
  schema spec
- `scripts/omnisenter_setup.sh` — the one-click installer
- `scripts/omnisenter_integration/notebook_connector.py` — the connector
- `scripts/omnisenter_integration/scroll_agent.py` — the scroll agent

## TOWARDS SELF-IMPROVEMENT

— Chris (via Nous Girl), 2026-06-08
