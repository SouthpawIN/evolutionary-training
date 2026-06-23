# Senter (32A8B MoE)

> **The agentic MoE without the Ohm engine.** Senter Ohm (the
> [flagship](../entities/senter-ohm-32a8b.md)) adds the self-evolution
> runtime on top of this.

## Definition

**Senter** is the agentic flagship as a sparse-upcycled Mixture of
Experts. Same model weights as Senter Ohm — the only difference is the
absence of the [Ohm](./ohm.md) self-evolution engine. Senter is what
you ship when you don't want the model to self-modify in production;
Senter Ohm is what you ship when you do.

## Architecture (32B MoE)

```
Senter 32A8B
├── shared/                              8B (~3B in FFN)
│   ├── embed_tokens (151,936 vocab)
│   ├── attention (36 layers, Qwen3)
│   ├── norms (per layer)
│   └── lm_head (151,936)
│
├── experts/                             4 × 8B = 32B
│   ├── expert.0/    FFN from [OmniStep](./omnistep.md) (50% SFT + 50% Cosmos)
│   ├── expert.1/    FFN from agentic [SFT-8B](../../blog/senter-ohm-flagship.md)
│   ├── expert.2/    FFN from OmniStep + noise(0.001)
│   └── expert.3/    FFN from SFT-8B + noise(0.001)
│
└── router/                             0.18B (1 linear/layer)
    └── top-1 routing, load-balancing aux loss
```

## How it's built

1. Take the [new OmniStep](./omnistep.md) (16B, 3-way merge of
   SFT-merged Qwen3-8B + Cosmos3-Nano text body + ACE-Step attached
   modules)
2. Replicate its FFN as 4 expert copies (2 with original weights from
   OmniStep, 2 from the SFT-8B lineage)
3. Add a top-1 router per layer (random init; trained in Phase 2)
4. Save as a loadable Qwen3MoE bundle
5. (Phase 2) Train routers + LoRA on experts with a mixed dataset
6. (Phase 3) Quantize to Q4_K_M, publish to HF

## Status (2026-06-12)

- **Phase 1 (loadable MoE construction):** in progress at
  `training-output/senter-ohm-32a8b/`
- **Phase 2 (router training):** queued
- **Phase 3 (quantize + publish):** queued

See [senter-ohm-32a8b entity](../entities/senter-ohm-32a8b.md) for the
full pipeline status.

## Why 4 experts (not 8, not 16)?

- **4 experts × 8B = 32B total, 8B active per token** matches the
  32A8B designation
- **Top-1 routing** is simpler than top-2; load-balancing aux loss
  prevents collapse
- **2-from-source × 2 sources** (OmniStep + SFT-8B) gives the router
  enough headroom to learn "this token wants multimodal vs pure
  agentic" without an explosion of expert combinations
- **2 noisy copies** of each source provide intra-source diversity, so
  the router doesn't collapse to a single expert per source

## See also

- [Senter Ohm (flagship)](../entities/senter-ohm-32a8b.md) — Senter + Ohm self-evolution
- [OmniStep](./omnistep.md) — text body source
- [SFT-8B entity](../entities/omni-senter-3b.md) — agentic seed
- [Darwin Family merge](./darwin-family.md) — merge methodology
- [Ohm runtime](./ohm.md) — adds self-evolution
- Blog: [`../../blog/sparse-upcycling-deep-dive.md`](../../blog/sparse-upcycling-deep-dive.md)
- Blog: [`../../blog/senter-ohm-32a8b-math.md`](../../blog/senter-ohm-32a8b-math.md)
