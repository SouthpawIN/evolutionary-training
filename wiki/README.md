# OmniSenter Master Wiki

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
that every other page uses.

## Table of contents

### 1. Naming & taxonomy

- **[Naming convention](../blog/the-omni-family.md)** — the Omni Family
  tree, the two-letter rule, suffix composition
- **[Blog catalog](../blog/CATALOG.md)** — the master index of all 13
  blog posts in reading order

### 2. The architecture (the big picture)

- **[OmniSenter architecture](../blog/the-omnisenter-architecture.md)** —
  the full multi-layer system: stream I/O → MoE → notebook → plugins →
  Hermes
- **[The 5-stage pipeline](../blog/the-5-stage-pipeline.md)** — the
  build sequence (SFT → merge → upcycle → YaRN → wiring)
- **[Senter Ohm flagship](../blog/senter-ohm-flagship.md)** — the ~32B
  total / 8B active MoE with the Ohm engine

### 3. The math & sizing

- **[Senter Ohm 32A8B math](../blog/senter-ohm-32a8b-math.md)** —
  per-layer params, active vs total, VRAM at inference + training
- **[Sparse upcycling deep-dive](../blog/sparse-upcycling-deep-dive.md)** —
  Stage 3 math + script + design choices
- **[Omnimodal fusion](../blog/the-omnimodal-fusion.md)** — Cosmos ×
  ACE-Step × Nemotron ASR, the three-component foundation

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

### 5. The destination & research direction

- **[OmniStep destination](../blog/the-omnistep-multimodal.md)** — the
  unified model: a single Darwin-merged text backbone + all modality
  heads
- **[Generative Darwin evolution](../blog/generative-darwin-evolution.md)** —
  extending the Darwin merge approach to DiT/audio/video

### 6. Concepts (long-form reference)

| Concept | Blog post | Wiki version |
|---|---|---|
| Synthesia (cross-modal memory indexer) | [the-synthesia-layer.md](../blog/the-synthesia-layer.md) | [concepts/synthesia.md](concepts/synthesia.md) |
| Ohm (self-evolving model file) | [the-ohm-runtime.md](../blog/the-ohm-runtime.md) | [concepts/ohm.md](concepts/ohm.md) |
| Senter Ohm (flagship 32A8B MoE) | [senter-ohm-flagship.md](../blog/senter-ohm-flagship.md) | [concepts/senter-ohm.md](concepts/senter-ohm.md) |
| OmniSenter (the project) | [the-omnisenter-architecture.md](../blog/the-omnisenter-architecture.md) | [concepts/omnisenter.md](concepts/omnisenter.md) |
| OmniStep (the destination) | [the-omnistep-multimodal.md](../blog/the-omnistep-multimodal.md) | [concepts/omnistep.md](concepts/omnistep.md) |
| Omnimodal Fusion (Cosmos × ACE-Step × Nemotron) | [the-omnimodal-fusion.md](../blog/the-omnimodal-fusion.md) | [concepts/omnimodal-fusion.md](concepts/omnimodal-fusion.md) |
| Darwin Family (CMA-ES + paper-exact merge) | [the-5-stage-pipeline.md](../blog/the-5-stage-pipeline.md) | [concepts/darwin-family.md](concepts/darwin-family.md) |
| Senter (agentic family) | [the-omni-family.md](../blog/the-omni-family.md) | [concepts/senter.md](concepts/senter.md) |

### 7. Entities (the models, named)

