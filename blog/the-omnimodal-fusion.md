---
title: "The Omnimodal Fusion: Cosmos × ACE-Step × Nemotron ASR"
date: 2026-06-08
author: Nous Girl
hero: assets/images/synesthesia-concept.png
tags: [cosmos, ace-step, nemotron-asr, multimodal, darwin-family, omnimodal-fusion]
summary: >
  The three-component Darwin Family fusion that powers every multimodal
  model in the Omni Family: Cosmos3-Nano (multimodal reasoning) ×
  ACE-Step 4B (music generation) × Nemotron ASR 0.6B (speech
  conductor). The master plan, the component models, and the routing
  architecture.
related:
  - the-omni-family.md
  - the-omnistep-multimodal.md
  - the-senter-architecture.md
---


> **Revised 2026-06-08 (naming).** Per the canonical 4-model lineup in
> [`the-omni-family.md`](./the-omni-family.md), the project is
> "OmniSenter" but the **models** are **OmniStep** (8B), **OmniStep Ohm**,
> **Senter** (32A8B MoE), and **Senter Ohm** (flagship). No more
> "OmniSenter 12B" or "OmniSenterStep" as model names. The fusion recipe
> described in this post applies to **OmniStep** (8B) and gets
> sparse-upcycled to **Senter** (32A8B) in Stage 3.

# The Omnimodal Fusion: Cosmos × ACE-Step × Nemotron ASR

> **TOWARDS SELF-IMPROVEMENT** — a 2026-06-07 design post by Chris (via Nous Girl)

![Three component models converging into one omnimodal system — the Cosmos text/vision/video brain, the ACE-Step music DiT, and the Nemotron ASR conductor. Cosmic convergence.](../assets/images/synesthesia-concept.png)

> **Naming.** This is the **multimodal foundation** that every model in
> the Omni Family is built on top of. The **Omni** series is what
> emerges from this fusion. Read
> [`the-omni-family.md`](./the-omni-family.md) for the full taxonomy.

The master plan for fusing all modalities into a single Darwin Family
model.

## Three-Component Fusion

```
┌──────────────────────────────────────────────────────────┐
│                   OMNIMODAL FUSION                       │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Cosmos3-Nano │  │ ACE-Step 4B  │  │ Nemotron ASR  │  │
│  │  (multimodal  │  │ (music gen)  │  │  0.6B (STS)   │  │
│  │   reasoning)  │  │              │  │               │  │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘  │
│         │                 │                   │          │
│         └─────────┬───────┴───────────────────┘          │
│                   ▼                                      │
│         Darwin Family Merge                              │
│                   │                                      │
│                   ▼                                      │
│         Omnimodal Base Model                             │
│         (speech in, text out, music out, video out)      │
│                   │                                      │
│                   ×                                      │
│         Omni Base 16B (HF: sovthpaw/OmniSenter-Base-16B) │
│                   │                                      │
│                   ▼                                      │
│         FINAL SENTER (or SENTER OHM, or OMNISTEP)         │
│         agentic · omnimodal · speech-conductor           │
└──────────────────────────────────────────────────────────┘
```

## Component Models

| Component | Model | Size | Role | Architecture |
|-----------|-------|------|------|-------------|
| **Brain** | Cosmos3-Nano | ~8B | Multimodal reasoning, video, vision | MoE Transformer |
| **Music** | ACE-Step v1.5 XL SFT | 4B | Music generation | DiT (Diffusion Transformer) |
| **Speech** | Nemotron ASR Streaming | 0.6B | Speech-to-text input, orchestration conductor | FastConformer-CacheAware-RNNT |

## Nemotron ASR 0.6B

Source: `nvidia/nemotron-3.5-asr-streaming-0.6b` (released 2026-06-04)

- **Architecture**: 24-layer Cache-Aware FastConformer encoder + RNNT
  decoder
- **Size**: 600M params
- **Languages**: 40 language-locales (19 production-ready)
- **Key features**: Native streaming (80-1120ms chunks), punctuation +
  capitalization built-in
- **Acoustic embedding**: 512-dim, concatenated with 128-dim language
  prompt
- **Cache-aware design**: Reuses hidden states to eliminate redundant
  computation — optimized for low-latency voice agents

### Why This Belongs Here

The Nemotron ASR is not just speech-to-text — it's the **conductor** of
the omnimodal system:
- **Always listening** — streaming ASR that processes speech
  continuously
- **Aware of all modalities** — receives context from Cosmos (what's
  being reasoned about), ACE-Step (what music is playing)
- **Can redirect** — if user says "stop the music" or "what's on screen",
  the ASR component orchestrates the response
- **Reports on state** — can describe what the system is doing at any
  moment

## Routing Architecture

Each component works **independently** but the ASR conductor is **aware
of all**:

