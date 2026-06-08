# OmniSenter Blog Catalog

> **The one page that indexes everything.** Every post in the OmniSenter
> blog catalog, with summaries, reading order, and cross-links to HF
> models + GitHub repos.

## Start here

If you only read one post, read **[`the-omni-family.md`](./the-omni-family.md)**.
It explains the naming convention that every other post uses. Without
it, "Senter", "Ohm", and "OmniSenter" sound like noise.

## Current state (transitional)

The models currently published on HuggingFace under `sovthpaw/` are the
**v1 transitional** lineage:

- **[`sovthpaw/omnistep-12a3b`](https://huggingface.co/sovthpaw/omnistep-12a3b)**
  — 12B total / 3B active, multimodal, 4 GGUFs + 4 safetensors
- **[`sovthpaw/Omni-Senter-3B`](https://huggingface.co/sovthpaw/Omni-Senter-3B)**
  — 3B early Senter, LoRA + GGUF
- **[`sovthpaw/OmniSenter-Base-16B`](https://huggingface.co/sovthpaw/OmniSenter-Base-16B)**
  — 16B base, multimodal (Qwen3-8B + Cosmos3-Nano Darwin merge)

The new architecture (Senter Ohm 32A8B, OmniSenter 12B, OmniSenterStep)
will **replace** these as it ships. They're foundation, not destination.

## The posts

### 🏛️ Foundations (read first)

| Post | What's in it | Read time |
|---|---|---|
| **[`the-omni-family.md`](./the-omni-family.md)** | The naming convention: Omni (multimodal), Senter (agentic), Ohm (self-evolving), Senter Ohm (the flagship). With a family tree. | 5 min |
| **[`the-omnimodal-fusion.md`](./the-omnimodal-fusion.md)** | The three-component fusion that powers every Omni model: Cosmos × ACE-Step × Nemotron ASR. | 8 min |
| **[`the-omnistep-multimodal.md`](./the-omnistep-multimodal.md)** | The destination unified model — a single Darwin-merged text backbone with all modality heads. The current transitional `sovthpaw/omnistep-12a3b` is the proof-of-concept. | 7 min |

### 🚀 The Flagship (the build)

| Post | What's in it | Read time |
|---|---|---|
| **[`senter-ohm-flagship.md`](./senter-ohm-flagship.md)** | The flagship post. Senter Ohm = ~32B-total / 8B-active MoE with the Ohm self-evolution engine bundled. The design doc. | 15 min |
| **[`senter-ohm-32a8b-math.md`](./senter-ohm-32a8b-math.md)** | The math: per-layer params, active vs total, 4-bit vs bf16 disk, VRAM at inference, VRAM at training. | 8 min |
| **[`the-5-stage-pipeline.md`](./the-5-stage-pipeline.md)** | The 5-stage build sequence: SFT → evolutionary merge → sparse upcycle → 256K YaRN → plugin+notebook+Ohm wiring. With wall times. | 10 min |
| **[`sparse-upcycling-deep-dive.md`](./sparse-upcycling-deep-dive.md)** | Stage 3 deep dive: turning an 8B dense into a 32B MoE with 8B active. Math, script, design choices, wild cards. | 12 min |

### 🧠 The Concepts (what makes it special)

| Post | What's in it | Read time |
|---|---|---|
| **[`the-synthesia-layer.md`](./the-synthesia-layer.md)** | The cross-modal memory indexer. Joint `(text, audio, image)` embeddings, 10 concrete benefits, the data it needs. | 10 min |
| **[`the-ohm-runtime.md`](./the-ohm-runtime.md)** | The self-evolving model file. The `.ohm` bundle format, the background CMA-ES loop, the safety properties. | 12 min |
| **[`the-omnisenter-architecture.md`](./the-omnisenter-architecture.md)** | The full system architecture: Layer 0 stream I/O, Layer 1 MoE, Layer 1.5 Synthesia, Layer 2 plugins, Layer 3 Hermes, Layer 5.5 Ohm. | 15 min |

### 🔌 The Integration (how it ships)

| Post | What's in it | Read time |
|---|---|---|
| **[`senter-as-hermes-auxiliary.md`](./senter-as-hermes-auxiliary.md)** | How Senter talks to Hermes Agent. The notebook-as-API pattern, the escalation rules, the cost model. | 12 min |
| **[`the-notebook-schema.md`](./the-notebook-schema.md)** | The notebook spec. YAML session files, cross-modal moments, the compaction policy, the privacy model. | 10 min |

### 🧬 The Research (extending the approach)

| Post | What's in it | Read time |
|---|---|---|
| **[`generative-darwin-evolution.md`](./generative-darwin-evolution.md)** | Extending Darwin Family weight-space merging to DiT/audio/video. The research direction. | 10 min |

## The reading order

For a cold reader:

1. **[`the-omni-family.md`](./the-omni-family.md)** — start here
2. **[`the-omnimodal-fusion.md`](./the-omnimodal-fusion.md)** — what's
   the foundation
3. **[`senter-ohm-flagship.md`](./senter-ohm-flagship.md)** — the
   flagship overview
4. **[`senter-ohm-32a8b-math.md`](./senter-ohm-32a8b-math.md)** — the
   sizing math
5. **[`the-5-stage-pipeline.md`](./the-5-stage-pipeline.md)** — how to
   build it
6. **[`the-synthesia-layer.md`](./the-synthesia-layer.md)** — the
   cross-modal memory layer
7. **[`the-ohm-runtime.md`](./the-ohm-runtime.md)** — the self-evolution
   engine
8. **[`the-omnisenter-architecture.md`](./the-omnisenter-architecture.md)**
   — the system overview
9. **[`senter-as-hermes-auxiliary.md`](./senter-as-hermes-auxiliary.md)**
   — the integration
10. **[`the-notebook-schema.md`](./the-notebook-schema.md)** — the
    notebook spec
11. **[`sparse-upcycling-deep-dive.md`](./sparse-upcycling-deep-dive.md)**
    — the Stage 3 deep dive
12. **[`the-omnistep-multimodal.md`](./the-omnistep-multimodal.md)** —
    the destination unified model
13. **[`generative-darwin-evolution.md`](./generative-darwin-evolution.md)**
    — the research direction

## HuggingFace models

| Model | Size | Status | What it is |
|---|---|---|---|
| [`sovthpaw/omnistep-12a3b`](https://huggingface.co/sovthpaw/omnistep-12a3b) | 12B total / 3B active | ✅ published (transitional) | OmniStep baseline. Multimodal any-to-any. 4 GGUFs + 4 safetensors. |
| [`sovthpaw/Omni-Senter-3B`](https://huggingface.co/sovthpaw/Omni-Senter-3B) | 3B | ✅ published (transitional) | Early Senter. LoRA + GGUF. Predecessor of OmniSenter 12B. |
| [`sovthpaw/OmniSenter-Base-16B`](https://huggingface.co/sovthpaw/OmniSenter-Base-16B) | 16B | ✅ published (transitional) | Omni base. Qwen3-8B + Cosmos3-Nano Darwin merge. Predecessor of OmniSenter 12B + Senter Ohm. |
| `sovthpaw/omnisenter-12b` | ~12B | ⏳ planned | The new OmniSenter 12B (small function calling + omnimodal fusion). |
| `sovthpaw/senter-ohm-32a8b` | ~32B total / 8B active | ⏳ planned | The new Senter Ohm flagship MoE. |

## GitHub repos (`SouthpawIN/`)

| Repo | Role |
|---|---|
| [`evolutionary-training`](https://github.com/SouthpawIN/evolutionary-training) | Main repo. Training scripts, Ohm runtime, this blog. |
| [`evolutionary-model-merging`](https://github.com/SouthpawIN/evolutionary-model-merging) | Darwin Family. CMA-ES + paper-exact merge. The merge formula that powers everything. |
| [`multimodal-expansion`](https://github.com/SouthpawIN/multimodal-expansion) | REAP + EvoMoE + `sparse_upcycle.py` for Stage 3. |
| [`omnistep-fusion`](https://github.com/SouthpawIN/omnistep-fusion) | Cosmos × ACE-Step multimodal merge. |
| [`evolutionary-radio`](https://github.com/SouthpawIN/evolutionary-radio) | The OmniStep-brained music radio. A Stage 5 consumer. |
| [`hermes-agent`](https://github.com/SouthpawIN/hermes-agent) | The smart agent Senter is auxiliary to. |
| `senter`, `nous-girl`, `chizul` | Hermes Agent profiles. |

## Cross-reference cheat sheet

Every blog post links to:
- The Omni Family post (naming source of truth)
- The relevant sibling posts in the catalog
- The relevant HF models
- The relevant GitHub repos
- The relevant wiki concepts (`~/wiki/concepts/`)

If you find a blog post that doesn't link to the Omni Family post or
its siblings, that's a bug — please report.

## TOWARDS SELF-IMPROVEMENT

— Chris (via Nous Girl), 2026-06-07
