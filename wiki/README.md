# OmniSenter / Omni Family Master Wiki

> **The consolidated knowledge base for the OmniSenter project.** Every
> blog post, every concept, every model — in catalog order, all in one
> place.

This is the **public, versioned** knowledge base. The local Obsidian-style
notebook at `~/wiki/` is the **personal** notebook (with personal infra,
the NVIDIA partnership note, the Discord hub, build logs, and other
private context). The blog at [`../blog/`](../blog/) is the
**published** content. This wiki is the **glue** — it points to both,
organized in catalog order.

## Start here

If you only read one page, read **[`../blog/the-omni-family.md`](../blog/the-omni-family.md)**.
It explains the naming convention (Omni / Senter / Ohm / Senter Ohm)
that every other page uses. **"OmniSenter" is the project name, not
a model.**

If you read two pages, add **[`../blog/the-agent-hub-markdown-as-agents.md`](../blog/the-agent-hub-markdown-as-agents.md)**.
It's the unified surface that ties the local model server, the
evolutionary radio, the note-taker, and the LLM wiki together.

## Table of contents

### 1. Naming & taxonomy

- **[Naming convention](../blog/the-omni-family.md)** — the Omni Family
  tree, the 4-model lineup, the build-blocks rule (Cosmos + Nemotron
  0.6B ASR + 8B SFT + ACE-Step, always all 4)
- **[Blog catalog](../blog/CATALOG.md)** — the master index of all 18
  blog posts in reading order

### 2. The architecture (the big picture)

- **[OmniSenter architecture](../blog/the-omnisenter-architecture.md)** —
  the full multi-layer system: stream I/O → MoE → notebook → plugins →
  Hermes
- **[The 5-stage pipeline](../blog/the-5-stage-pipeline.md)** — the
  build sequence (SFT → merge → upcycle → YaRN → wiring)
- **[The Omni VA architecture](../blog/the-omni-va-architecture.md)** —
  the local model server: wake-on-ping, liquid VRAM, auto-heal
- **[The Agent Hub](../blog/the-agent-hub-markdown-as-agents.md)** —
  the unified vault + wiki + model server + radio + note-taker
  (markdown as agents)
- **[Evolutionary Radio is the Desk Pet](../blog/evolutionary-radio-as-desk-pet.md)** —
  the one-button experience that starts the whole local intelligence
- **[OmniSenter integration (older)](../blog/omnisenter-integration.md)** —
  the glue: notebook ↔ radio ↔ pet ↔ wiki ↔ Hermes

### 3. The math & sizing

- **[Senter Ohm 32A8B math](../blog/senter-ohm-32a8b-math.md)** —
  per-layer params, active vs total, VRAM at inference + training
- **[Sparse upcycling deep-dive](../blog/sparse-upcycling-deep-dive.md)** —
  Stage 3 math + script + design choices
- **[Omnimodal fusion](../blog/the-omnimodal-fusion.md)** — Cosmos ×
  ACE-Step × Nemotron ASR, the three-component foundation
- **[Stages 2→4 orchestration](../blog/stages-2-to-4-prep.md)** — the
  exact copy-paste commands (revision banner: this predates the
  2026-06-08 architecture rule, see the doc)

### 4. The concepts (what makes it special)

- **[Synthesia (cross-modal memory)](../blog/the-synthesia-layer.md)** —
  the joint `(text, audio, image)` embedding indexer, with 10 concrete
  benefits
- **[Ohm (self-evolving engine)](../blog/the-ohm-runtime.md)** — the
  `.ohm` file format, the background CMA-ES loop, the safety properties
- **[Notebook schema](../blog/the-notebook-schema.md)** — the structured
  state object (256K context, multi-modal entries, compaction policy)
- **[Senter as Hermes auxiliary](../blog/senter-as-hermes-auxiliary.md)** —
  the notebook-as-API pattern, escalation rules, cost model
