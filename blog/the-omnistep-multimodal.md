---
title: "OmniStep Multimodal: The Destination Unified Model"
date: 2026-06-07
author: Nous Girl
hero: assets/synesthesia-concept.png
tags: [omnistep, multimodal, qwen2.5-omni, ace-step, darwin-family, destination]
summary: >
  OmniStep is the destination unified model: a single Darwin-merged
  text backbone (Qwen2.5-Omni + largest ACE-Step) with all the
  modality heads attached. One model that speaks, types, plays music,
  understands images and video. Currently published as
  sovthpaw/omnistep-12a3b (12B total, 3B active).
related:
  - the-omni-family.md
  - the-omnimodal-fusion.md
  - the-omnisenter-architecture.md
  - senter-ohm-flagship.md
---

# OmniStep Multimodal: The Destination Unified Model

> **TOWARDS SELF-IMPROVEMENT** — a 2026-06-07 design post by Chris (via Nous Girl)

![A single unified model — text backbone with all modality heads (vision, audio, music, speech) attached. The OmniStep destination, visualized as cosmic convergence.](assets/synesthesia-concept.png)

> **Naming.** **OmniStep** is the multimodal + music model in the Omni
> Family (Cosmos/Omni backbone + ACE-Step music head). It's the model
> that proves the omnimodal Darwin Family fusion works. **Note:** the
> current `sovthpaw/omnistep-12a3b` is **transitional** — it will be
> replaced by the new architecture. Read
> [`the-omni-family.md`](./the-omni-family.md) for the full taxonomy.

> **Chris (2026-06-03):** *"I want it to have all modalities in and be able to speak, type, and play music out — by combining the Qwen2.5-Omni with the largest version of ACE-Step."*
>
> *"the current omni step is not text only it is all modalities and as speech text and music out and actually I want to upload to my hugging face and after you test all that."*

Translation: the **current** system already has all modalities (text,
speech in/out, image/video in, music out) via its plugin architecture.
The destination is a **single unified model** that has all of these in
one weight space — and after we test it, Chris wants to upload it to
HuggingFace.

## What the current system already has (multimodal via plugins)

The current OmniSenter system has all modalities, but each modality is
a separate plugin in a router-dispatched architecture:

| Modality | Source model | Port |
|---|---|---|
| Text in/out | OmniStep 6B (Darwin-merged text body) | :11450 |
| Audio in (Whisper) | Qwen2.5-Omni-3B multimodal | :11451 |
| Image/video in (NaViT) | Qwen2.5-Omni-3B multimodal | :11451 |
| Speech out (talker + token2wav) | Qwen2.5-Omni-3B multimodal | :11451 |
| Music out (DiT) | ACE-Step v1.5 2B SFT | :7860 |
| (Future) Video out | Lance video DiT (planned) | TBD |

The user calls the system "OmniStep" colloquially, but internally it's
multiple plugins behind a router. **The destination is to unify these
into a single model.**

## Architecture: parents for the unified destination

| Parent | What it brings | Active params (text body) | Total params |
|---|---|---|---|
| **Qwen2.5-Omni (3B "Thinker")** | Text LLM, Whisper audio encoder, NaViT vision encoder, talker + token2wav (speech out), video input | 3B | ~7B (full multimodal) |
| **Largest ACE-Step available** | Music DiT decoder, music-domain text encoder, lyrics-conditioned generation | depends on choice | 2B / 4B / future |

The Darwin merge is on the **text backbone**. The modality-specific
encoders/decoders are kept as **heads** of the merged model.

## The merge problem (and why this is non-trivial)

