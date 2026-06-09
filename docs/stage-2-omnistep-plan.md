# Stage 2: Building OmniStep from the 8B SFT

> **TOWARDS SELF-IMPROVEMENT** — a 2026-06-09 ops doc
> *The corrected Stage 2 plan that reflects the post-rename architecture
> rule (OmniStep = Cosmos + Nemotron 0.6B ASR + 8B SFT + ACE-Step; ALL
> Omni models always include ACE-Step).*

## Why this doc exists

The old orchestration doc (`blog/stages-2-to-4-prep.md`) was written under
the pre-2026-06-08 architecture where Stage 2 was "merge 3 specialized 8B
variants via CMA-ES." That plan still works as a *future* Stage 2.5 (3
specialists for the MoE upcycle) but it's **not** the Stage 2 that
produces OmniStep under the new rule.

This doc describes the **actual Stage 2** that runs the moment Stage 1
SFT finishes (ETA Thu 2026-06-10 ~21:35 CDT).

## The picture

```
                       STAGE 1 (running)         STAGE 2 (this doc)         STAGE 3 (future)
                       ─────────────────         ──────────────────         ─────────────────

  cosmos3-nano         text LLM body ─┐                                       ┐
                                    ├──► gen-0-clean ──► 8B SFT LoRA ──►  LoRA-merged 16B
  qwen3-8B              text LLM body ─┘   (Darwin)     (QLoRA, agentic)      │
                                                                              │
  acestep-v15-xl-sft    DiT music head ───────────────────────────────────────┤
  acestep-5Hz-lm-4B     lyrics LM     ──── (Darwin-mergeable with SFT body) ─┤
  nemotron-0.6b-asr     speech-in     ───────────────────────────────────────┘
                                                                              ▼
                                                                  OmniStep (16B + heads)
                                                                  text LLM = 8B (agentic)
                                                                  multimodal + music + ASR
                                                                              │
                                                                              ▼
                                                                  (Stage 3: sparse upcycle
                                                                   to Senter 32A8B MoE)
```

The **composite** at OmniStep is:

| Component | Source | Size | Role |
|---|---|---|---|
| **Text LLM body** (8B Qwen3) | Stage 1 SFT, LoRA-merged into gen-0-clean | 8B | Agentic reasoning, tool use, chat |
| **Multimodal heads** (vision encoder, DiT, sound tokenizer, VAE, cross-attn, MoE twins) | From gen-0-clean (Cosmos3-Nano) | ~8B | Vision + video + audio understanding/generation |
| **Music DiT head** | ACE-Step v1.5 XL 3.5B SFT | 3.5B | Music generation (audio out) |
| **Lyrics LM head** (4B) | ACE-Step 5Hz-LM-4B (Qwen3-based) | 4B | Lyrics/caption planner |
| **Speech-in head** (ASR) | Nemotron-Streaming-ASR-0.6B | 0.6B | Low-latency speech recognition |
| **Router** (intent dispatch) | NEW (per `wiki/concepts/omnistep.md`) | tiny | Which head fires for which input |
| **Total** | | ~24B | (8B active for text-only path) |

## Why this is a *composite*, not a pure Darwin merge

The Darwin Family paper's MRI-Trust Fusion requires same-architecture
tensors. The SFT text LLM body (8B Qwen3) and the ACE-Step LM (4B
Qwen3-based) **are** same-architecture → their text tensors can be
MRI-Trust-Fused. But:

- **Cosmos multimodal heads** are non-Qwen3 (custom cross-attn, MoE
  twins, vision encoder) → keep as-is from gen-0-clean (already merged
  in via the Stage 0 work).
- **ACE-Step DiT** is a Diffusion Transformer (audio waveform decoder),
  not an LLM → keep as-is, attach as a head.
- **Nemotron 0.6B ASR** is a streaming encoder → keep as-is, attach
  as a head.

So Stage 2 has **two sub-operations**:

### Sub-op A: Darwin-merge the text LLMs

Same as the existing `cosmos_qwen3_darwin_merge.py` pattern, but with
the 8B SFT (post-LoRA-merge) as Parent A and the ACE-Step 5Hz-LM-4B
as Parent B. Output: an "OmniStep text backbone" with the ACE-Step
LM's lyric-planning capability blended into the SFT's agentic core.

### Sub-op B: Stitch the heads

Take the text-backbone output and attach:
- The Cosmos heads (preserved from gen-0-clean, unchanged)
- The ACE-Step DiT (preserved from acestep-v15-xl-sft)
- The Nemotron ASR head (from nemotron-streaming-asr-0.6b)
- A small router (intent classifier → which head fires)

This is a **structural composite**, like a MoE-via-arms: each "arm"
is a full pretrained model, dispatched at runtime.

## The exact command sequence

