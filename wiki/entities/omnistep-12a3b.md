# OmniStep 12A3B — the transitional baseline

> **Status:** ✅ published · **HF:** [`sovthpaw/omnistep-12a3b`](https://huggingface.co/sovthpaw/omnistep-12a3b)
>
> **Transitional v1.** The new architecture (2026-06-08) will ship a
> next-generation OmniStep (~12A3B) with the four mandatory blocks
> (Cosmos + Nemotron 0.6B ASR + 8B SFT + ACE-Step). This entity
> documents the v1 that proved the approach.

## Identity

| | |
|---|---|
| **Full name** | OmniStep 12A3B |
| **Type** | Darwin-merged multimodal baseline (transitional v1) |
| **Total params** | 12B |
| **Active per token** | 3B |
| **Context window** | 8K (configurable) |
| **Modalities** | text + vision + audio + speech (in + out) + music (out) |
| **Self-evolution** | no (no Senter agentic core, no Ohm engine) |

## What it is

The current published baseline. A paper-exact 2-parent Darwin merge of:
- **Qwen2.5-Omni-3B** (multimodal parent: text + Whisper + NaViT +
  talker + token2wav)
- **ACE-Step v1.5 XL 4B DiT** (music parent: DiT decoder + music text
  encoder)

The 12A3B naming means **12B total, 3B active**.

## Quantizations

| Quant | Size | VRAM | Best for |
|---|---|---|---|
| **F16** | 6.4GB | 6.4GB | Maximum quality |
| **Q8_0** | 3.4GB | 3.4GB | Near-F16, balanced |
| **Q4_K_M** | 2.0GB | 2.0GB | **Recommended** — best size/quality |
| **Q4_0** | 1.9GB | 1.9GB | Smallest |

Plus 4 safetensors shards for vllm.

## Status: transitional

This is the v1 OmniStep. The new architecture (Senter Ohm 32A8B,
OmniSenter 12B, OmniSenterStep) will **replace** it as it ships.

Use it now as the multimodal baseline. When the new architecture
ships, switch over.

## See also

- HF: [`sovthpaw/omnistep-12a3b`](https://huggingface.co/sovthpaw/omnistep-12a3b)
- [OmniStep concept](../concepts/omnistep.md)
- Blog: [`../../blog/the-omnistep-multimodal.md`](../../blog/the-omnistep-multimodal.md)
- Blog: [`../../blog/the-omni-family.md`](../../blog/the-omni-family.md) (where it fits in the family)
- Related: [OmniSenter 12B](./omnisenter-12b.md) · [Senter Ohm 32A8B](./senter-ohm-32a8b.md) · [OmniSenterStep](./omnisenterstep.md)
