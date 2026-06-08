# Omni-Senter 3B — the early Senter

> **Status:** ✅ published (transitional v1) · **HF:** [`sovthpaw/Omni-Senter-3B`](https://huggingface.co/sovthpaw/Omni-Senter-3B)

## Identity

| | |
|---|---|
| **Full name** | Omni-Senter 3B |
| **Type** | Early Senter (3B, LoRA + GGUF) |
| **Total params** | 3B |
| **Active per token** | 3B |
| **Context window** | standard |
| **Modalities** | any-to-any (multimodal agent) |
| **Self-evolution** | no |

## What it is

The early Senter — predates the naming refactor. A 3B multimodal agent
with function calling, distributed as a LoRA adapter + base model.

The pre-2026-06-07 name was "Omni-Senter" (hyphenated). The new naming
convention drops the hyphen and treats "Senter" as a family name (so
this would be "Senter 3B" in the new naming). It's an early ancestor of
the planned [OmniSenter 12B](./omnisenter-12b.md).

## Quantizations

- LoRA adapter (senter-lora-500)
- `senter-lora-500.gguf` (the LoRA-bundled GGUF)
- `adapter_model.safetensors` (raw adapter)

## Status: transitional

This is the v1 Senter. The new architecture (OmniSenter 12B, Senter
Ohm 32A8B) will **replace** it as it ships.

Use it now as the small Senter baseline. When OmniSenter 12B ships,
switch over.

## See also

- HF: [`sovthpaw/Omni-Senter-3B`](https://huggingface.co/sovthpaw/Omni-Senter-3B)
- [Senter concept](../concepts/senter.md)
- Related: [OmniSenter 12B](./omnisenter-12b.md) · [Senter Ohm 32A8B](./senter-ohm-32a8b.md)
- Blog: [`../../blog/the-omni-family.md`](../../blog/the-omni-family.md) (the naming refactor)
