# OmniSenter

> **The project** (not a model name). See the full blog post:
> [`../../blog/the-omnisenter-architecture.md`](../../blog/the-omnisenter-architecture.md)

## Definition

**OmniSenter** is the **project** — the umbrella that contains the Omni
Family of models, the training pipeline, the notebook manager, the Ohm
runtime, and the integration with Hermes Agent. It is **not** a specific
model name.

> **Naming note (per Chris 2026-06-07):** going forward, "OmniSenter"
> should only be used for:
> 1. The project (this page)
> 2. `OmniSenter 12B` — the small function-calling + omnimodal fusion
>    model (a specific entity, see
>    [entities/omnisenter-12b.md](../entities/omnisenter-12b.md))
>
> The flagship is called **Senter Ohm** (not "OmniSenter 32A8B"). The
> multimodal + music one is **OmniSenterStep / Omni SS** (not
> "OmniSenter Step"). See [`../../blog/the-omni-family.md`](../../blog/the-omni-family.md).

## The system

The OmniSenter system has 5 layers:

```
Layer 0 — Stream I/O (Nemotron ASR 0.6B + Cosmos NaViT)
   ↓
Layer 1 — MoE (Senter Ohm ~32A8B, 8B active)
   ↓
Layer 1.5 — Synthesia (cross-modal memory indexer)
   ↓
Layer 2 — Modality plugins (Qwen3-Omni, ACE-Step, LTX-2, TTS, HeartMuLa)
   ↓
Notebook (256K context, every entry indexed by all modalities)
   ↓
Layer 3 — Hermes Agent (smart reasoning, receives notebook slice)
   ↓
Layer 5.5 — Ohm runtime (background self-evolution, atomic swap)
```

## The 5-stage build pipeline

1. **Stage 1** — Agentic Backbone SFT (QLoRA, 34K convs)
2. **Stage 2** — Evolutionary Merge (3 variants × CMA-ES)
3. **Stage 3** — Sparse Upcycle to MoE (8B → 32B MoE)
4. **Stage 4** — 256K YaRN Context Extension
5. **Stage 5** — Plugin + Notebook + Ohm Wiring

## What lives in the project

- **Code**: `evolutionary-training/` (main repo) + 5 sibling repos
- **Blog**: 13 posts in `evolutionary-training/blog/`
- **Wiki**: this `evolutionary-training/wiki/` (consolidated knowledge base)
- **HF models** (transitional v1):
  - `sovthpaw/omnistep-12a3b` (12B total / 3B active, multimodal)
  - `sovthpaw/Omni-Senter-3B` (3B)
  - `sovthpaw/OmniSenter-Base-16B` (16B base)
- **HF models** (planned, new architecture):
  - `sovthpaw/omnisenter-12b` (small function-calling)
  - `sovthpaw/omnisenterstep` (multimodal + music)
  - `sovthpaw/senter-ohm-32a8b` (the flagship)

## See also

- Blog post: [`../../blog/the-omnisenter-architecture.md`](../../blog/the-omnisenter-architecture.md)
- Naming: [`../../blog/the-omni-family.md`](../../blog/the-omni-family.md)
- Related: [Senter Ohm](./senter-ohm.md) · [Omni](./omni.md) · [Senter](./senter.md) · [Pipeline](../../blog/the-5-stage-pipeline.md)
