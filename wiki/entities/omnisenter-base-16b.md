# OmniSenter-Base 16B — the Omni base

> **Status:** ✅ published (transitional v1) · **HF:** [`sovthpaw/OmniSenter-Base-16B`](https://huggingface.co/sovthpaw/OmniSenter-Base-16B)

## Identity

| | |
|---|---|
| **Full name** | OmniSenter-Base 16B |
| **Type** | Multimodal base (Darwin-merged, no agentic core) |
| **Total params** | 16B |
| **Active per token** | 16B (dense) |
| **Context window** | standard |
| **Modalities** | text + vision + audio + video (text-generation pipeline) |
| **Self-evolution** | no |

## What it is

A 16B multimodal **base** model. Darwin-merged from:
- **Qwen3-8B** (text backbone, agentic capability)
- **nvidia/Cosmos3-Nano** (multimodal capability, vision + video)

It's the **Omni** base that future [OmniSenter 12B](./omnisenter-12b.md)
and [Senter Ohm 32A8B](./senter-ohm-32a8b.md) models will be built on
top of. Pre-Senter — no notebook, no function calling, no agentic core.

## Composition

| Component | Source | Role |
|---|---|---|
| Text backbone | Qwen3-8B | Reasoning, instruction following |
| Multimodal | Cosmos3-Nano | Vision, video, audio understanding |
| Total | Darwin-merged | 16B, 7 safetensors shards |

## Status: transitional

This is the v1 Omni base. When the new architecture ships (OmniSenter
12B as the small Senter, Senter Ohm 32A8B as the flagship), this base
will be **superseded** by the new releases.

Use it now as the multimodal base for downstream Senter fine-tunes.
When the new architecture's base ships, switch over.

## See also

- HF: [`sovthpaw/OmniSenter-Base-16B`](https://huggingface.co/sovthpaw/OmniSenter-Base-16B)
- [OmniSenter concept](../concepts/omnisenter.md)
- Related: [OmniSenter 12B](./omnisenter-12b.md) · [Senter Ohm 32A8B](./senter-ohm-32a8b.md)
- Blog: [`../../blog/the-omni-family.md`](../../blog/the-omni-family.md) (the naming refactor)
- Blog: [`../../blog/the-omnimodal-fusion.md`](../../blog/the-omnimodal-fusion.md) (the three-component fusion that produces this)