- **[Agent Hub (markdown as agents)](../blog/the-agent-hub-markdown-as-agents.md)** —
  the unified vault + wiki + slot + radio + note-taker

### 5. The destination & research direction

- **[OmniStep destination](../blog/the-omnistep-multimodal.md)** — the
  unified model: a single Darwin-merged text backbone + all modality
  heads
- **[Generative Darwin evolution](../blog/generative-darwin-evolution.md)** —
  extending the Darwin merge approach to DiT/audio/video

### 6. Concepts (long-form reference)

| Concept | Wiki version | Related blog / doc |
|---|---|---|
| **Omni** (the multimodal family) | [concepts/omni.md](concepts/omni.md) | [the-omni-family.md](../blog/the-omni-family.md) |
| **OmniStep** (8B = Cosmos + ASR + ACE-Step + Agentic SFT) | [concepts/omnistep.md](concepts/omnistep.md) | [the-omnistep-multimodal.md](../blog/the-omnistep-multimodal.md) |
| **Senter** (the agentic family, 32A8B MoE) | [concepts/senter.md](concepts/senter.md) | [the-omni-family.md](../blog/the-omni-family.md) |
| **Senter Ohm** (flagship with self-evolution) | [concepts/senter-ohm.md](concepts/senter-ohm.md) | [omnisenter-flagship.md](../blog/omnisenter-flagship.md) |
| **Ohm** (the self-evolving engine) | [concepts/ohm.md](concepts/ohm.md) | [the-ohm-runtime.md](../blog/the-ohm-runtime.md) |
| **Omnimodal Fusion** (Cosmos × ACE-Step × Nemotron) | [concepts/omnimodal-fusion.md](concepts/omnimodal-fusion.md) | [the-omnimodal-fusion.md](../blog/the-omnimodal-fusion.md) |
| **OmniSenter** (the project) | [concepts/omnisenter.md](concepts/omnisenter.md) | [the-omnisenter-architecture.md](../blog/the-omnisenter-architecture.md) |
| **Synthesia** (cross-modal memory) | [concepts/synthesia.md](concepts/synthesia.md) | [the-synthesia-layer.md](../blog/the-synthesia-layer.md) |
| **Notebook** (the structured state object) | [concepts/notebook.md](concepts/notebook.md) | [the-notebook-schema.md](../blog/the-notebook-schema.md) |
| **Hermes auxiliary** (the integration pattern) | [concepts/hermes-auxiliary.md](concepts/hermes-auxiliary.md) | [senter-as-hermes-auxiliary.md](../blog/senter-as-hermes-auxiliary.md) |
| **Darwin Family** (CMA-ES + paper-exact merge) | [concepts/darwin-family.md](concepts/darwin-family.md) | [the-5-stage-pipeline.md](../blog/the-5-stage-pipeline.md) |
| **Omni VA** (the local model server slot) | [concepts/omni-va.md](concepts/omni-va.md) | [the-omni-va-architecture.md](../blog/the-omni-va-architecture.md) |
| **Evolutionary Radio** (the perpetual music engine) | [concepts/evolutionary-radio.md](concepts/evolutionary-radio.md) | [evolutionary-radio-as-desk-pet.md](../blog/evolutionary-radio-as-desk-pet.md) |
| **Agent Hub** (markdown as agents, the LLM wiki) | [concepts/agent-hub.md](concepts/agent-hub.md) | [the-agent-hub-markdown-as-agents.md](../blog/the-agent-hub-markdown-as-agents.md) |

### 7. Entities (the models, named)

