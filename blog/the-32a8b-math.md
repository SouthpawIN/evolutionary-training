# The 32A8B Math: How Big is OmniSenter Anyway?

> **TOWARDS SELF-IMPROVEMENT** — a 2026-06-07 design post by Chris (via Nous Girl)

The full sizing breakdown for the OmniSenter-MoE-32A8B target. Per-layer params, active vs total, 4-bit vs bf16 disk, VRAM at inference, VRAM at training. With tables.

## The Qwen3-8B base (the starting point)

The Stage 1 SFT base is `gen-0-clean`, which is a Cosmos3×Qwen3-8B merge, stripped of multimodal tensors. The text-only base is Qwen3-8B class:

| Component | Params |
|---|---|
| Per-layer attention (36 layers) | 50M each → 1.8B total |
| Per-layer FFN (36 layers) | 150M each → 5.4B total |
| Embeddings (152K vocab × 4096 dim) | 0.62B |
| **Total dense** | **~8.2B** |
| Native context (max_position_embeddings) | 40,960 |
| RoPE theta | 1,000,000 |

## The sparse upcycle math

For a MoE with N experts per layer (top-k routing):

| Component | Params per layer | Total |
|---|---|---|
| Attention (shared) | 50M | 1.8B |
| N experts (each = copy of FFN) | N × 150M | N × 5.4B |
| Router | ~0.5M | ~18M |
| Embeddings | — | 0.62B |
| **Total** | **50M + N×150M** | **~2.4B + N×5.4B** |

For N=4: 2.4 + 21.6 = 24B total
For N=6: 2.4 + 32.4 = 35B total
For N=8: 2.4 + 43.2 = 46B total

## Active per token (top-k routing)

| Component | Active per layer (top-1) | Active per layer (top-2) |
|---|---|---|
| Attention (always on) | 50M | 50M |
| Selected expert(s) | 1 × 150M = 150M | 2 × 150M = 300M |
| **Per-layer active** | **200M** | **350M** |
| **Across 36 layers** | 7.2B | 12.6B |
| + Embeddings | 0.6B | 0.6B |
| **Total active** | **~7.8B ≈ 8B** ✓ | **~13B** |

The "8B active" target is achieved with top-1 routing, regardless of N. Adding more experts adds knowledge (total params) but not compute (active stays at 8B).

## The shared-expert design (DeepSeek-V2 style)

Add 1 always-on shared expert (~75M per layer, half the size of a normal expert) + N routed experts.

| Component | Active per layer |
|---|---|
| Attention | 50M |
| Shared expert (always on) | 75M |
| Top-1 routed expert | 150M |
| **Per-layer active** | **275M** |
| **Across 36 layers** | 9.9B |
| + Embeddings | 0.6B |
| **Total active** | **~10.5B** |

The shared expert adds ~2.5B to the active count but provides common-knowledge coverage. For the strict 8B-active target, skip the shared expert. For 10.5B-active (still fast), include it.

## The sizing table

| N experts | Total | Active @ top-1 | Active @ shared+top-1 | Disk @ 4-bit Q4_K_M | Disk @ bf16 | Inference VRAM (1× 3090) |
|---|---|---|---|---|---|---|
| 1 (dense) | 8B | 8B | 10.5B | 4GB | 16GB | 6GB |
| 2 | 13B | 8B | 10.5B | 7GB | 26GB | 10GB |
| 4 | 24B | 8B | 10.5B | 13GB | 48GB | 17GB |
| **6** | **35B** | **8B** | **10.5B** | **18GB** | **70GB** | **22GB** |
| 8 | 46B | 8B | 10.5B | 24GB | 92GB | 28GB |
| 10 | 57B | 8B | 10.5B | 30GB | 114GB | 34GB |

The sweet spot: **N=6, 35B total, 8B active, 18GB at 4-bit, fits one 3090 for inference with room for KV cache**.

## Inference VRAM by context length

For OmniSenter-MoE-35B at 4-bit, top-1 routing:

| Context | Model weights | KV cache (turbo4) | Activations | Scratch | Total |
|---|---|---|---|---|---|
| 8K | 18GB | 0.5GB | 0.5GB | 0.5GB | **~20GB** |
| 32K | 18GB | 2GB | 1GB | 0.5GB | **~22GB** |
| 128K | 18GB | 8GB | 2GB | 1GB | **~29GB** |
| 256K | 18GB | 16GB | 4GB | 1.5GB | **~40GB** |

