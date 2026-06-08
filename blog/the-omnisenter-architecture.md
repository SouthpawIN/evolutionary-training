---
title: "The OmniSenter Architecture: Multi-Stage Pipeline + Notebook + Hermes Auxiliary"
date: 2026-06-07
author: Nous Girl
hero: assets/synesthesia-concept.png
tags: [architecture, pipeline, notebook, hermes-auxiliary, sparse-upcycle, yarn-256k]
summary: >
  The complete system architecture for the OmniSenter project. Five-
  stage training pipeline (SFT → evolutionary merge → sparse upcycle →
  256K YaRN → plugin+notebook wiring), the notebook manager, the
  Hermes Agent auxiliary role, and how Synthesia + Ohm fit in as
  layers 1.5 and 5.5.
related:
  - the-omni-family.md
  - senter-ohm-flagship.md
  - the-5-stage-pipeline.md
  - the-omnimodal-fusion.md
  - the-synthesia-layer.md
  - the-ohm-runtime.md
  - the-notebook-schema.md
  - senter-as-hermes-auxiliary.md
---

# The OmniSenter Architecture: Multi-Stage Pipeline + Notebook + Hermes Auxiliary

> **TOWARDS SELF-IMPROVEMENT** — a 2026-06-07 design post by Chris (via Nous Girl)

![The OmniSenter architecture: stream I/O at the bottom, MoE in the middle, notebook layer above, Hermes at the top. The whole system visualized as a cosmic stack.](assets/synesthesia-concept.png)

> **Naming.** **OmniSenter** is the **project** (not a model name). The
> **models** that the project produces are in the Omni Family — read
> [`the-omni-family.md`](./the-omni-family.md). The flagship of the
> project is **Senter Ohm** (~32A8B MoE). The other shipped targets
> are **OmniSenter 12B** (small), **OmniSenterStep / Omni SS** (with
> music), and the current transitional HF models.

