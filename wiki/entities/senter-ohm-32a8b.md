# Senter Ohm (32A8B) — the flagship

> **Status:** ⏳ planned · **HF target:** `sovthpaw/senter-ohm-32a8b`

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

## What it is

The flagship of the OmniSenter project. A ~32B-total / 8B-active MoE
with:
- 5-6 routed experts (agentic, image/video, music, long-context,
  Synthesia, generalist)
- The [Ohm](../concepts/ohm.md) self-evolution engine bundled in (the
  `.ohm` file format)
- The 256K context window (for the notebook)
- All modalities in and out

## How it's built

The full 5-stage pipeline (see
[`../../blog/the-5-stage-pipeline.md`](../../blog/the-5-stage-pipeline.md)):

| Stage | What | Output |
|---|---|---|
| 1 | Agentic SFT (QLoRA, 34K convs) | `senter-ohm-8b-sft` |
| 2 | Evolutionary merge (CMA-ES) | `senter-ohm-8b-merged` |
| 3 | Sparse upcycle to MoE | `senter-ohm-moe-32a8b` |
| 4 | 256K YaRN context | `senter-ohm-moe-32a8b-256k` |
| 5 | Plugin + notebook + Ohm wiring | deployable `.ohm` bundle |

Stage 1 is running right now (PID 3975936, step 596/4268).

## See also

- [Senter Ohm concept](../concepts/senter-ohm.md)
- Blog: [`../../blog/senter-ohm-flagship.md`](../../blog/senter-ohm-flagship.md)
- Blog: [`../../blog/senter-ohm-32a8b-math.md`](../../blog/senter-ohm-32a8b-math.md)
