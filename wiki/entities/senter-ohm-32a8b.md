# OmniSenter Ohm (~32A8B) — the flagship

> **Status:** ⏳ planned · **HF target:** `sovthpaw/omnisenter-ohm-32a8b`
>
> **Renamed 2026-06-08.** This entity was previously called "Senter Ohm
> (32A8B)" under the old naming. The new name is **OmniSenter Ohm**
> (Standard = no engine, Ohm = with engine). See
> [`the-omni-family.md`](../../blog/the-omni-family.md) for the
> canonical naming convention.

## Identity

| | |
|---|---|
| **Full name** | OmniSenter Ohm 32A8B |
| **Type** | Sparse-upcycled MoE with the Ohm self-evolution engine |
| **Total params** | ~32B |
| **Active per token** | ~8B (top-1 routing) |
| **Context window** | 256K (YaRN-extended) |
| **Modalities** | text + vision + audio + video + music (in + out) + speech (in) |
| **Self-evolution** | continuous, background, strict-acceptance |
| **Built from** | Cosmos + Nemotron 0.6B ASR + 8B SFT + upgraded ACE-Step, all merged, then sparse-upcycled |

## What it is

The flagship of the OmniSenter project. A ~32B-total / 8B-active MoE
with:
- 5-6 routed experts (agentic, image/video, music, long-context,
  Synthesia, generalist)
- The [Ohm](../concepts/ohm.md) self-evolution engine bundled in (the
  `.ohm` file format)
- The 256K context window (for the notebook)
- All modalities in and out, including the **mandatory ACE-Step music
  merge** and the **Nemotron 0.6B streaming ASR** head

## How it's built

The full 5-stage pipeline (see
[`../../blog/the-5-stage-pipeline.md`](../../blog/the-5-stage-pipeline.md)):

| Stage | What | Output |
|---|---|---|
| 1 | Agentic SFT (QLoRA, ~31K convs) | `omnisenter-8b-sft` |
| 2 | Evolutionary merge of 8B SFT + ACE-Step into OmniStep (~12A3B) | `omnistep-12a3b-merged` |
| 3 | Sparse upcycle of OmniStep to 32A8B MoE | `omnisenter-moe-32a8b` |
| 4 | 256K YaRN context extension | `omnisenter-moe-32a8b-256k` |
| 5 | Plugin + notebook + Senter core + Ohm wiring | deployable `.ohm` bundle |

**Stage 1 is running right now** (PID 3884286, resumed from
checkpoint-1000, target 3954 steps, see
[`../../AGENTS.md`](../../AGENTS.md)).

**Variants:**
- **OmniSenter Standard** = stages 1-5 without the Ohm engine
  (no self-evolution)
- **OmniSenter Ohm** = stages 1-5 with the Ohm engine bundled (this
  entity)

Both are valid shipping targets. The Standard variant is the static
serving model; the Ohm variant self-evolves in the background.

## See also

- [Senter Ohm concept](../concepts/senter-ohm.md) (also being
  retitled `omnisenter.md` shortly)
- [The Omni Family](../../blog/the-omni-family.md) (canonical naming)
- Blog: [`../../blog/senter-ohm-flagship.md`](../../blog/senter-ohm-flagship.md)
  (also being retitled `omnisenter-flagship.md` shortly)
- Blog: [`../../blog/senter-ohm-32a8b-math.md`](../../blog/senter-ohm-32a8b-math.md)
  (also being retitled `omnisenter-32a8b-math.md` shortly)