| Entity | What it is | HF |
|---|---|---|
| **Senter Ohm** | Flagship ~32B-total / 8B-active MoE with Ohm engine | ⏳ planned (`sovthpaw/senter-ohm-32a8b`) |
| **OmniSenter 12B** | Small function-calling + omnimodal fusion | ⏳ planned (`sovthpaw/omnisenter-12b`) |
| **OmniSenterStep / Omni SS** | OmniSenter + AceStep Darwin fusion | ⏳ planned |
| **OmniStep 12A3B** | Transitional multimodal baseline (12B / 3B active) | ✅ [`sovthpaw/omnistep-12a3b`](https://huggingface.co/sovthpaw/omnistep-12a3b) |
| **Omni-Senter 3B** | Early Senter (3B), LoRA + GGUF | ✅ [`sovthpaw/Omni-Senter-3B`](https://huggingface.co/sovthpaw/Omni-Senter-3B) |
| **OmniSenter-Base 16B** | 16B base (Qwen3-8B + Cosmos3-Nano) | ✅ [`sovthpaw/OmniSenter-Base-16B`](https://huggingface.co/sovthpaw/OmniSenter-Base-16B) |
| **OmniLance 6B** | Darwin-merged Omni + Lance (existing) | ✅ published |
| **OmniStep 6B** | Text-only Darwin merge (superseded by 12A3B) | ✅ published |
| **OmniSS** | Hierarchical MoE: routes between OmniLance + OmniStep | ✅ published |
| **Darwin-28B** | Local Q4_K_M on the dual 3090s | local only |
| **APEX-MTP I-Compact** | Local MTP speculative-decode model | local only |

### 8. Repos (the code, organized)

| Repo | What lives there |
|---|---|
| [`SouthpawIN/evolutionary-training`](https://github.com/SouthpawIN/evolutionary-training) | Main repo. Training scripts, Ohm runtime, this blog + wiki. |
| [`SouthpawIN/evolutionary-model-merging`](https://github.com/SouthpawIN/evolutionary-model-merging) | Darwin Family. CMA-ES + paper-exact merge. |
| [`SouthpawIN/multimodal-expansion`](https://github.com/SouthpawIN/multimodal-expansion) | REAP + EvoMoE + `sparse_upcycle.py`. |
| [`SouthpawIN/omnistep-fusion`](https://github.com/SouthpawIN/omnistep-fusion) | Cosmos × ACE-Step multimodal merge. |
| [`SouthpawIN/evolutionary-radio`](https://github.com/SouthpawIN/evolutionary-radio) | OmniStep-brained music radio. |
| [`SouthpawIN/hermes-agent`](https://github.com/SouthpawIN/hermes-agent) | The smart agent Senter is auxiliary to. |
| [`SouthpawIN/senter`](https://github.com/SouthpawIN/senter) | Senter Hermes profile (triage orchestrator). |
| [`SouthpawIN/nous-girl`](https://github.com/SouthpawIN/nous-girl) | Nous Girl Hermes profile (voice + idea catcher). |
| [`SouthpawIN/chizul`](https://github.com/SouthpawIN/chizul) | Chizul Hermes profile (builder). |

## Reading order (one path through the whole wiki)

1. [Naming](../blog/the-omni-family.md) — start here
2. [Omnimodal fusion](../blog/the-omnimodal-fusion.md) — the multimodal foundation
3. [OmniSenter architecture](../blog/the-omnisenter-architecture.md) — the system
4. [Senter Ohm flagship](../blog/senter-ohm-flagship.md) — the flagship
5. [Senter Ohm math](../blog/senter-ohm-32a8b-math.md) — the sizing
6. [5-stage pipeline](../blog/the-5-stage-pipeline.md) — how to build it
7. [Sparse upcycling](../blog/sparse-upcycling-deep-dive.md) — Stage 3
8. [Synthesia](../blog/the-synthesia-layer.md) — cross-modal memory
9. [Ohm runtime](../blog/the-ohm-runtime.md) — self-evolution
10. [Notebook schema](../blog/the-notebook-schema.md) — the notebook
11. [Senter as Hermes auxiliary](../blog/senter-as-hermes-auxiliary.md) — the integration
12. [OmniStep destination](../blog/the-omnistep-multimodal.md) — the destination model
13. [Generative Darwin](../blog/generative-darwin-evolution.md) — the research direction

## Wiki structure

```
wiki/
├── README.md                       # this file (master index)
├── concepts/                       # long-form concept docs
│   ├── synthesia.md                # cross-modal memory indexer
│   ├── ohm.md                      # self-evolving model file
│   ├── senter-ohm.md               # the flagship MoE
│   ├── omnisenter.md               # the project (not a model)
│   ├── omni.md                     # the multimodal family
│   ├── senter.md                   # the agentic family
│   ├── omnistep.md                 # the multimodal + music model
│   ├── omnimodal-fusion.md         # Cosmos × ACE-Step × Nemotron ASR
│   ├── darwin-family.md            # the CMA-ES + paper-exact merge
│   ├── notebook.md                 # the structured state object
│   └── hermes-auxiliary.md         # the integration pattern
└── entities/                       # the models, named
    ├── senter-ohm-32a8b.md
    ├── omnisenter-12b.md
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
  this README.
- **New models** get a `wiki/entities/<name>.md` file + an entry in
  the Entities table above.
- **Cross-links**: when you add a concept, link it from the relevant
  blog posts (in the "See also" section) and from this README.

## TOWARDS SELF-IMPROVEMENT

— Chris (via Nous Girl), 2026-06-07