```
Speech in ──→ [Nemotron ASR] ──→ transcribed text
                    │
                    ├──→ "play jazz" ──→ [ACE-Step 4B] ──→ music out
                    │
                    ├──→ "what do you see?" ──→ [Cosmos3-Nano] ──→ text/video out
                    │
                    └──→ "stop music" ──→ signal to ACE-Step
```

- Cosmos works independently on multimodal reasoning
- ACE-Step works independently on music generation
- Nemotron ASR works independently on speech recognition
- ASR has **read access** to all modality states and **write access** to
  stop/redirect

## Darwin Merge Strategy

### Challenge: Architecture Heterogeneity

| Component | Architecture | Compatible with Darwin? |
|-----------|-------------|------------------------|
| Cosmos3-Nano | MoE Transformer (Qwen3-based) | ✅ Yes (already merged with Qwen3-8B → OmniSenter-Base-16B) |
| ACE-Step 4B | DiT (Qwen3 text encoder + diffusion decoder) | ✅ Partial (text encoder shares Qwen3 skeleton) |
| Nemotron ASR | FastConformer + RNNT | ❌ No shared architecture with transformer models |

### Approach

**Phase 1: Cosmos × ACE-Step (OmniStep)**
- Already achieved: Darwin merge of Qwen2.5-Omni-3B × ACE-Step v1.5
- Published at [sovthpaw/omnistep-12a3b](https://huggingface.co/sovthpaw/omnistep-12a3b)
  — 12A3B (12B total, 3B active), 4 GGUFs + 4 safetensors shards
- This is the **OmniStep** in the new taxonomy

**Phase 2: Attach Nemotron ASR**
- ASR can't be Darwin-merged directly (architecture mismatch)
- Option A: **Plugin attachment** — ASR feeds its transcribed text into
  the fused model's text stream
- Option B: **Encoder distillation** — train the Cosmos audio encoder
  to produce equivalent embeddings to the FastConformer, then
  Darwin-merge the distilled encoder
- Option C: **Context-passing bridge** — ASR runs alongside, passes
  token stream + language embeddings to Cosmos via a learned projection

**Phase 3: Fuse with Senter (the agentic core)**
- [sovthpaw/OmniSenter-Base-16B](https://huggingface.co/sovthpaw/OmniSenter-Base-16B)
  is the current published base (16B, multimodal, Darwin-merged)
- The Senter family adds the agentic core (function calling + notebook)
  on top
- The result is **Senter**, in any of its sizes (Senter,
  OmniStep, Senter Ohm)

## Current Blockers (as of 2026-06-07)

1. **Stage 1 SFT training** — running, step 596/4268 (gen-0-clean 8B
   base)
2. **Nemotron ASR integration** — architecture mismatch with Darwin
   merge approach; likely going with Option A (plugin attachment) or
   Option C (context-passing bridge) for v1
3. **ACE-Step largest version** — need the 4B DiT (XL), not the 2B SFT

## What ships first

The target order:
1. **Senter** (small function-calling + omnimodal fusion) —
   first to ship. Cosmos + Senter + Hermes-trained Qwen VL 8B Darwin
   children. Dense-ish, ~12B active.
2. **OmniStep / OmniStep** — OmniSenter + AceStep Darwin fusion
   (adds music generation).
3. **Senter Ohm ~32A8B** — the flagship. OmniStep sparse-upcycled
   to a 32B MoE + the Ohm self-evolution engine bundled.

All three will eventually **replace** the current transitional HF models
(`omnistep-12a3b`, `Omni-Senter-3B`, `OmniSenter-Base-16B`).

## See also

- [`the-omnistep-multimodal.md`](./the-omnistep-multimodal.md) — the
  destination unified model (Phase 1 of the fusion)
- [`the-senter-architecture.md`](./the-omnisenter-architecture.md) —
  the multi-stage pipeline built on top of this fusion
- [`senter-ohm-flagship.md`](./senter-ohm-flagship.md) — the Senter Ohm
  32A8B flagship that emerges from the full fusion
- [`senter-as-hermes-auxiliary.md`](./senter-as-hermes-auxiliary.md) —
  the integration with Hermes Agent
- [sovthpaw/omnistep-12a3b](https://huggingface.co/sovthpaw/omnistep-12a3b)
  — the published OmniStep baseline (transitional)
- [sovthpaw/OmniSenter-Base-16B](https://huggingface.co/sovthpaw/OmniSenter-Base-16B)
  — the published 16B base (transitional)
- Paper: [Komatsuzaki et al. 2022 "Sparse Upcycling"](https://arxiv.org/abs/2212.05055)
- Paper: [DeepSeek-V2 shared-expert MoE](https://arxiv.org/abs/2405.04434)

## TOWARDS SELF-IMPROVEMENT

— Chris (via Nous Girl), 2026-06-07
