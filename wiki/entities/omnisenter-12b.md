# OmniSenter 12B — the small Senter

> **Status:** ⏳ planned · **HF target:** `sovthpaw/omnisenter-12b`
>
> **Superseded by the architecture simplification (2026-06-08).** The
> small model in the new lineup is **OmniStep** (~12A3B, no agentic
> core, no Ohm) — not "OmniSenter 12B". The flagship is **OmniSenter
> 32A8B** (Standard + Ohm). This entity is kept for historical
> reference; treat it as transitional until the catalog cleanup lands.

## Identity

| | |
|---|---|
| **Full name** | OmniSenter 12B |
| **Type** | Small function-calling + omnimodal fusion (dense-ish) |
| **Total params** | ~12B (aspirational) |
| **Active per token** | ~12B (dense) |
| **Context window** | 256K (target) |
| **Modalities** | text + vision + audio + speech (in + out) |
| **Self-evolution** | no (Senter, not Senter Ohm) |

## What it is

The small one. Built from **Cosmos + Senter + Hermes-trained Qwen VL 8B
Darwin children**. The **shipping target** for routine function calling
+ omnimodal fusion on commodity hardware.

The "12B" is the aspirational active-parameter count — the actual merge
may come out to ~10-14B active depending on how the Darwin children
stack. It's a **dense-ish** model, not a MoE.

## Build approach

- Base: Cosmos3-Nano (multimodal reasoning)
- + Senter agentic core (function calling, notebook manager)
- + Hermes-trained Qwen VL 8B Darwin children (vision-language
  specialization)
- All Darwin-merged via paper-exact 2-parent merge
- Dense model, no MoE routing

## Why this exists

The flagship (Senter Ohm 32A8B) is the moonshot. **OmniSenter 12B is the
shipping target** — small enough to run on a single RTX 3090 in 4-bit
(~6-8GB), fast enough for routine use, capable enough to handle
function calling + notebook + multimodal I/O for typical agent
workloads.

## See also

- [Senter concept](../concepts/senter.md)
- Blog: [`../../blog/the-omni-family.md`](../../blog/the-omni-family.md) (the naming taxonomy)
- Related: [Senter Ohm 32A8B](./senter-ohm-32a8b.md) · [OmniSenterStep](./omnisenterstep.md)
