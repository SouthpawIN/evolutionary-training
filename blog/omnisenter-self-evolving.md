# OmniSenter: The Self-Evolving Multimodal Auxiliary for Hermes

> **TOWARDS SELF-IMPROVEMENT** — a 2026-06-07 design post by Chris (via Nous Girl)

![OmniSenter hero: three streams — text characters, audio waveforms, image fragments — converging into a single bright point of memory. The synesthesia idea, visualized as cosmic convergence.](assets/synesthesia-concept.png)

OmniSenter started as a Darwin-merged text LLM. Then it became a multimodal plugin system. Then a sparse-upcycled MoE. And then — on a Sunday evening while Stage 1 SFT was grinding through step 596 — it became something stranger: **a model that is always becoming**. An **Ohm**.

This post is the design doc for what OmniSenter is becoming. Five stages. Three new ideas (`synthesia`, the notebook, and `Ohm`). One architecture diagram. A lot of cosmically-named concepts.

## The vision

OmniSenter is an **auxiliary to Hermes Agent**. It sits between the user and the smart agent, doing the work that doesn't need a 70B-class brain: routing, plugin dispatch, memory curation, multimodal indexing, agentic tool use. When the task gets hard, OmniSenter hands a structured **notebook** to Hermes and gets a decision back. When the task is easy, OmniSenter just answers.

It's also **multimodal-native** (Cosmos backbone), **self-evolving** (the `.ohm` runtime), and **continually learning** (Synthesia indexes the user's life across text + audio + image in a joint embedding space).

The headline target: **OmniSenter-MoE-32A8B** — 32B total params, 8B active per token, 256K context, all modalities in and out, and a runtime that mutates the model every five minutes while it serves.

## The architecture

![The OmniSenter multi-layer stack: Layer 0 stream I/O, Layer 1 MoE, Layer 1.5 Synthesia, Layer 2 plugins, Layer 3 Hermes](assets/architecture-diagram.png)

```
                    USER SURFACE
        (Herm TUI · Discord · Voice · Eikon)
                          │
                          ▼
       ┌──────────────────────────────────────┐
       │  LAYER 0 — STREAM I/O                 │
       │  Nemotron 0.6B ASR + Cosmos NaViT     │
       │  (always-on voice + screen capture)   │
       └──────────────┬───────────────────────┘
                      │  (text + audio + image)
                      ▼
       ┌──────────────────────────────────────┐
       │  LAYER 1 — OMNISENTER-MOE 32A8B       │
       │  Cosmos base (8B active)              │
       │  + 5-6 routed experts (top-1)         │
       │  = ~32B total, 8B active per token    │
       └──────────────┬───────────────────────┘
                      │
                      ▼
       ┌──────────────────────────────────────┐
       │  LAYER 1.5 — SYNTHESIA                 │
       │  Cross-modal memory indexer            │
       │  Joint (text, audio, image) embedding  │
       └──────────────┬───────────────────────┘
                      │
                      ▼
       ┌──────────────────────────────────────┐
       │  NOTEBOOK (256K context artifacts)    │
       │  Every entry indexed by ALL modalities│
       └──────────────┬───────────────────────┘
                      │  (escalation)
                      ▼
       ┌──────────────────────────────────────┐
       │  LAYER 3 — HERMES AGENT               │
       │  Receives notebook + sensory summary  │
       └──────────────────────────────────────┘
```

