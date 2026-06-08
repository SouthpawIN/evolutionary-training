# Senter Ohm

> **The flagship model.** See the full blog post:
> [`../../blog/senter-ohm-flagship.md`](../../blog/senter-ohm-flagship.md)

## Definition

**Senter Ohm** is the flagship model of the OmniSenter project — a
~32B-total, ~8B-active Mixture-of-Experts (top-1 routing) with the
[Ohm](./ohm.md) self-evolution engine bundled in.

The name decomposes:
- **Senter** = Omni + agentic core (function calling, notebook
  management, plugin routing)
- **Ohm** = the self-evolution engine (background CMA-ES, atomic weight
  swap, strict improvement acceptance)

## The headline numbers

| | |
|---|---|
| **Total params** | ~32B |
| **Active per token** | ~8B (top-1 routing) |
| **Context window** | 256K (via YaRN) |
| **Modalities** | text + vision + audio + video + music (in + out) |
| **Self-evolution** | continuous, background, strict-acceptance |
| **Inference VRAM** | ~22GB at 4-bit Q4_K_M, 32K context (fits 1× RTX 3090) |
| **Disk (Q4_K_M GGUF)** | ~18GB |
| **HF target** | `sovthpaw/senter-ohm-32a8b` (planned) |

## How it's built

The 5-stage pipeline (see [`../../blog/the-5-stage-pipeline.md`](../../blog/the-5-stage-pipeline.md)):

| Stage | What | Input | Output |
|---|---|---|---|
| 1 | Agentic SFT (QLoRA) | Qwen3-8B | `senter-ohm-8b-sft` |
| 2 | Evolutionary merge (CMA-ES) | 3 specialized variants | `senter-ohm-8b-merged` |
| 3 | Sparse upcycle to MoE | merged 8B + 5 specialists | `senter-ohm-moe-32a8b` |
| 4 | 256K YaRN context extension | MoE 32A8B | `senter-ohm-moe-32a8b-256k` |
| 5 | Plugin + notebook + Ohm wiring | 256K MoE | deployable `.ohm` bundle |

## The 5-6 routed experts

1. Agentic expert (function calling, tool use)
2. Image/video expert (distilled from Qwen3-Omni-30B-A3B)
3. Music expert (distilled from HeartMuLa / ACE-Step)
4. Long-context expert (the YaRN-extended anchor)
5. **Synthesia expert** (cross-modal memory, see [synthesia.md](./synthesia.md))
6. Generalist fallback (catches fall-throughs)

## The 256K context

The 256K context is **for the notebook** — the structured state object
that flows between Senter Ohm and Hermes Agent. The raw conversation
stays short; the notebook entries get the long window.

## See also

- Blog post: [`../../blog/senter-ohm-flagship.md`](../../blog/senter-ohm-flagship.md)
- Math: [`../../blog/senter-ohm-32a8b-math.md`](../../blog/senter-ohm-32a8b-math.md)
- Pipeline: [`../../blog/the-5-stage-pipeline.md`](../../blog/the-5-stage-pipeline.md)
- Related: [Ohm engine](./ohm.md) · [Synthesia expert](./synthesia.md) · [Sparse upcycling](../../blog/sparse-upcycling-deep-dive.md) · [Notebook schema](./notebook.md)
- Script: `scripts/omnisenter_ohm.py` (the Ohm runtime, in `evolutionary-training`)
- Script: `multimodal-expansion/scripts/sparse_upcycle.py` (Stage 3 tool)
