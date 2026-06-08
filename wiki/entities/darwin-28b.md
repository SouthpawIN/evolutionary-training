# Darwin-28B — local Q4_K_M

> **Status:** ✅ local · **HF:** private · **Local port:** `:11401`

## Identity

| | |
|---|---|
| **Full name** | Darwin-28B (Q4_K_M) |
| **Type** | Local dense model (Darwin-merged) |
| **Total params** | 28B |
| **Active per token** | 28B (dense) |
| **Quantization** | Q4_K_M |
| **Disk** | ~16-18GB |
| **VRAM** | ~18-20GB (1× RTX 3090) |

## What it is

One of the local Darwin-merged dense models that runs on the dual
RTX 3090 rig. The specific 28B configuration is part of the
Southpaw-models lineup (see [local server infra](#) for the full
inventory).

## Local use

- **Server**: llama-server on `:11401`
- **Profile**: `sovthpaw` Hermes profile uses it as one of the model
  options
- **Use case**: when you need a 28B-class model for local reasoning,
  Darwin-28B is the default

## See also

- Related: [APEX-MTP I-Compact](./apex-mtp.md) (the speculative-decode
  partner on GPU 1)
- Local server: `~/projects/LLM-Infra/southpaw-turbohaul/`
- Blog: [`../../blog/the-omni-family.md`](../../blog/the-omni-family.md)
  (for the broader family context)