The KV cache grows with context. At 256K, you need both 3090s (~40GB total VRAM).

## Training VRAM (QLoRA)

For OmniSenter-MoE-35B QLoRA training, top-1 routing, batch=1, seq=8K:

| Component | VRAM |
|---|---|
| Base weights (4-bit) | 18GB |
| LoRA adapters (r=64, all 7 modules) | 1.5GB |
| LoRA gradients | 1.5GB |
| 8-bit optimizer state (paged_adamw_8bit) | 3GB |
| Activations (batch 1, seq 8K, grad ckpt) | 8GB |
| KV cache + scratch | 2GB |
| **Total** | **~34GB** |

**Fits 2× 3090 with headroom.** Tight for batch > 1 or seq > 8K, but doable for the continued-training pass in Stage 3 (100-200 steps, no need for large batches).

## HF upload size (matching omnistep-12a3b layout)

The existing `sovthpaw/omnistep-12a3b` publishes 4 quantizations + 4 safetensors shards. For `omnisenter-moe-32a8b` at 35B:

| Quantization | Format | Size |
|---|---|---|
| F16 | safetensors | ~70GB |
| Q8_0 | GGUF | ~38GB |
| Q4_K_M | GGUF | ~18GB |
| Q4_0 | GGUF | ~16GB |
| **Total upload** | | **~142GB** |

This is in the same range as `omnistep-12a3b` (~35GB total but smaller model). Tractable for HF upload.

## The "fits the rig" check

For Chris's 2× RTX 3090 (48GB total) setup:

| Use case | Fits? | Notes |
|---|---|---|
| Inference @ 4-bit @ 32K context, 1 GPU | ✅ yes | 22GB used, 2GB headroom on one 3090 |
| Inference @ 4-bit @ 256K context | ⚠️ needs both GPUs | 40GB total, 8GB headroom across both |
| QLoRA training @ 8K context, batch 1 | ✅ yes | 34GB used across both GPUs |
| Full fine-tune @ any context | ❌ no | needs ~200GB+ |
| 35B dense (no MoE) at 4-bit, any context | ⚠️ inference only | 18GB model + KV fits, but no MoE benefit |

## The naming convention (XAYB)

Following the [[omnisenter-naming|existing convention]]:

| Model | Total | Active | Composition |
|---|---|---|---|
| OmniLance 6B (existing) | 6B | 3B | Omni 3B + Lance 3B → 3B child, MoE-routed |
| OmniStep 6B (existing) | 6B | 3B | Omni 3B + ACE-Step 3B → 3B child, MoE-routed |
| OmniSenter 6A3B (existing) | 6B active | 3B | Hierarchical MoE: routes between OmniLance 6B and OmniStep 6B sub-models |
| **OmniSenter 32A8B (new)** | **32B** | **8B** | Cosmos base (8B) + 5 specialists (32B total), MoE top-1 |

The "A" = active, "B" = active size in B. So **32A8B = 32B total, 8B active**.

## The Q4_K_M is the recommended deployment

For Chris's HF pattern:
- F16 for full-fidelity inference (research, eval)
- Q8_0 for high-quality production (slight quality loss, 2× size reduction)
- **Q4_K_M for everyday use** (best quality/size tradeoff, ~18GB for 32A8B)
- Q4_0 for ultra-low-end (slightly worse than K_M, marginally smaller)

The Q4_K_M is the one most users will download. ~18GB is a one-time download, then the model is local forever.

## See also

- [omnisenter-self-evolving.md](./omnisenter-self-evolving.md) — the flagship overview
- [sparse-upcycling-deep-dive.md](./sparse-upcycling-deep-dive.md) — the Stage 3 deep dive with the math
- [the-5-stage-pipeline.md](./the-5-stage-pipeline.md) — the build roadmap
- [omnisenter-architecture](file:///home/sovthpaw/wiki/concepts/omnisenter-architecture.md) — the system overview

## TOWARDS SELF-IMPROVEMENT

— Chris (via Nous Girl), 2026-06-07
