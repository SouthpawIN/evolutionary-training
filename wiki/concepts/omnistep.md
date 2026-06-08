# OmniStep

> **The multimodal + music model.** See the full blog post:
> [`../../blog/the-omnistep-multimodal.md`](../../blog/the-omnistep-multimodal.md)

## Definition

**OmniStep** is the destination unified model: a single Darwin-merged
text backbone (Qwen2.5-Omni + largest ACE-Step) with all the modality
heads attached. One model that speaks, types, plays music, understands
images and video.

The "Step" suffix is from the music lineage (ACE-Step).

## What it is

A paper-exact 2-parent Darwin merge of:
- **Qwen2.5-Omni-3B** (multimodal parent: text + Whisper audio encoder
  + NaViT vision encoder + talker + token2wav speech out)
- **ACE-Step v1.5 XL 4B DiT** (music parent: DiT decoder + music text
  encoder + lyrics-conditioned generation)

The Darwin merge is on the **text backbone**. The modality-specific
encoders/decoders are kept as **heads** of the merged model.

```
OmniStep (single model, Darwin-merged text backbone + heads)
├── text_backbone  Darwin merge of Qwen2.5-Omni + ACE-Step text encoders
├── heads/
│   ├── whisper_audio_in      (Qwen2.5-Omni's Whisper encoder)
│   ├── navit_vision_in       (Qwen2.5-Omni's NaViT)
│   ├── talker_speech_out     (Qwen2.5-Omni's talker)
│   ├── token2wav             (Qwen2.5-Omni's codec decoder)
│   └── ace_step_dit_music    (largest ACE-Step DiT)
├── router     intent-based dispatch
├── evolver    background Darwin CMA-ES
└── ui         TUI / Discord / voice / API
```

## Current published baseline (transitional)

[`sovthpaw/omnistep-12a3b`](https://huggingface.co/sovthpaw/omnistep-12a3b)
— 12A3B (12B total / 3B active), 4 GGUFs + 4 safetensors:
- F16 (6.4GB)
- Q8_0 (3.4GB)
- Q4_K_M (2.0GB) — recommended
- Q4_0 (1.9GB)

**This is transitional** — the new architecture's OmniStep will
eventually replace it.

## See also

- Blog post: [`../../blog/the-omnistep-multimodal.md`](../../blog/the-omnistep-multimodal.md)
- Related: [Omni](./omni.md) · [Omnimodal fusion](./omnimodal-fusion.md) · [Generative Darwin](../../blog/generative-darwin-evolution.md)
- HF: [`sovthpaw/omnistep-12a3b`](https://huggingface.co/sovthpaw/omnistep-12a3b)
- Repo: [`SouthpawIN/evolutionary-radio`](https://github.com/SouthpawIN/evolutionary-radio) (the music radio that uses OmniStep)