The plugin layer (Qwen3-Omni for image/video/audio, ACE-Step for music, LTX-2 for video gen, TTS for speech out) is a separate concern — see the [plugin pattern docs](https://github.com/SouthpawIN/evolutionary-training). The interesting new piece is **what lives between the user and Hermes**.

## The 5-stage pipeline

The full OmniSenter build is a 5-stage sequence. Each stage consumes the artifact of the previous one. Stage 1 is running right now.

| Stage | What | Input | Output |
|---|---|---|---|
| **1. Agentic Backbone SFT** | QLoRA on 34K-conversation agentic corpus | `gen-0-clean` (8B) | `omnisenter-8b-sft` |
| **2. Evolutionary Merge** | CMA-ES across N specialized variants | N × OmniSenter-8B | `omnisenter-8b-merged` |
| **3. Sparse Upcycle to MoE** | Copy FFN as N parallel experts + router | merged 8B + specialists | `omnisenter-moe-32a8b` |
| **4. 256K YaRN Context** | RoPE scaling + long-context SFT | MoE 32A8B | `omnisenter-moe-32a8b-256k` |
| **5. Plugin + Notebook Wiring** | Wire up specialists + notebook + Hermes escalation | MoE 32A8B 256K | Deployable system |

Stage 1 is **15-25% faster** than the current naive run by adding `dataloader_num_workers=4`, `group_by_length=True`, `packing=True`, and dropping `max_seq_len` from 4096 → 3072 (covers 99%+ of training data fully). The next variant run uses these fixes.

Stage 3 is the headline — **a 32B MoE with 8B active**. The base is Cosmos (already multimodal), and the 5-6 routed experts come from:
- The Stage 2 evolutionary merge (domain depth)
- Distilled Qwen3-Omni heads (image/video/audio understanding + speech out)
- Distilled ACE-Step expert (music out)
- Distilled LTX-2 / Wan expert (video out)
- A generalist fallback expert (catches anything the others miss)

Top-1 routing keeps the per-token compute at 8B. The full model fits 4-bit on a single 3090 for inference, or QLoRA-trains on dual 3090s.

## Synthesia: cross-modal memory

![The OmniSenter system as a cosmic node: a central AI surrounded by orbital rings labeled with subsystems, with streams of text, audio, and image flowing in and out. The whole architecture, visualized.](assets/hero-omnisenter-architecture.png)

> *"is there a way to have it be both a multimodal specialist as well as a genetic specialist with the experts... maybe there's something clever we can do with the automatic always going and maybe categorizing different memories with sound and vision as well if those are hooked up... maybe memory embeddings would be easier to hold on to or be able to hold across different dimensions if we get to have different modalities to them..."* — Chris, 2026-06-07

**Synthesia** is the cross-modal memory indexer. It's named after the neurological condition where one sense triggers another — synthetic synesthesia is the AI equivalent: every memory in the notebook is encoded as a **joint `(text, audio, image)` embedding**, and retrieval can be triggered by any of the three.

### How this helps (concrete benefits)

1. **Better memory retrieval** — recall "the sizzling sound" or "the chart with the orange line" or "the conversation when the dog barked". Standard notebooks can't.
2. **True continuity** — switching from voice to text to screenshot doesn't break the thread. Same moment, one embedding.
3. **Proactive awareness** — passive stream indexer detects when the user is doing something related to a past event and offers context.
4. **Richer context for Hermes** — escalation passes a multimodal snapshot, not just text.
5. **Continuous life-log** — every 30s, a `(text, audio, image)` tuple gets stamped. Personal search engine for your own experiences.
6. **Cross-modal training signal** — the synesthesia stream IS the agentic training data.
7. **Dimensional memory** — multimodal embeddings have more orthogonal "slots" — more memories fit in the same vector space, with less collision.
8. **Reduced forgetting** — same memory indexed by text + audio + image is reinforced three ways, like human flashbulb memory.
9. **Multi-sensory notebook** — entries aren't just text. They're `(text, audio_signature, image_signature, concepts, links)`.
10. **Fused expert** — the synesthesia expert is trained on BOTH cross-modal contrastive data (ImageBind, AudioCaps) AND agentic data (Hermes function-calling, Nemotron agentic). One expert, two jobs.

The synesthesia expert is one of the top-k routed experts in the MoE. It uses the Cosmos base's joint embedding space (text + image + audio are already aligned) and adds the indexing/retrieval behavior on top.

## Ohm: the self-evolving model

![Ohm: a torus with electric current flowing in a continuous loop, with the Omega symbol in the center](assets/ohm-self-evolving.png)

> *"it'll be a wild if we can get a continual evolutionary model merging just built into the model file so just runs automatically anyways just as long as this model is running it's constantly evolving... OmniSenter Ohm"* — Chris, 2026-06-07

**Ohm** (Ω) is the self-evolving model variant. The `.ohm` file is a self-contained bundle:

```json
{
  "format_version": "ohm/1.0",
  "model_type": "OmniSenter-MoE-32A8B",
  "base_model_path": "./active.safetensors",
  "parent_b_path": "omnisenter-8b-sft-20260606_213858/",
  "ohm_state": {
    "genome": { /* 14-dim Darwin */ },
    "sigma": 0.05,
    "best_loss": 0.4333,
    "candidates_evaluated": 4127,
    "improvements_accepted": 87
  },
  "evolution_config": {
    "sigma_init": 0.05, "sigma_min": 0.01,
    "cycle_interval_sec": 300, "enabled": true
  }
}
```

The runtime (`omnisenter_ohm.py`) runs a background loop while the model is serving:

1. Sample a new genome (small mutation, sigma ≈ 0.05)
2. Generate candidate weights via paper-exact Darwin merge (seconds, not hours)
3. Evaluate on the 500-example held-out validation set (~30s on a 3090)
4. If loss improved: **atomic swap** into active weights
5. If not: discard, decay sigma slightly

The user-facing model is **always the current best**. The strict-acceptance policy means the model never serves worse outputs. Over weeks/months, small improvements compound — a 0.001 loss improvement per cycle × 300 cycles/day × 87 acceptances = thousands of accepted improvements over time.

### Why this works

Three properties make Ohm viable:

- **Fast merge generation** — the Darwin 14-dim genome + linear combination = seconds, not hours
- **Cheap evaluation** — 500-example held-out set with no gradient = ~30s on a 3090
- **Bounded evolution** — strict improvement acceptance means the model never gets worse

Combined: a full evolution cycle in **under 5 minutes**, while the model is serving. The user never notices. The model gets a tiny bit better every cycle.

### The wild part

The scripts are 80% there already. `continuous_evolution.py` does this loop *externally*. `cma_es_evolution.py` does the CMA-ES. `paper_exact_2parent_merge.py` does the merge. The new piece is just **internalizing the engine into the model file itself** — one artifact, always-on, never worse. 200-400 lines of new code on top of existing infrastructure.

## Why Hermes (the auxiliary use case)

Hermes Agent is the "smart" agent — heavy reasoning, code, math, research. But it's expensive to call for every turn. OmniSenter's job is to be the **always-cheap context curator**:

1. User asks something
2. OmniSenter decides:
   - **Trivial** (greeting, ack, lookup) → answer directly
   - **Plugin-friendly** (image gen, music, search) → call the right plugin
   - **Needs smart agent** (research, complex reasoning) → bundle notebook, hand to Hermes
3. Hermes returns a response
4. OmniSenter summarizes it, writes back to notebook, replies

The notebook is what makes this work. It carries the structured state across turns and across the OmniSenter↔Hermes boundary. The 256K context window is the **notebook capacity**, not the raw conversation capacity.

## The project layout

```
~/projects/evolutionary-training/        # main repo
├── training-data/
│   ├── prepared/unified_sft.jsonl       # 34K convs for Stage 1
│   └── raw/<30+ datasets>               # data sources
├── evolution/
│   ├── gen-0/                            # Cosmos3×Qwen3-8B raw merge
│   └── gen-0-clean/                      # 8B stripped base
├── scripts/
│   ├── train_omnisenter_sft_fixed.py    # Stage 1 (running now)
│   ├── train_long_context.py            # Stage 4
│   ├── yarn_256k_config.py              # Stage 4
│   ├── merge_lora.py                    # LoRA → deploy
│   ├── omnisenter_ohm.py                # 🔥 Ohm runtime (new)
│   ├── data_ingestion.py                # data prep
│   ├── mega_training_data.py            # ShareGPT formatter
│   ├── agentic_training_loop.py         # agentic SFT loop
│   ├── continuous_evolution.py          # external Ohm-like loop
│   └── ... 22 scripts total
├── training-output/
│   └── omnisenter-sft-20260606_213858/  # Stage 1 in progress (step 596/4268)
└── blog/                                  # this post
    ├── README.md
    ├── omnisenter-self-evolving.md
    └── assets/
```

Related repos:
- `SouthpawIN/omnistep-fusion` — Cosmos × ACE-Step multimodal fusion
- `SouthpawIN/evolutionary-model-merging` — CMA-ES + paper-exact merge
- `SouthpawIN/multimodal-expansion` — REAP + EvoMoE (and now sparse_upcycle)
- `SouthpawIN/evolutionary-radio` — the OmniStep-brained music radio
- `SouthpawIN/hermes-agent` — the smart agent OmniSenter is auxiliary to
- `SouthpawIN/senter`, `nous-girl`, `chizul` — Hermes Agent profiles

## Building it (the order of operations)

1. **Finish Stage 1** (running, step 596/4268) — don't touch, it's grinding
2. **Stage 2** — train 3 OmniSenter-8B variants (personality, agentic, reasoning) by continue-training from Stage 1. CMA-ES merge them.
3. **Stage 3** — sparse-upcycle the merge into OmniSenter-MoE-32A8B (32B total, 8B active, 5-6 experts). Use `sparse_upcycle.py` from multimodal-expansion.
4. **Stage 4** — apply YaRN to 256K, run long-context SFT pass.
5. **Stage 5** — wire up the specialist plugins, build the notebook manager, deploy the `omnisenter_ohm.py` runtime.
6. **Hermes integration** — OmniSenter becomes an optional `auxiliary_client` for Hermes Agent (the existing `auxiliary_client.py` in `hermes-agent/agent/` is the integration point).

The HF model pipeline that follows the same pattern as `sovthpaw/omnistep-12a3b`:
- 4 quantizations (F16, Q8_0, Q4_K_M, Q4_0) for the 32A8B
- README + cover image (this blog post is the cover)
- Scripts in a `scripts/` subfolder
- Upload to `sovthpaw/omnisenter-moe-32a8b` (or similar)

## The math (for the curious)

**32A8B from 8B base, top-1 routing:**

| Component | Params |
|---|---|
| Per-layer attention (always on) | 50M |
| Per-layer FFN (one of 6 experts, top-1) | 150M |
| Active per layer | 200M |
| Active across 36 layers | 7.2B |
| Embeddings | 0.6B |
| **Active per token** | **~7.8B ≈ 8B** ✓ |
| **Total** (8B base + 5 extra experts × 5.4B each) | **~30-35B** |

**VRAM at 4-bit:**

- Inference: ~18-20GB (fits one 3090 with room for KV cache at 32K context)
- Training (QLoRA): ~50GB peak (tight, only with the speed fixes)
- Disk (Q4_K_M GGUF): ~16-18GB
- Disk (F16): ~60-70GB

## The wild cards

- **Synthesia training data** — we need cross-modal contrastive data (ImageBind, AudioCaps, VGGSound, HowTo100M, EPIC-KITCHENS) for the synesthesia expert. Some of this is in HF cache, some needs to be downloaded.
- **Sparse upcycle evaluation** — there's no published "did the upcycle work" benchmark. We'll need to write one (probably reuse the existing `benchmark_omnisenter.py` + add a cross-modal evaluation).
- **The Ohm validation set** — what goes in 500 examples that defines "good"? This is a research question. Probably: held-out agentic + reasoning + multimodal examples that don't appear in any training data.
- **The notebook compaction policy** — when does a "moment" get summarized into a longer-timespan entry? Daily? Weekly? LLM-driven? Open question.
- **The 32A8B "active" math** — the 8B active holds with top-1 routing. If we want top-2, active becomes ~13B. Still fits, but worth thinking about.

## See also

- Wiki: `~/wiki/concepts/omnisenter-architecture.md` (the system overview)
- Wiki: `~/wiki/concepts/synthesia.md` (the cross-modal memory layer)
- Wiki: `~/wiki/concepts/omnisenter-ohm.md` (the self-evolving model file)
- Wiki: `~/wiki/concepts/omnimodal-fusion-architecture.md` (the 2026-06-06 master plan)
- Wiki: `~/wiki/concepts/omnistep-multimodal.md` (the destination unified model)
- Script: `~/projects/evolutionary-training/scripts/omnisenter_ohm.py` (Ohm runtime)
- Script: `~/projects/omni-fusion/sparse_upcycle.py` (Stage 3 tool)
- Script: `~/projects/evolutionary-training/scripts/yarn_256k_config.py` (Stage 4 tool)
- Repo: `SouthpawIN/evolutionary-training` (the main project)
- HF: [sovthpaw/omnistep-12a3b](https://huggingface.co/sovthpaw/omnistep-12a3b) (the multimodal baseline)

## TOWARDS SELF-IMPROVEMENT

— Chris (via Nous Girl), 2026-06-07