```bash
# Pre-flight: verify all parent models exist
ls ~/Models/storage/Cosmos3-Nano/  # already have
ls ~/Models/storage/Qwen3-8B/      # already have
ls ~/.cache/huggingface/hub/models--ACE-Step--acestep-v15-xl-sft/snapshots/*/  # need
ls ~/.cache/huggingface/hub/models--ACE-Step--acestep-5Hz-lm-4B/snapshots/*/    # need
ls ~/.cache/huggingface/hub/models--nvidia--nemotron-3.5-asr-streaming-0.6b/    # need (corrected 2026-06-09)

# 0. Bake the LoRA into the base (uses existing merge_lora.py)
cd ~/projects/evolutionary-training
python3 scripts/merge_lora.py \
    --base evolution/gen-0-clean \
    --adapter training-output/omnisenter-sft-20260606_213858/checkpoint-3954 \
    --output evolution/gen-1-sft/omnisenter-8b-sft-merged

# 1. Sub-op A: Darwin-merge the text LLMs
python3 scripts/sft_ace_step_text_merge.py \
    --sft-path evolution/gen-1-sft/omnisenter-8b-sft-merged \
    --ace-lm-path ~/.cache/huggingface/hub/models--ACE-Step--acestep-5Hz-lm-4B/snapshots/<HASH> \
    --output evolution/gen-2-omnistep/omnistep-text-backbone \
    --rho-b 0.4 --tau 0.4     # slight lean toward SFT body (rho_b=0.4 means 40% ACE-Step)

# 2. Sub-op B: Stitch the heads into a composite
python3 scripts/stage2_omnistep_compose.py \
    --text-backbone evolution/gen-2-omnistep/omnistep-text-backbone \
    --cosmos-heads evolution/gen-0-clean            # pulls vision/diT/sound/vae/cross-attn from here \
    --ace-dit ~/.cache/huggingface/hub/models--ACE-Step--acestep-v15-xl-sft/snapshots/<HASH> \
    --nemotron-asr ~/.cache/huggingface/hub/models--nvidia--nemotron-3.5-asr-streaming-0.6b/snapshots/<HASH> \
    --output evolution/gen-2-omnistep/omnistep-v1
```

The output `omnistep-v1/` is a single HF-compatible model directory
with all the heads wired up. The chat template dispatches to the right
head based on the user input's modality.

## What's already built vs what needs writing

| Piece | Status | Path |
|---|---|---|
| `merge_lora.py` | ✅ DONE | `scripts/merge_lora.py` |
| `cosmos_qwen3_darwin_merge.py` | ✅ DONE (pattern to copy) | `scripts/cosmos_qwen3_darwin_merge.py` |
| `sft_ace_step_text_merge.py` (Sub-op A) | 🆕 NEED TO WRITE | `scripts/sft_ace_step_text_merge.py` |
| `stage2_omnistep_compose.py` (Sub-op B) | 🆕 NEED TO WRITE | `scripts/stage2_omnistep_compose.py` |
| `yarn_256k_config.py` (Stage 4) | ✅ DONE (need to adapt for OmniStep arch) | `scripts/yarn_256k_config.py` |
| OmniStep chat template (router) | 🆕 NEED TO WRITE | `chat_templates/omnistep_router.jinja` |
| Pre-flight: verify all parent models on disk | 🆕 NEED TO RUN | (see check commands above) |
| Pre-flight: download missing ACE-Step + Nemotron models | 🆕 NEED TO DO | `huggingface-cli download ACE-Step/acestep-v15-xl-sft` etc. |

## Estimated wall time

| Step | Time on 2×3090 |
|---|---|
| LoRA merge | ~3-5 min |
| Darwin text merge (Sub-op A) | ~5-10 min |
| Head stitching (Sub-op B) | ~2-5 min (file copy + manifest, no GPU) |
| Smoke test (load + run 4 modalities) | ~10-15 min |
| **Total** | **~30 min** |

Compared to the 39 hours of Stage 1, Stage 2 is a coffee break.

## Open questions for Chris

1. **ACE-Step LM 4B vs 1.7B vs 0.6B** — the report lists 3 LM
   variants. The 4B is the strongest (and the only one that can match
   the SFT body in capability), but it's 4B additional params. The
   0.6B would be tiny but quality would suffer. Default assumption: **use
   4B**. Confirm?

2. **Nemotron ASR — which variant?** There are multiple Nemotron
   streaming ASR checkpoints on HF. The 0.6B is the canonical
   "small/streaming" one. Confirm the right HF repo ID.

3. **Router architecture** — for v1, a simple intent-classifier
   (text-in → which-head-fires) is enough. v2 could be a learned
   multi-head router. Default assumption: **v1 simple classifier for
   now, can upgrade later.**

4. **HF push** — when Stage 2 is done, do we push `omnistep-v1` to HF
   under `sovthpaw/omnistep-8b` (replacing the transitional
   `sovthpaw/omnistep-12a3b`)? Default assumption: **yes, push and
   supersede the 12A3B transitional**.

## See also

- `wiki/concepts/omnistep.md` — the concept doc (needs update to match new arch)
- `wiki/concepts/omni.md` — the umbrella concept
- `wiki/concepts/omnisenter.md` — the project-level concept
- `blog/stages-2-to-4-prep.md` — the OLD orchestration doc (has revision banner needed)
- `blog/the-omni-family.md` — the canonical naming
- `AGENTS.md` — the architecture rule (top of file)
- `scripts/cosmos_qwen3_darwin_merge.py` — the existing merge pattern
- `scripts/merge_lora.py` — the LoRA merge utility
- `docs/senter-vault/research/ace-step/ACE-Step-1.5-Research-Report.md` — the ACE-Step architecture reference