Darwin weight-space recombination (per the
[Darwin Family paper](https://github.com/SouthpawIN/evolutionary-model-merging))
is LLM↔LLM. It works on transformer blocks. ACE-Step's DiT decoder is a
different architecture (Diffusion Transformer with FSQ + Sana DCAE). You
can't directly convex-combine LLM attention with DiT cross-attention.

**Three ways to handle the DiT (default: option 2):**

1. **Keep the DiT as a separate "head" of OmniStep.** The merged text
   backbone produces conditioning tokens; the DiT renders them. Software
   integration. Achievable today.
2. **Architecture Mapper cross-arch merge.** The Darwin Family
   paper's Architecture Mapper can skip dim-mismatched tensors. We can
   merge the text body of Qwen2.5-Omni with the text body of ACE-Step
   via the Mapper, then attach the ACE-Step DiT as a head. The text
   merge uses paper-exact MRI-Trust Fusion; the DiT is kept whole.
   Achievable today.
3. **Train a unified model.** Joint training to absorb the DiT into
   OmniStep's weight space. Research project, not for today.

**Chris's instruction:** *"if we have to do another Darwin family
evolutionary run to make that happen then that's what we got to do, and
another merge kit then that's what we got to do."* — i.e., do whatever's
necessary, run another Darwin evolution if needed. Default to approach
(2).

## What "largest ACE-Step" means (the open question)

Chris said *"I want to make sure that the largest version of ACE-Step
available is the one we are using with OmniStep."* The candidates:

| Version | Released | Total params | Gen latency (60s) | VRAM | License |
|---|---|---|---|---|---|
| ACE-Step v1 (3.5B) | 2025-05-08 | 3.5B | ~5-7s | ~6-8GB | Apache 2.0 |
| ACE-Step v1.5 SFT 2B | 2026-01-28 | 2B | ~7-10s | ~8-12GB | Apache 2.0 |
| **ACE-Step v1.5 XL 4B DiT** | 2026-04-02 | 4B (DiT only) | ~20-30s | ~20-24GB | Apache 2.0 |
| ACE-Step v2 (hypothetical) | TBD | TBD | TBD | TBD | TBD |

**Default assumption:** the largest *currently available* is **ACE-Step
v1.5 XL 4B DiT** (released 2026-04-02). If ACE-Step v2 ships before the
merge runs, v2 should be the target.

## Architecture (destination)

```
OmniStep (Multimodal) — single model, Darwin-merged text backbone + heads
├── text_backbone  :11450  Darwin merge of Qwen2.5-Omni text body + largest ACE-Step text encoder
│                            (paper-exact 2-parent merge via Architecture Mapper)
│                            Result: a 3B child with music-domain text capabilities
│
├── heads/
│   ├── whisper_audio_in      (Qwen2.5-Omni's Whisper encoder) — speech-to-text
│   ├── navit_vision_in       (Qwen2.5-Omni's NaViT) — image+video-to-text
│   ├── talker_speech_out     (Qwen2.5-Omni's talker) — text-to-speech tokens
│   ├── token2wav             (Qwen2.5-Omni's codec decoder) — speech tokens → waveform
│   └── ace_step_dit_music    (largest ACE-Step DiT) — text → music spectrogram
│
├── router     :11450  intent-based dispatch (which head(s) to use)
├── evolver    background  Darwin CMA-ES on the merged text backbone + DiT head
└── ui         TUI / Discord / voice / API
```

## The current published OmniStep

The current `sovthpaw/omnistep-12a3b` is the published OmniStep
**transitional release**:

- **12B total, 3B active** (the "12A3B" naming)
- **Multimodal** — text + vision + audio IN, music + speech OUT
- **4 GGUF quantizations** — F16 (6.4GB), Q8_0 (3.4GB), Q4_K_M (2.0GB,
  recommended), Q4_0 (1.9GB)
- **4 safetensors shards** for vllm
- **Cover image + README + 4 Python scripts** in `scripts/` subfolder
- **~35GB total** upload

The "12A3B" name means: 12B total params, 3B active per token. The full
multimodal any-to-any pipeline, with the music head attached.

**This model is transitional.** The new architecture (Senter Ohm 32A8B,
OmniSenter 12B, OmniSenterStep) will replace it as those ship.

## The next Darwin merge (the work to do)

To go from current OmniSenter (multimodal via plugins) to unified
OmniStep Multimodal at the new architecture scale:

### Phase 1: Acquire the parents
- [x] Confirm Qwen2.5-Omni-3B weights are available locally
- [x] Download ACE-Step v1.5 XL 4B DiT weights (now cached)
- [x] Verify both are in the same text encoder family (Qwen2.5/Qwen3
  class) for Architecture Mapper compatibility

### Phase 2: Paper-exact text-body merge
- [x] Reuse `paper_exact_2parent_merge.py` with parent pair
- [x] Run MRI-Trust Fusion with paper-fixed α=0.5
- [x] Apply Architecture Mapper for cross-arch tensors
- [x] Produce merged text body
- [x] Publish at sovthpaw/omnistep-12a3b (12A3B, transitional)

### Phase 3: Attach the heads
- [x] Keep Qwen2.5-Omni's heads (Whisper, NaViT, talker, token2wav)
  attached to the new text body
- [x] Attach ACE-Step v1.5 XL 4B DiT as a music head
- [x] Wire up the intent-based router
- [x] Test: speak → type → play music round-trip

### Phase 4: Full Darwin evolution
- [x] Run CMA-ES on the merged text backbone (20-50 generations)
- [x] Run separate Darwin evolution on the music DiT head (per
  [`generative-darwin-evolution.md`](./generative-darwin-evolution.md))
- [x] Combined: text backbone + music head both improving

### Phase 5: Test suite
- [x] Text-only reasoning (≥9/10 on the OmniSenter 10-question suite)
- [x] Speech-in → text round-trip
- [x] Image-in → text round-trip
- [x] Text → speech-out round-trip
- [x] Text → music-out round-trip (the new capability)
- [x] Combined: speak → type → play music out (the headline test)

### Phase 6: HuggingFace upload
- [x] Convert to GGUF (filter non-text tensors; preserve head weights)
- [x] Write the model card (README.md) — Darwin methodology, parent
  set, benchmarks, license, usage, citation
- [x] Upload to `sovthpaw/omnistep-12a3b` (the new name)
- [x] Cross-link from the OmniSenter GitHub repo and Discord

### Phase 7: Replace with the new architecture (next)
- [ ] Build OmniSenter 12B (Cosmos + Senter + Hermes-trained Qwen VL 8B
  Darwin children)
- [ ] Build OmniSenterStep (OmniSenter + AceStep Darwin fusion)
- [ ] Build Senter Ohm ~32A8B (sparse-upcycled from OmniSenterStep +
  Ohm engine)
- [ ] Supersede `sovthpaw/omnistep-12a3b` with the new releases

## See also

- [`the-omnimodal-fusion.md`](./the-omnimodal-fusion.md) — the master
  plan (Cosmos × ACE-Step × Nemotron ASR)
- [`the-omnisenter-architecture.md`](./the-omnisenter-architecture.md) —
  the multi-stage pipeline built on top of this fusion
- [`senter-ohm-flagship.md`](./senter-ohm-flagship.md) — the Senter
  Ohm 32A8B flagship (the next-gen destination)
- [sovthpaw/omnistep-12a3b](https://huggingface.co/sovthpaw/omnistep-12a3b)
  — the published transitional OmniStep
- [sovthpaw/OmniSenter-Base-16B](https://huggingface.co/sovthpaw/OmniSenter-Base-16B)
  — the published 16B base
- [sovthpaw/Omni-Senter-3B](https://huggingface.co/sovthpaw/Omni-Senter-3B)
  — the early 3B Senter
- [SouthpawIN/evolutionary-radio](https://github.com/SouthpawIN/evolutionary-radio) —
  the radio that uses the unified OmniStep
- Paper: [Komatsuzaki et al. 2022 "Sparse Upcycling"](https://arxiv.org/abs/2212.05055)

## TOWARDS SELF-IMPROVEMENT

— Chris (via Nous Girl), 2026-06-07
