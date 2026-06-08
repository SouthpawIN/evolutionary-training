# OmniSenterStep (Omni SS) — the multimodal + music + agentic

> **Status:** ⏳ planned · **HF target:** `sovthpaw/omnisenterstep`

## Identity

| | |
|---|---|
| **Full name** | OmniSenterStep (abbreviated: Omni SS) |
| **Type** | OmniSenter + AceStep Darwin fusion |
| **Modalities** | text + vision + audio + speech (in + out) + **music (out)** |
| **Self-evolution** | no (Senter, not Senter Ohm) |

## What it is

**OmniSenter + AceStep Darwin fusion**. So you get:
- The [Senter](../concepts/senter.md) agentic core (function calling,
  notebook, plugin routing)
- The multimodal vision (from Cosmos/Omni)
- The music generation (from ACE-Step)
- The notebook-keeper
- **All in one model**

The most capable single model in the family short of the flagship
(Senter Ohm).

## Naming

- **OmniSenter** = Omni + Senter agentic core
- **Step** = ACE-Step music generation
- **Omni SS** = the shorthand

## Build approach

- Base: [OmniSenter 12B](./omnisenter-12b.md) (or similar Senter
  variant)
- + ACE-Step v1.5 XL 4B DiT (Darwin-merged as a routed expert or as
  a head)
- Multimodal heads attached: Whisper (audio in), NaViT (vision in),
  talker + token2wav (speech out), ACE-Step DiT (music out)
- Dense model, no MoE routing (or single-expert "MoE" if Senter Ohm
  shares weights)

## When to use this

Use OmniSenterStep when you need everything (function calling +
notebook + multimodal I/O + music generation) but don't need the
flagship's full 32B MoE capacity or its self-evolution capability. This
is the "production" model for the OmniSenter system.

## See also

- [Senter concept](../concepts/senter.md)
- [OmniSenter 12B](./omnisenter-12b.md)
- [Senter Ohm 32A8B](./senter-ohm-32a8b.md) (the flagship)
- Blog: [`../../blog/the-omni-family.md`](../../blog/the-omni-family.md)
