# APEX-MTP I-Compact — local speculative decode

> **Status:** ✅ local · **HF:** private · **Local port:** `:11401` (paired with Darwin-28B)

## Identity

| | |
|---|---|
| **Full name** | APEX-MTP I-Compact |
| **Type** | Speculative-decode draft model (Multi-Token Prediction) |
| **Use** | Paired with [Darwin-28B](./darwin-28b.md) for fast inference |
| **GPU** | 1 (paired with Darwin-28B on GPU 0) |

## What it is

The local MTP (Multi-Token Prediction) speculative-decode partner for
Darwin-28B. While Darwin-28B runs on GPU 0 doing the heavy lifting,
APEX-MTP runs on GPU 1 predicting multiple tokens ahead, which the
verifier then accepts/rejects in batch. Net effect: faster inference on
the dual 3090s without losing quality.

## See also

- Related: [Darwin-28B](./darwin-28b.md)
- Local server: `~/projects/LLM-Infra/southpaw-turbohaul/`
- Skill: `mlops/local-llm-infra`
