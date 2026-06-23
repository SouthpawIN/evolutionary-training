# OmniStep

> **The multimodal + music + agentic model.** Canonical architecture
> reference (2026-06-08+): `OmniStep = Cosmos + Nemotron 0.6B ASR + 8B
> agentic SFT + ACE-Step`. ALL Omni models always include ACE-Step —
> music is in the DNA.
>
> **Updated 2026-06-12:** New OmniStep is built via 3-way merge
> (SFT-merged Qwen3-8B + Cosmos3-Nano text body + ACE-Step attached
> modules). CMA-ES evolving 9 candidates. See Status section.

## Definition

**OmniStep** is the destination unified model: a single composite model
that handles text reasoning, agentic tool use, vision, video, audio
understanding, and music generation. The text LLM body is the 8B
agentic SFT (Qwen3-8B base, LoRA-merged into the Darwin-merged
gen-0-clean base). The other modalities attach as **heads** rather
than being merged into the text backbone (they have incompatible
architectures — DiT for music, streaming encoder for ASR, custom
cross-attn for Cosmos multimodal).

## The 4 mandatory build blocks

Per `evolutionary-training/AGENTS.md`, every Omni model includes all
four. Removing any of them is a violation of the architecture rule.

| Block | What | Source | Size | Role |
|---|---|---|---|---|
| 1. **Cosmos** | Multimodal encoder/decoder | NVIDIA Cosmos3-Nano | ~8B heads | Vision in/out, video, image, audio |
| 2. **Nemotron 0.6B** | Streaming ASR | NVIDIA Nemotron-Streaming-ASR-0.6B | 0.6B | Low-latency speech input |
| 3. **8B SFT** | Agentic text LLM | Stage 1 SFT (running) | 8B | Reasoning, tool use, chat, notebook |
| 4. **ACE-Step** | Music generation | ACE-Step v1.5 XL 3.5B SFT | 3.5B DiT + 4B LM | Music out (lyrics + audio) |

**Total:** ~24B parameters, **8B active** on the text-only path.

## Architecture

```
OmniStep (composite, runtime-routed)
├── text_backbone/        8B Qwen3 (agentic SFT)
│   ├── 36 transformer layers (Qwen3 arch)
│   ├── embed_tokens (151,936 vocab)
│   ├── lm_head
│   └── (LoRA-merged into gen-0-clean = Darwin text backbone)
│
├── heads/
│   ├── cosmos/           From Cosmos3-Nano (preserved from gen-0-clean)
│   │   ├── vision_encoder    (NaViT-style)
│   │   ├── cross_modal_attn  (add_q/k/v_proj + to_add_out, per layer)
│   │   ├── moe_gen_twins     (layers.*.mlp_moe_gen.*)
│   │   ├── modality_embed
│   │   ├── dit               (Diffusion Transformer for video/image gen)
│   │   ├── sound_tokenizer
│   │   └── vae
│   │
│   ├── ace_step_dit      Symlink → ACE-Step v1.5 XL 3.5B SFT
│   │                       (DiT music decoder, 50 diffusion steps)
│   │
│   ├── ace_step_lm       (FUTURE — Darwin-merged into text_backbone in Stage 2 Sub-op A)
│   │                       (5Hz-LM-4B Qwen3-based, lyrics/caption planner)
│   │
│   └── nemotron_asr      Symlink → Nemotron-Streaming-ASR-0.6B
│                           (CTC-based streaming speech recognizer)
│
├── router/               Intent classifier (v1: keyword match; v2: learned)
│   ├── text_only      → text_backbone
│   ├── vision_in      → heads/cosmos (vision_encoder)
│   ├── audio_in       → heads/nemotron_asr
│   ├── music_out      → heads/ace_step_dit
│   ├── video_out      → heads/cosmos (dit)
│   └── image_out      → heads/cosmos (dit)
│
└── evolver/              (Senter Ohm only — Darwin CMA-ES, background)
```

## Build process

Stage 2 (after Stage 1 SFT completes):

1. **Sub-op A** — `merge_lora.py` bakes the Stage 1 LoRA into
   `gen-0-clean` → `omnisenter-8b-sft-merged/` (the 8B agentic text body
   with full multimodal heads from gen-0-clean)
2. **Sub-op A** — `sft_ace_step_text_merge.py` Darwin-merges the text
   LLMs (SFT body × ACE-Step 5Hz-LM-4B) → `omnistep-text-backbone/`
3. **Sub-op B** — `stage2_omnistep_compose.py` stitches Cosmos heads,
   ACE-Step DiT, Nemotron ASR onto the text backbone →
   `omnistep-v1/` (the final composite)

Total Stage 2 wall time: ~30 min on 2×3090.


## Variants

| Variant | Has Ohm? | Use case |
|---|---|---|
| **OmniStep** (8B active) | no | Default local model, single-user |
| **OmniStep Ohm** (8B + Ohm) | yes | Self-evolution engine bundled |
| **Senter** (32A8B MoE) | no | Agentic flagship, sparse-upcycled from OmniStep |
| **Senter Ohm** (32A8B + Ohm) | yes | Flagship with self-evolution |

The "Step" suffix is from the music lineage (ACE-Step). All four
variants are **always multimodal + music + agentic**. The 8B ↔ 32A8B
distinction is about scale/specialization, not feature set.

## Current published baseline (transitional)

[`sovthpaw/omnistep-12a3b`](https://huggingface.co/sovthpaw/omnistep-12a3b)
— 12A3B (12B total / 3B active), 4 GGUFs + 4 safetensors:
- F16 (6.4GB)
- Q8_0 (3.4GB)
- Q4_K_M (2.0GB) — recommended
- Q4_0 (1.9GB)

**This is transitional** — the new architecture's OmniStep (above) will
eventually replace it. The transitional model is **not** multimodal +
music + agentic; it's a smaller MoE that does the multimodal basics
but lacks ACE-Step integration. The Stage 2 output will be the real
OmniStep.

## See also

- Blog (transitional, still relevant): [`../../blog/the-omnistep-multimodal.md`](../../blog/the-omnistep-multimodal.md)
- Family naming: [`../../blog/the-omni-family.md`](../../blog/the-omni-family.md)
- Related: [Omni[](../concepts/omni.md) · [Omnimodal fusion](./omnimodal-fusion.md) · [OmniSenter (project)](./omnisenter.md) · [Senter (32A8B MoE)[](../concepts/senter.md)
- HF (transitional): [`sovthpaw/omnistep-12a3b`](https://huggingface.co/sovthpaw/omnistep-12a3b)
- Repo (music radio that uses OmniStep): [`SouthpawIN/evolutionary-radio`](https://github.com/SouthpawIN/evolutionary-radio)