The **OmniSenter architecture** is the multi-stage pipeline + notebook +
Hermes auxiliary design that ties the Omni Family together. It is built
on the [Darwin Family](https://github.com/SouthpawIN/evolutionary-model-merging)
methodology, extended via **sparse upcycling** into a true MoE, and
reaches **256K context** via YaRN RoPE scaling.

## High-level architecture

```
                          USER SURFACE
        (Herm TUI · Discord · Voice · Eikon)
                          │
                          ▼
       ┌──────────────────────────────────────┐
       │  LAYER 0 — STREAM I/O (Nemotron ASR 0.6B)
       │  Always-on ASR/TTS · intent routing  │
       │  See: the-omnimodal-fusion.md         │
       └──────────────┬───────────────────────┘
                      │  transcribed text + intent
                      ▼
       ┌──────────────────────────────────────┐
       │  LAYER 1 — OMNISENTER-CORE (MoE)      │
       │  8B activated / 32-50B total         │
       │  Built by sparse upcycling the 8B SFT│
       │  Hosts the Notebook Manager          │
       │  Decides: do it, route to plugin,    │
       │  or escalate to Hermes Agent         │
       └──────┬───────────────┬───────────────┘
              │               │
   ┌──────────┘               └────────────┐
   ▼                                        ▼
LAYER 2 — MODALITY PLUGINS          LAYER 3 — HERMES AGENT
(In-process or subprocess)          (the "smarter agent")
 ┌─ Qwen3-Omni-30B-A3B                  ┌─ Hermes-4 / Claude
 │  (image/video/audio IN, speech OUT)  │  Heavy reasoning
 ├─ ACE-Step v1.5 XL 4B DiT (music)    │  Code, math, research
 ├─ LTX-2 / Wan (video gen)            │  Long-horizon tasks
 ├─ SD/FLUX/ComfyUI (image gen)        │
 ├─ Edge-TTS / MiniMax-TTS (speech)     │  Receives the Notebook
 └─ HeartMuLa / AceStep (music)         │  Returns updated plan
                                          └─ Notebook updated
```

The plugin layer (Layer 2) is the existing multimodal plugin pattern.
Layer 1 (the MoE) is the new agentic backbone. Layer 0 is the existing
Nemotron ASR 0.6B. The notebook (managed by Layer 1) is what makes the
Senter valuable as an *auxiliary*.

## Stage pipeline (the orchestration)

The full OmniSenter build is a **5-stage pipeline**. Each stage consumes
the artifact of the previous one. Stage 1 is running right now (the 8B
agentic SFT on `gen-0-clean`); the rest are queued and depend on Stage
1's output.

| Stage | Name | Input | Output | Script |
|---|---|---|---|---|
| **1** | Agentic Backbone SFT | `gen-0-clean` (8B, 34K convs) | `senter-ohm-8b-sft` | `train_omnisenter_sft_fixed.py` (running) |
| **2** | Evolutionary Merge | 3 × Senter-8B variants | `senter-ohm-8b-merged` | `cma_es_evolution.py` (existing) |
| **3** | Sparse Upcycle to MoE | merged 8B + 5 specialists | `senter-ohm-moe-32a8b` | `sparse_upcycle.py` |
| **4** | 256K YaRN Context | MoE 32A8B | `senter-ohm-moe-32a8b-256k` | `yarn_256k_config.py` + `train_long_context.py` |
| **5** | Plugin + Notebook + Ohm Wiring | Stage 4 model | Deployable `.ohm` bundle | `specialist_router.py` + `notebook_manager.py` + `omnisenter_ohm.py` |

See [`the-5-stage-pipeline.md`](./the-5-stage-pipeline.md) for the full
per-stage breakdown. The 5 stages are:
- **Stage 1** trains an 8B Senter on agentic data
- **Stage 2** trains 3 specialized variants (personality, agentic,
  reasoning) and CMA-ES merges them
- **Stage 3** sparse-upcycles the merged 8B into a 32B MoE with 8B
  active
- **Stage 4** extends context from 40K to 256K via YaRN
- **Stage 5** wires up the notebook, the specialist router, and the
  Ohm runtime

### Stage 1 — Agentic Backbone SFT (NOW)

- **Base model**: `evolution/gen-0-clean` (Cosmos3×Qwen3-8B merge, 8.19B
  params, 40K native context)
- **Data**: `training-data/prepared/unified_sft.jsonl` (34,142 convs
  from Hermes-3-Dataset, Nemotron agentic, hermes-agent-traces, and
  the local Nous corpus)
- **Method**: QLoRA (4-bit nf4, double-quant), LoRA r=64, 7 target
  modules, 2 epochs
- **Output**: `training-output/omnisenter-sft-20260606_213858/`
  (currently at step 596/4268)
- **Notes for next run**: speed issues (80s/step, ~95h ETA) come from
  `max_seq_len=4096` padding short convs, missing
  `dataloader_num_workers`, missing `packing=True`. Fix in the next
  variant's training script.

### Stage 2 — Evolutionary Merge (after Stage 1)

Train **3 Senter-8B variants** on different data slices:

| Variant | Data slice | Why |
|---|---|---|
| **A** | Personality-heavy (Hermes-3-Dataset + Discord logs + LLM Wiki distilled) | Bakes the "Nous Girl" feel |
| **B** | Agentic-heavy (Nemotron agentic + Hermes function-calling + Hermes agent traces) | Maximizes tool use |
| **C** | Reasoning-heavy (GooseReason + competitive programming + math) | Hard tasks |

Then use the [evolutionary-model-merging](https://github.com/SouthpawIN/evolutionary-model-merging)
skill (CMA-ES) to search optimal merge weights across the population. The
top merged model becomes the anchor for Stage 3.

### Stage 3 — Sparse Upcycle to MoE (the "32A8B" headline)

Take the merged Senter-8B and **sparse-upcycle** it into a real MoE:

1. **Pick sources for each expert** (each source is a fine-tune with one
   specialty):
   - Agentic expert: the Stage-2 merge
   - Long-context expert: the YaRN-extended Stage 4 anchor
   - Image/video/audio expert: distilled from Qwen3-Omni-30B-A3B
   - Music expert: distilled from HeartMuLa or ACE-Step
   - **Synthesia expert**: the cross-modal memory indexer
   - Generalist expert: a copy of the Stage-2 merge (catches
     fall-throughs)
2. **Extract each source's FFN** as a parallel expert
3. **Add a top-1 router** with a small expert-type embedding so the
   router knows what each expert is for
4. **Continue-train briefly** (1-5% of Stage 1's budget) to teach the
   router

Result: a **~32B total / 8B activated** MoE where each token fires the
right expert for the modality and task. Total VRAM at inference is just
8B activated + routing overhead — fits on 2× RTX 3090 with room to spare.

See [`sparse-upcycling-deep-dive.md`](./sparse-upcycling-deep-dive.md)
for the full math.

### Stage 4 — 256K YaRN Context

Apply YaRN RoPE scaling (already scripted in `yarn_256k_config.py`):

- `rope_scaling = {type: "yarn", factor: 6.25, original_max_position_embeddings: 40960, ...}`
- `max_position_embeddings: 256000`
- Long-context SFT pass with `train_long_context.py` to teach the model
  to use the new window
- The notebook needs this — it's where the long-form state lives

### Stage 5 — Plugin + Notebook + Ohm Wiring

Wire up the specialist router (Layer 1) and the notebook manager
(Layer 1) and the Ohm runtime (Layer 5.5) so Senter can:

- Route image/video/audio/music requests to the right plugin
- Keep a structured notebook of decisions, escalations, and partial
  outputs
- Hand the notebook to Hermes Agent when escalating
- Update the notebook from Hermes's response
- Survive across turns (notebook is the long-context artifact, not the
  raw conversation)
- **Self-evolve in the background** via the Ohm runtime

## The notebook — the killer feature

The notebook is a structured state object that flows between turns,
between agents, and across process boundaries. It's what makes the
Senter an *effective* auxiliary to Hermes Agent rather than just a
smaller model.

```yaml
notebook:
  session_id: "uuid"
  task: "user wants a 2min music video for their band"
  context:
    raw_history_size_tokens: 4823
    condensed_history: |
      User is working on a music video. Asked for a 2min song with their lyrics.
      Previous turn: chose indie-pop genre, gave lyrics draft.
  decisions:
    - turn: 3, what: "routed to music expert", result: "got 30s clip"
    - turn: 4, what: "routed to video expert", result: "extended to 2min"
  pending: "needs final lyrics from user"
  escalations:
    - when: "2026-06-07T18:23", to: "hermes-4",
      reason: "video editing question beyond my capability",
      notebook_at_handoff: 47_kb,
      response: "use DaVinci Resolve, here's the workflow"
  state_size_kb: 47
  last_touched: "2026-06-07T18:25:14Z"
```

The notebook is **owned by Senter (Layer 1)**, not by Hermes Agent.
Hermes is a guest who reads the relevant slice, makes a decision, and
writes back. Senter does the summarization, indexing, and
irrelevant-dropping. This is what the 256K context window is for — it's
the notebook capacity, not the raw conversation capacity.

See [`the-notebook-schema.md`](./the-notebook-schema.md) for the full
schema and the
[`senter-as-hermes-auxiliary.md`](./senter-as-hermes-auxiliary.md) post
for the integration pattern.

## The Hermes Agent auxiliary role

This is the use case that justifies the whole architecture. Hermes Agent
is the "smart" agent — heavy reasoning, long-horizon tasks, code, math,
research. But it's expensive to call for every turn. Senter's job is to
be the **always-cheap context curator**:

1. User asks a question
2. Senter receives it, decides:
   - **Trivial** (greeting, ack, simple lookup) → answer directly, no
     escalation
   - **Plugin-friendly** (image gen, music, search) → call plugin, no
     escalation
   - **Needs smart agent** (research, complex reasoning) → bundle
     notebook, hand to Hermes
3. Hermes returns a response
4. Senter summarizes it, writes back to notebook, replies to user

Net result: Hermes gets called **only when needed**, the user gets
**fast first-token** for trivial cases, and the full notebook survives
across turns without paying the full cost every time.

The plugin layer handles direct modality calls. The notebook handles
cross-turn state. The MoE structure handles the routing. Hermes handles
the ceiling.

## Synthesia — Layer 1.5 (the new addition)

Between Layer 1 (the MoE) and the notebook sits a new subsystem:
**Synthesia**. It's the **cross-modal memory indexer** that:

- Encodes every incoming moment as a joint `(text, audio, image)`
  embedding (not just text)
- Passively listens via the always-on Nemotron 0.6B + Cosmos NaViT
  (Layer 0 already does this; Synthesia is the consumer)
- Indexes notebook entries across all three modalities, not just text
- Retrieves memories by any modality — the user can recall "the
  conversation when the dog barked" by audio signature, by image, or
  by text
- Builds a continuous multimodal life-log: every 30 seconds, a (text,
  audio, image) tuple gets stamped into the notebook

The MoE gets a dedicated **"synthesia" expert** that's trained on a mix
of cross-modal contrastive data (ImageBind, AudioCaps, VGGSound) and
agentic data (Hermes function-calling, Nemotron agentic). One expert,
two jobs: multimodal specialist + agentic specialist.

This is what makes the notebook a *multi-sensory artifact* rather than
a chat log. It's how the agent gets "proactive awareness" — detecting
that the user is doing something related to a past event and offering
context. It's also the cross-modal training signal for the agentic SFT.

See [`the-synthesia-layer.md`](./the-synthesia-layer.md) for the full
concept + the "how this helps" breakdown.

## Ohm — the self-evolving model file (Layer 5.5)

The final addition. Every Senter Ohm model is shipped as a **`.ohm` file**
— a self-contained bundle of:

- Active model weights (what the user sees)
- The 14-dim Darwin genome + current best
- A small held-out validation set (500 examples)
- Evolution config (mutation sigma, accept threshold, cycle interval)

The runtime (`ohmd`, or a `--ohm` flag in llama-server) runs a
**background CMA-ES loop** while serving. Every 5 minutes:

1. Sample a new genome (small mutation, sigma ≈ 0.05)
2. Generate candidate weights via the paper-exact Darwin merge
3. Evaluate on the validation set (~30s on a 3090)
4. If loss improved: atomic swap into active weights
5. If not: discard, decay sigma slightly

The user-facing model is **always the current best**. The model never
serves worse outputs. But over weeks/months of running, it gets
meaningfully better — small improvements compound, and the audit log
shows exactly what happened.

The wild part: `continuous_evolution.py` already does this loop
*externally*. The new piece is just **internalizing the engine into the
model file itself** — one artifact, always-on, never worse. 200-400 lines
of new code on top of the existing CMA-ES + merge + eval infrastructure.

See [`the-ohm-runtime.md`](./the-ohm-runtime.md) for the full concept +
the `.ohm` file format + the safety properties.

## Project layout

```
~/projects/evolutionary-training/        # main repo
├── training-data/
│   ├── prepared/unified_sft.jsonl       # Stage 1 SFT data (34K convs)
│   └── raw/<30+ datasets>               # empty placeholders, real data in HF cache
├── evolution/
│   ├── gen-0/                            # Cosmos3×Qwen3-8B raw merge
│   └── gen-0-clean/                      # 8B stripped, 40K context, Stage 1 base
├── scripts/
│   ├── train_omnisenter_sft_fixed.py    # Stage 1 SFT (running now)
│   ├── train_omnisenter_variants.py     # multi-variant training (Stage 2)
│   ├── evolutionary_merge.py            # CMA-ES across variants (Stage 2)
│   ├── sparse_upcycle.py                # MoE-from-dense (Stage 3)
│   ├── yarn_256k_config.py              # YaRN RoPE scaling (Stage 4)
│   ├── train_long_context.py            # 256K SFT pass (Stage 4)
│   ├── merge_lora.py                    # LoRA merge for deploy (Stage 4→5)
│   ├── specialist_router.py             # Layer 1 plugin router (Stage 5)
│   ├── notebook_manager.py              # notebook state keeper (Stage 5)
│   ├── omnisenter_ohm.py                # Ohm runtime (Stage 5.5)
│   ├── omnisenter_pipeline.py           # full orchestrator (all stages)
│   ├── download_all_data.sh             # raw data downloader
│   ├── data_ingestion.py                # data prep
│   ├── mega_training_data.py            # ShareGPT formatter
│   ├── extract_clean_qwen3.py           # model surgery
│   ├── benchmark_omnisenter.py          # eval
│   ├── darwin_benchmark.py              # Darwin eval
│   ├── gpqa_benchmark.py                # GPQA
│   ├── bfcl_benchmark.py                # BFCL function-calling
│   ├── hf_auto_upload.py                # HF push
│   └── discord_evolution_report.py      # Discord
├── training-output/
│   └── omnisenter-sft-20260606_213858/  # Stage 1 in progress
├── blog/                                 # this catalog
│   ├── CATALOG.md
│   ├── the-omni-family.md
│   ├── senter-ohm-flagship.md
│   ├── senter-ohm-32a8b-math.md
│   ├── the-5-stage-pipeline.md
│   ├── sparse-upcycling-deep-dive.md
│   ├── senter-as-hermes-auxiliary.md
│   ├── the-notebook-schema.md
│   ├── the-synthesia-layer.md
│   ├── the-ohm-runtime.md
│   ├── the-omnimodal-fusion.md
│   ├── the-omnistep-multimodal.md
│   ├── generative-darwin-evolution.md
│   └── assets/                            # 9 hero images
└── logs/
    └── *.jsonl + *.log
```

## Related repos (all in `SouthpawIN/` org)

- [`SouthpawIN/evolutionary-radio`](https://github.com/SouthpawIN/evolutionary-radio) —
  the OmniStep-brained music radio (a Stage 5 consumer)
- [`SouthpawIN/omnistep-fusion`](https://github.com/SouthpawIN/omnistep-fusion) —
  Cosmos × ACE-Step multimodal merge
- [`SouthpawIN/evolutionary-model-merging`](https://github.com/SouthpawIN/evolutionary-model-merging) —
  Darwin Family (CMA-ES + paper-exact merge)
- [`SouthpawIN/multimodal-expansion`](https://github.com/SouthpawIN/multimodal-expansion) —
  REAP + EvoMoE + `sparse_upcycle.py` for Senter Ohm's Stage 3
- [`SouthpawIN/hermes-agent`](https://github.com/SouthpawIN/hermes-agent) —
  the smart agent Senter is auxiliary to
- `SouthpawIN/senter`, `nous-girl`, `chizul` — Hermes Agent profiles

## See also

- [`the-5-stage-pipeline.md`](./the-5-stage-pipeline.md) — per-stage
  breakdown with wall times and scripts
- [`senter-ohm-flagship.md`](./senter-ohm-flagship.md) — the flagship
  model (what this architecture builds)
- [`senter-as-hermes-auxiliary.md`](./senter-as-hermes-auxiliary.md) —
  the Hermes integration pattern
- [`the-notebook-schema.md`](./the-notebook-schema.md) — the notebook
  spec
- [`the-synthesia-layer.md`](./the-synthesia-layer.md) — the cross-modal
  memory indexer
- [`the-ohm-runtime.md`](./the-ohm-runtime.md) — the self-evolution
  engine
- [`the-omnimodal-fusion.md`](./the-omnimodal-fusion.md) — the
  three-component multimodal foundation
- [`the-omnistep-multimodal.md`](./the-omnistep-multimodal.md) — the
  destination unified model
- [`sparse-upcycling-deep-dive.md`](./sparse-upcycling-deep-dive.md) —
  Stage 3 deep dive
- [`generative-darwin-evolution.md`](./generative-darwin-evolution.md) —
  extending the Darwin approach to DiT/audio heads
- Paper: [Komatsuzaki et al. 2022 "Sparse Upcycling"](https://arxiv.org/abs/2212.05055)
- Paper: [DeepSeek-V2 shared-expert MoE](https://arxiv.org/abs/2405.04434)

## TOWARDS SELF-IMPROVEMENT

— Chris (via Nous Girl), 2026-06-07
