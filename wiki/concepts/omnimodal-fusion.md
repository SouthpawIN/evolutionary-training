# Omnimodal Fusion

> **The three-component foundation.** See the full blog post:
> [`../../blog/the-omnimodal-fusion.md`](../../blog/the-omnimodal-fusion.md)

## Definition

**Omnimodal Fusion** is the master plan for fusing all modalities into a
single Darwin Family model. It composes three component models:

| Component | Model | Size | Role |
|---|---|---|---|
| **Brain** | Cosmos3-Nano | ~8B | Multimodal reasoning, video, vision |
| **Music** | ACE-Step v1.5 XL SFT | 4B | Music generation (DiT) |
| **Speech** | Nemotron ASR Streaming | 0.6B | Speech-to-text + orchestration conductor |

## The diagram

```
┌──────────────────────────────────────────────────────────┐
│                   OMNIMODAL FUSION                       │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Cosmos3-Nano │  │ ACE-Step 4B  │  │ Nemotron ASR  │  │
│  │  (multimodal  │  │ (music gen)  │  │  0.6B (STS)   │  │
│  │   reasoning)  │  │              │  │               │  │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘  │
│         │                 │                   │          │
│         └─────────┬───────┴───────────────────┘          │
│                   ▼                                      │
│         Darwin Family Merge                              │
│                   │                                      │
│                   ▼                                      │
│         Omnimodal Base Model                             │
│         (speech in, text out, music out, video out)      │
│                   │                                      │
│                   ×                                      │
│         Omni Base 16B                                    │
│                   │                                      │
│                   ▼                                      │
│         FINAL SENTER (or SENTER OHM, or OMNISTEP)         │
└──────────────────────────────────────────────────────────┘
```

## Nemotron ASR 0.6B (the conductor)

Source: `nvidia/nemotron-3.5-asr-streaming-0.6b` (released 2026-06-04)

- **Architecture**: 24-layer Cache-Aware FastConformer encoder + RNNT
  decoder
- **Size**: 600M params
- **Languages**: 40 language-locales (19 production-ready)
- **Key features**: Native streaming (80-1120ms chunks), punctuation +
  capitalization built-in

The ASR is the **conductor** — always listening, aware of all modalities,
can redirect (e.g., "stop the music" → signal to ACE-Step), reports on
system state.

## Darwin merge strategy

- **Cosmos3-Nano × ACE-Step** — works (text encoder shares Qwen3
  skeleton, Architecture Mapper handles dim mismatches)
- **Cosmos3-Nano × Nemotron ASR** — does NOT work directly (architecture
  mismatch). Options:
  - Option A: Plugin attachment (ASR feeds text into the fused stream)
  - Option B: Encoder distillation (distill ASR into a transformer
    encoder, then merge)
  - Option C: Context-passing bridge (ASR runs alongside, passes
    tokens via learned projection)

## What this enables

Every model in the Omni Family is built on this fusion:
- **Omni** series (multimodal native) — uses the fusion as the base
- **OmniStep** (multimodal + music) — uses Cosmos × ACE-Step specifically
- **Senter** (agentic) — adds the notebook + function calling
- **Senter Ohm** (flagship) — adds the sparse upcycle + Ohm engine

## See also

- Blog post: [`../../blog/the-omnimodal-fusion.md`](../../blog/the-omnimodal-fusion.md)
- Related: [OmniStep](./omnistep.md) · [OmniSenter](./omnisenter.md) · [Darwin Family](./darwin-family.md)
