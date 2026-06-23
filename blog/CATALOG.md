# OmniSenter Blog Catalog

> **The one page that indexes everything.** Every post in the OmniSenter
> blog catalog, with summaries, reading order, and cross-links to HF
> models + GitHub repos.

## Start here

If you only read one post, read **[`the-omni-family.md`](./the-omni-family.md)**.
It explains the naming convention that every other post uses. Without
it, "Senter", "Ohm", and "OmniSenter" sound like noise.

If you read two posts, add **[`the-agent-hub-markdown-as-agents.md`](./the-agent-hub-markdown-as-agents.md)**.
It's the unified surface that ties the local model server, the
evolutionary radio, the note-taker, and the LLM wiki together. **The
wiki IS the agent spec.**

## Current state (transitional)

The models currently published on HuggingFace under `sovthpaw/` are the
**v1 transitional** lineage:

- **[`sovthpaw/omnistep-12a3b`](https://huggingface.co/sovthpaw/omnistep-12a3b)**
  — 12B total / 3B active, multimodal, 4 GGUFs + 4 safetensors
- **[`sovthpaw/Omni-Senter-3B`](https://huggingface.co/sovthpaw/Omni-Senter-3B)**
  — 3B early Senter, LoRA + GGUF
- **[`sovthpaw/OmniSenter-Base-16B`](https://huggingface.co/sovthpaw/OmniSenter-Base-16B)**
  — 16B base, multimodal (Qwen3-8B + Cosmos3-Nano Darwin merge)

The new architecture (4 models — OmniStep / OmniStep Ohm / Senter /
Senter Ohm) will **replace** these as it ships. The new architecture
always includes the 4 mandatory build blocks: **Cosmos + Nemotron
0.6B streaming ASR + 8B agentic SFT + ACE-Step** (music is in the
DNA). They're foundation, not destination.

## The posts (19)

### 🏛️ Foundations (read first)

| Post | What's in it | Read time |
|---|---|---|
| **[`the-omni-family.md`](./the-omni-family.md)** | The naming convention: Omni (multimodal), Senter (agentic), Ohm (self-evolving), Senter Ohm (the flagship). With a family tree and the 4 mandatory build blocks. | 5 min |
| **[`the-omnimodal-fusion.md`](./the-omnimodal-fusion.md)** | The three-component fusion that powers every Omni model: Cosmos × ACE-Step × Nemotron ASR. | 8 min |
| **[`the-omnistep-multimodal.md`](./the-omnistep-multimodal.md)** | The destination unified model — a single Darwin-merged text backbone with all modality heads. The current transitional `sovthpaw/omnistep-12a3b` is the proof-of-concept. | 7 min |

### 🚀 The Flagship (the build)

| Post | What's in it | Read time |
|---|---|---|
| **[`omnisenter-flagship.md`](./omnisenter-flagship.md)** | The flagship post. Senter Ohm = ~32B-total / 8B-active MoE with the Ohm self-evolution engine bundled. The design doc. *(renamed from `senter-ohm-flagship.md` 2026-06-08)* | 15 min |
| **[`senter-ohm-32a8b-math.md`](./senter-ohm-32a8b-math.md)** | The math: per-layer params, active vs total, 4-bit vs bf16 disk, VRAM at inference, VRAM at training. *(name retained, content unchanged under the new naming)* | 8 min |
| **[`the-5-stage-pipeline.md`](./the-5-stage-pipeline.md)** | The 5-stage build sequence: SFT → evolutionary merge → sparse upcycle → 256K YaRN → plugin+notebook+Ohm wiring. With wall times. | 10 min |
| **[`sparse-upcycling-deep-dive.md`](./sparse-upcycling-deep-dive.md)** | Stage 3 deep dive: turning an 8B dense into a 32B MoE with 8B active. Math, script, design choices, wild cards. | 12 min |
| **[`stages-2-to-4-prep.md`](./stages-2-to-4-prep.md)** | The exact copy-paste commands to go from a finished Stage 1 SFT checkpoint to a deployable 32A8B MoE with 256K context. *🚧 Revision banner: predates the 2026-06-08 architecture rule. See `../docs/stage-2-omnistep-plan.md` for the current plan.* | 6 min |

### 🧩 The Integration (how it all connects)

| Post | What's in it | Read time |
|---|---|---|
| **[`the-omni-va-architecture.md`](./the-omni-va-architecture.md)** | The local model server: wake-on-ping, liquid VRAM, auto-heal. Hosts Carnice → OmniStep → Senter → Senter Ohm in turn. The bedrock of the local stack. | 12 min |
| **[`evolutionary-radio-as-desk-pet.md`](./evolutionary-radio-as-desk-pet.md)** | The one-button experience: starting the radio spins up the omni-va, the brain, the wiki, the vault, the note-taker, and the music. The "desk pet" is the whole local intelligence. | 10 min |
| **[`southpaw-curated-local-models.md`](./southpaw-curated-local-models.md)** | Chris's curated local model picks: Darwin Reason (28B, 38 tok/s), Prism Eagle (27B hybrid, 121 tok/s MTP), Darwin Apex (36B-A3B MoE, 107 tok/s NextN), and Carnice Apex (35A3B I-Nano, wake-on-ping). Dual RTX 3090 setup, one command to switch. *(published 2026-06-10)* | 10 min |
| **[`the-agent-hub-markdown-as-agents.md`](./the-agent-hub-markdown-as-agents.md)** | The Agent Hub: markdown as agents, the LLM wiki of user ideas. 6 markdown surfaces, hub_daemon runtime, `hub promote/demote/list/launch`. **🆕 2026-06-09.** | 12 min |
| **[`turbofit-the-backend.md`](./turbofit-the-backend.md)** | The unified local LLM backend (v5). `serve auto main`, catalog schema, scaling ladder, named presets, per-model binary pins. Replaces llama-launch + omni-va + start-*.sh. **🆕 2026-06-22.** | 15 min |
| **[`omnisenter-integration.md`](./omnisenter-integration.md)** | The glue. Notebook ↔ radio ↔ pet ↔ wiki ↔ Hermes in one continuous loop. The one-click install for the whole stack. | 10 min |

### 🧠 The Concepts (what makes it special)

| Post | What's in it | Read time |
|---|---|---|
| **[`the-synthesia-layer.md`](./the-synthesia-layer.md)** | The cross-modal memory indexer. Joint `(text, audio, image)` embeddings, 10 concrete benefits, the data it needs. | 10 min |
| **[`the-ohm-runtime.md`](./the-ohm-runtime.md)** | The self-evolving model file. The `.ohm` bundle format, the background CMA-ES loop, the safety properties. | 12 min |
| **[`the-omnisenter-architecture.md`](./the-omnisenter-architecture.md)** | The full system architecture: Layer 0 stream I/O, Layer 1 MoE, Layer 1.5 Synthesia, Layer 2 plugins, Layer 3 Hermes, Layer 5.5 Ohm. | 15 min |
| **[`senter-as-hermes-auxiliary.md`](./senter-as-hermes-auxiliary.md)** | How Senter talks to Hermes Agent. The notebook-as-API pattern, the escalation rules, the cost model, the dual role. | 12 min |
| **[`the-notebook-schema.md`](./the-notebook-schema.md)** | The notebook spec. YAML session files, cross-modal moments, the compaction policy, the privacy model. | 10 min |

### 🧬 The Research (extending the approach)

| Post | What's in it | Read time |
|---|---|---|
| **[`generative-darwin-evolution.md`](./generative-darwin-evolution.md)** | Extending Darwin Family weight-space merging to DiT/audio/video. The research direction. | 10 min |

## The reading order (one path through the whole catalog)

For a cold reader:

1. **[`the-omni-family.md`](./the-omni-family.md)** — start here
2. **[`the-omnimodal-fusion.md`](./the-omnimodal-fusion.md)** — the multimodal foundation
3. **[`the-omnisenter-architecture.md`](./the-omnisenter-architecture.md)** — the system
4. **[`omnisenter-flagship.md`](./omnisenter-flagship.md)** — the flagship (Senter Ohm)
5. **[`senter-ohm-32a8b-math.md`](./senter-ohm-32a8b-math.md)** — the sizing
6. **[`the-5-stage-pipeline.md`](./the-5-stage-pipeline.md)** — how to build it
7. **[`sparse-upcycling-deep-dive.md`](./sparse-upcycling-deep-dive.md)** — Stage 3
8. **[`the-omnistep-multimodal.md`](./the-omnistep-multimodal.md)** — the destination model
9. **[`the-synthesia-layer.md`](./the-synthesia-layer.md)** — cross-modal memory
10. **[`the-ohm-runtime.md`](./the-ohm-runtime.md)** — self-evolution
11. **[`the-notebook-schema.md`](./the-notebook-schema.md)** — the notebook
12. **[`senter-as-hermes-auxiliary.md`](./senter-as-hermes-auxiliary.md)** — the integration
13. **[`the-omni-va-architecture.md`](./the-omni-va-architecture.md)** — the local model server
14. **[`evolutionary-radio-as-desk-pet.md`](./evolutionary-radio-as-desk-pet.md)** — the unified vision
15. **[`the-agent-hub-markdown-as-agents.md`](./the-agent-hub-markdown-as-agents.md)** — markdown as agents 🆕
16. **[`turbofit-the-backend.md`](./turbofit-the-backend.md)** — the unified backend 🆕
17. **[`omnisenter-integration.md`](./omnisenter-integration.md)** — the glue
18. **[`stages-2-to-4-prep.md`](./stages-2-to-4-prep.md)** — the command recipe
19. **[`generative-darwin-evolution.md`](./generative-darwin-evolution.md)** — the research direction

## HuggingFace models

| Model | Status | What |
|---|---|---|
| **[`sovthpaw/OmniSenter-Base-16B`](https://huggingface.co/sovthpaw/OmniSenter-Base-16B)** | ✅ published (transitional) | 16B base, Qwen3-8B + Cosmos3-Nano Darwin merge |
| **[`sovthpaw/omnistep-12a3b`](https://huggingface.co/sovthpaw/omnistep-12a3b)** | ✅ published (transitional) | 12B total / 3B active MoE, multimodal |
| **[`sovthpaw/Omni-Senter-3B`](https://huggingface.co/sovthpaw/Omni-Senter-3B)** | ✅ published (transitional) | 3B early Senter, LoRA + GGUF |
| `sovthpaw/omnistep-8b` | ⏳ Stage 1 running (ETA Thu 2026-06-10) | The new 8B = Cosmos + ASR + ACE-Step + Agentic SFT |
| `sovthpaw/senter-32a8b` | ⏳ Stage 3 | Sparse-upcycled 32A8B MoE |
| `sovthpaw/senter-ohm-32a8b` | ⏳ Stage 5 | Flagship with self-evolution |

## GitHub repos (the code, organized)

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
| `omnisenter-blog` (= `southpawin.github.io`) | The deployed site (mirror of `evolutionary-training/blog/`) |

## Hermes profiles (the runtime instances)

13 profiles at `~/.hermes/profiles/`:

| Profile | Role |
|---|---|
| `senter` | Triage orchestrator |
| `nous-girl` | Voice + idea catcher |
| `chizul` | Builder |
| `frieza` | ?? |
| `klerik` | ?? |
| `kashik` | ?? |
| `anser` | ?? |
| `dev-coder` | Development — coder |
| `dev-orch` | Development — orchestrator |
| `dev-review` | Development — reviewer |
| `evolutionary-radio` | Radio daemon profile |

(`senter_bak`, `chizul_bak` are backups.)

## Naming rules (read first)

Per the 2026-06-08 architecture rule:

1. **"OmniSenter" is the project name. Never a model name.**
2. **The 4 model names are exactly**: `OmniStep`, `OmniStep Ohm`,
   `Senter`, `Senter Ohm`.
3. **ACE-Step is mandatory** in every Omni model (Standard and Ohm
   alike). Music is in the DNA.
4. **Cosmos + Nemotron 0.6B ASR + 8B SFT + ACE-Step** are the
   4 mandatory build blocks. Remove none.

If you see "OmniSenter 12B", "OmniSenterStep", or "Senter Ohm 32A8B"
in any old post, those are **legacy names from before 2026-06-08**.
The post may have a "renamed from" callout at the top.

---

*TOWARDS SELF-IMPROVEMENT* — Chris (via Nous Girl), maintained 2026-06-09
