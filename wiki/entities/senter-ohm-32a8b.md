# Senter Ohm (32A8B) — the flagship

> **Status:** 🔄 **Stage 1 done · Stage 2-3 in progress** (updated 2026-06-12)
> **HF target:** `sovthpaw/senter-ohm-32a8b`

## Identity

| | |
|---|---|
| **Full name** | Senter Ohm 32A8B |
| **Type** | Sparse-upcycled MoE with the Ohm self-evolution engine |
| **Total params** | ~32B |
| **Active per token** | ~8B (top-1 routing) |
| **Context window** | 256K (YaRN-extended) |
| **Modalities** | text + vision + audio + video + music (in + out) |
| **Self-evolution** | continuous, background, strict-acceptance |
| **Derived from** | New OmniStep (16B, 3-way merge SFT+Cosmos+ACE-Step) + original SFT-8B |

## What it is

The flagship of the OmniSenter project. A ~32B-total / 8B-active MoE
with:
- **4 experts × 8B each**, top-1 routing (8B active per token)
- The [Ohm](../concepts/ohm.md) self-evolution engine bundled in (the
  `.ohm` file format)
- All four mandatory build blocks: Cosmos (vision/audio) + ACE-Step
  (music) + Nemotron 0.6B ASR (speech) + agentic text SFT
- 256K context window (for the notebook)

## Current status (2026-06-12)

### ✅ Stage 1: Agentic SFT — **DONE**
- **Output:** `omnistep-sft-merged-20260612/` (8.19B params, Qwen3-8B + Hermes/Nemotron)
- **Benchmark** (limit=500, lm-eval-harness):
  - **MMLU:** 78.07% (61 subjects) — beats base Qwen3-8B (~70-72%) by +6-8pp
  - **GSM8K:** 81.80% strict / 82.60% flexible — outstanding for 8B
  - **IFEval:** 39.20% prompt-strict / 54.33% inst-strict / 58.86% inst-loose
- **Loss:** 0.3959 → 0.2352 (-40.6%), token accuracy 0.93+
- **HF target for SFT-8B alone:** `sovthpaw/omnistep-sft-8b` (TBD upload)

### 🔄 Stage 2: New OmniStep (3-way merge) — **IN PROGRESS**
- **Parents:** SFT-merged Qwen3-8B + Cosmos3-Nano (text body) + ACE-Step
  (text encoder 1.7B, DiT v15-turbo, VAE)
- **Approach:** Darwin paper-exact merge (ρ=0.5, τ=0.4) for text body
  (398/398 shape-matched, 0 skipped) + attached multimodal modules
- **Output:** `evolution/line2-new-omnistep/` (798 tensors raw, 399 clean
  Qwen3 tensors, 16.4GB F16)
- **Smoke test:** "11×13=143" ✓, "Paris" ✓, factorial one-liner ✓
- **CMA-ES evolution** running: 9 candidates across ρ_b × τ grid
  (`evolution/cmaes-line2/`) — picks the best merge hyperparameters

### 🔄 Stage 3: Sparse upcycle → Senter (32A8B MoE) — **IN PROGRESS**
- **Phase 1 (loadable model with random routers):** construction underway
  at `training-output/senter-ohm-32a8b/`
- **Architecture:** 4 experts (top-1 routing)
  - Expert 0: OmniStep FFN (agentic + multimodal)
  - Expert 1: SFT-8B FFN (pure agentic)
  - Expert 2: OmniStep FFN + small noise (diversity)
  - Expert 3: SFT-8B FFN + small noise (diversity)
  - Shared: attention, embed, norms, lm_head (from SFT-8B)
- **Phase 2 (router training):** LoRA on experts + router, on a mixed
  dataset (Hermes-agentic + Cosmos multimodal + general text)
- **Phase 3 (LoRA on experts + quantization + publish):** pending

### ⏳ Stage 4: 256K YaRN context — pending
### ⏳ Stage 5: Plugin + notebook + Ohm wiring — pending

## Architecture (32B MoE)

```
Senter Ohm 32A8B
├── shared/                              8B (~3B in FFN)
│   ├── embed_tokens (151,936 vocab)
│   ├── attention (36 layers, Qwen3)
│   ├── norms (per layer)
│   └── lm_head (151,936)
│
├── experts/                             4 × 8B = 32B
│   ├── expert.0/    FFN from OmniStep (50% SFT + 50% Cosmos)
│   ├── expert.1/    FFN from SFT-8B (pure Hermes/Nemotron agentic)
│   ├── expert.2/    FFN from OmniStep + noise(0.001)
│   └── expert.3/    FFN from SFT-8B + noise(0.001)
│
└── router/                             0.18B (1 linear/layer)
    └── top-1 routing, load-balancing aux loss
```

## How it's built (current sequence)

| Stage | What | Status (2026-06-12) |
|---|---|---|
| **1** | Agentic SFT (QLoRA, 34K convs) | ✅ **DONE** (8B MMLU 78.07%) |
| **2** | New OmniStep (3-way merge + CMA-ES) | 🔄 Text body done, CMA-ES running 9 candidates |
| **3** | Sparse upcycle → Senter 32A8B | 🔄 Phase 1 (loadable model) in build |
| **4** | Router + LoRA training on experts | ⏳ Queued (start after CMA-ES) |
| **5** | YaRN 256K context extension | ⏳ Queued |
| **6** | Plugin + notebook + `.ohm` wiring | ⏳ Queued |
| **7** | Quantize to Q4_K_M + publish to HF | ⏳ Queued |

## See also

- [Senter Ohm concept](../concepts/senter-ohm.md)
- [OmniStep concept](../concepts/omnistep.md) — text body source
- [Ohm concept](../concepts/ohm.md) — self-evolution engine
- [Senter concept](../concepts/senter.md) — the MoE without Ohm
- Blog: [`../../blog/the-omni-family.md`](../../blog/the-omni-family.md)
- Blog: [`../../blog/senter-ohm-flagship.md`](../../blog/senter-ohm-flagship.md)
- Blog: [`../../blog/senter-ohm-32a8b-math.md`](../../blog/senter-ohm-32a8b-math.md)
- Blog: [`../../blog/the-5-stage-pipeline.md`](../../blog/the-5-stage-pipeline.md)
- Blog: [`../../blog/sparse-upcycling-deep-dive.md`](../../blog/sparse-upcycling-deep-dive.md)