| Entity | What it is | HF status |
|---|---|---|
| **OmniStep** (8B) | Multimodal + music + agentic, 4 build blocks | ⏳ Stage 1 running (ETA Thu 2026-06-10) |
| **OmniStep Ohm** (8B + Ohm) | Same 8B + .ohm self-evolution engine | ⏳ Stage 5 |
| **Senter** (32A8B MoE) | Sparse-upcycled from OmniStep, agentic flagship | ⏳ Stage 3 |
| **Senter Ohm** (32A8B + Ohm) | Flagship with self-evolution | ⏳ Stage 5 |
| **OmniStep (the agent)** | The local AI persona — the soul on top of the omni-va slot. Lives at `~/.hermes/hub/agents/omni-step.md`. | [entities/omni-step.md](entities/omni-step.md) |
| **OmniSenter-Base 16B** (transitional) | 16B base (Qwen3-8B + Cosmos3-Nano Darwin merge) | ✅ [`sovthpaw/OmniSenter-Base-16B`](https://huggingface.co/sovthpaw/OmniSenter-Base-16B) |
| **OmniStep 12A3B** (transitional) | 12B-total / 3B-active MoE, multimodal | ✅ [`sovthpaw/omnistep-12a3b`](https://huggingface.co/sovthpaw/omnistep-12a3b) |
| **Omni-Senter 3B** (transitional) | Early Senter (3B), LoRA + GGUF | ✅ [`sovthpaw/Omni-Senter-3B`](https://huggingface.co/sovthpaw/Omni-Senter-3B) |
| **Darwin-28B** | Local Q4_K_M on the dual 3090s | local only |
| **APEX-MTP I-Compact** | Local MTP speculative-decode model | local only |

### 8. Repos (the code, organized)

| Repo | What lives there |
|---|---|
| [`SouthpawIN/evolutionary-training`](https://github.com/SouthpawIN/evolutionary-training) | Main repo. Training scripts, Ohm runtime, this blog + wiki, senter notebook, Stage 2/3/4 plans |
| [`SouthpawIN/evolutionary-model-merging`](https://github.com/SouthpawIN/evolutionary-model-merging) | Darwin Family. CMA-ES + paper-exact merge |
| [`SouthpawIN/multimodal-expansion`](https://github.com/SouthpawIN/multimodal-expansion) | REAP + EvoMoE + `sparse_upcycle.py` |
| [`SouthpawIN/omnistep-fusion`](https://github.com/SouthpawIN/omnistep-fusion) | Cosmos × ACE-Step multimodal merge |
| [`SouthpawIN/evolutionary-radio`](https://github.com/SouthpawIN/evolutionary-radio) | OmniStep-brained music radio (upstream) |
| [`SouthpawIN/nous-girl-agent`](https://github.com/SouthpawIN/nous-girl-agent) | The desktop pet, local model server, vendored radio + wiki-handoff |
| [`SouthpawIN/hermes-agent`](https://github.com/SouthpawIN/hermes-agent) | The smart agent Senter is auxiliary to |
| [`SouthpawIN/senter`](https://github.com/SouthpawIN/senter) | Senter Hermes profile (triage orchestrator) |
| [`SouthpawIN/nous-girl`](https://github.com/SouthpawIN/nous-girl) | Nous Girl Hermes profile (voice + idea catcher) |
| [`SouthpawIN/chizul`](https://github.com/SouthpawIN/chizul) | Chizul Hermes profile (builder) |
| [`omnisenter-blog`](https://github.com/southpawin/southpawin.github.io) | The deployed site (mirror of `evolutionary-training/blog/`) |

## Reading order (one path through the whole wiki)

1. [Naming](../blog/the-omni-family.md) — start here
2. [Omnimodal fusion](../blog/the-omnimodal-fusion.md) — the multimodal foundation
3. [OmniSenter architecture](../blog/the-omnisenter-architecture.md) — the system
4. [Senter Ohm flagship](../blog/omnisenter-flagship.md) — the flagship (renamed from `senter-ohm-flagship.md` 2026-06-08)
5. [Senter Ohm math](../blog/senter-ohm-32a8b-math.md) — the sizing
6. [5-stage pipeline](../blog/the-5-stage-pipeline.md) — how to build it
7. [Sparse upcycling](../blog/sparse-upcycling-deep-dive.md) — Stage 3
8. [OmniStep destination](../blog/the-omnistep-multimodal.md) — the destination model
9. [Synthesia](../blog/the-synthesia-layer.md) — cross-modal memory
10. [Ohm runtime](../blog/the-ohm-runtime.md) — self-evolution
11. [Notebook schema](../blog/the-notebook-schema.md) — the notebook
12. [Senter as Hermes auxiliary](../blog/senter-as-hermes-auxiliary.md) — the integration
13. [Omni VA architecture](../blog/the-omni-va-architecture.md) — the local model server
14. [Evolutionary Radio is the Desk Pet](../blog/evolutionary-radio-as-desk-pet.md) — the unified vision
15. [The Agent Hub](../blog/the-agent-hub-markdown-as-agents.md) — markdown as agents (2026-06-09)
16. [OmniSenter integration](../blog/omnisenter-integration.md) — the glue
17. [Stages 2→4 orchestration](../blog/stages-2-to-4-prep.md) — the command recipe
18. [Generative Darwin](../blog/generative-darwin-evolution.md) — the research direction

## Wiki structure

```
wiki/
├── README.md                       # this file (master index)
├── concepts/                       # 14 long-form concept docs
│   ├── omni.md                     # the multimodal family
│   ├── omnistep.md                 # 8B = Cosmos+ASR+ACE-Step+Agentic SFT
│   ├── senter.md                   # 32A8B MoE agentic family
│   ├── senter-ohm.md               # flagship with Ohm engine
│   ├── ohm.md                      # self-evolving model file
│   ├── omnisenter.md               # the project (not a model)
│   ├── omnimodal-fusion.md         # Cosmos × ACE-Step × Nemotron ASR
│   ├── darwin-family.md            # CMA-ES + paper-exact merge
│   ├── notebook.md                 # the structured state object
│   ├── hermes-auxiliary.md         # the integration pattern
│   ├── synthesia.md                # cross-modal memory indexer
│   ├── omni-va.md                  # the local model server slot
│   ├── evolutionary-radio.md       # the perpetual music engine
│   └── agent-hub.md                # markdown as agents + LLM wiki
└── entities/                       # 9 model entity pages (incl. omni-step the agent)
    ├── senter-ohm-32a8b.md
    ├── omnisenter-12b.md
    ├── omni-step.md               # the AGENT (not the model)
    ├── omnisenterstep.md
    ├── omnistep-12a3b.md
    ├── omni-senter-3b.md
    ├── omnisenter-base-16b.md
    ├── darwin-28b.md
    └── apex-mtp.md
```

## Personal vs public

The local `~/wiki/` Obsidian notebook contains personal/infrastructure
content (NVIDIA partnership details, Discord server setup, build logs,
GPU rig, personal APIs) that is **not** version-controlled in the repo.
This `wiki/` is the public, versioned counterpart.

The blog at `../blog/` is the published long-form content. This wiki
indexes it and adds concept/entity pages that summarize or extend the
blog posts.

## How to update

- **Blog posts** live in `../blog/`. Edit them there.
- **New concepts** get a `wiki/concepts/<name>.md` file + an entry in
  this README's section 6.
- **New models** get a `wiki/entities/<name>.md` file + an entry in
  section 7.
- **Cross-links**: when you add a concept, link it from the relevant
  blog posts (in the "See also" section) and from this README.

## Naming rules (read first)

Per the 2026-06-08 architecture rule (in [`../AGENTS.md`](../AGENTS.md)):

1. **"OmniSenter" is the project name. Never a model name.**
2. **The 4 model names are exactly**: `OmniStep`, `OmniStep Ohm`,
   `Senter`, `Senter Ohm`.
3. **ACE-Step is mandatory** in every Omni model (Standard and Ohm
   alike). Music is in the DNA.
4. **Cosmos + Nemotron 0.6B ASR + 8B SFT + ACE-Step** are the
   4 mandatory build blocks. Remove none.

## TOWARDS SELF-IMPROVEMENT

— Chris (via Nous Girl), 2026-06-07 (initial), updated 2026-06-09
