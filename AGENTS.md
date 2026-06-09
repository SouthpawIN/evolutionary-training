# AGENTS.md — evolutionary-training

This file tells AI agents (Claude Code, OpenCode, Codex, future-me) how
to behave when working in the OmniSenter training repo.

## 🏗️ Architecture rule (2026-06-08, mandatory)

Every Omni model is built from these **four blocks** (always all four,
always):

1. **Cosmos** (multimodal base: text + image + video)
2. **Nemotron 0.6B streaming ASR** (low-latency speech input)
3. **the 8B SFT we're training** (agentic reasoning, tool use, notebook)
4. **upgraded ACE-Step** (music generation, audio rhythm)

**ACE-Step is not optional.** Every Omni model — Standard and Ohm
alike — includes the ACE-Step merge. Music is in the DNA.

**Model lineup (4 models, canonical naming 2026-06-08):**
- **OmniStep** (8B) — Cosmos + Nemotron ASR + ACE-Step + Agentic SFT. Multimodal+music+agentic, no self-evolution.
- **OmniStep Ohm** (8B + Ohm) — same as OmniStep, with the self-evolution engine bundled.
- **Senter** (32A8B MoE) — sparse-upcycled from OmniStep. The agentic flagship, no Ohm.
- **Senter Ohm** (32A8B + Ohm) — the **flagship**, with self-evolution.

**Naming rules (Chris 2026-06-08):**
- "**OmniSenter**" is the **project name** (umbrella). It is **NOT** a model name.
- "**Senter**" alone = the 32A8B MoE (no Ohm).
- "**Senter Ohm**" = the 32A8B + Ohm (flagship).
- "**OmniStep**" = the 8B (with ACE-Step + agentic).
- "**OmniStep Ohm**" = the 8B + Ohm.
- ~~"OmniSenter 12B"~~ / ~~"OmniSenterStep"~~ / ~~"OmniSenter Standard"~~ / ~~"OmniSenter Flagship"~~ → all **gone**. See `blog/the-omni-family.md` for the canonical naming.

**For Stage 2+ data prep:** ALWAYS include ACE-Step training data
(music corpus, beat-aligned captions, lyric-genre pairs). NEVER build
an Omni model without the ACE-Step merge.

## Project overview

The OmniSenter training pipeline. A 5-stage process that turns the 8B
SFT base into the Senter Ohm flagship:

1. **Stage 1 — Agentic SFT** (running): QLoRA on Qwen3-8B base with
   Hermes-3 + Nemotron data → 8B SFT block (the seed for OmniStep)
2. **Stage 2 — Evolutionary merge** (queued): Darwin merge of the 8B
   SFT + ACE-Step into OmniStep, plus 2 other variants
3. **Stage 3 — Sparse upcycle** (scripted): OmniStep → Senter 32A8B
4. **Stage 4 — YaRN** (recipe documented): 6.25x context extension to 256K
5. **Stage 5 — Wiring** (scaffolding built): plug-ins, notebook, pet, Senter core, Ohm engine for Senter Ohm

## Current state

**Stage 1 is running.** Training process:
- Command: `python3 scripts/train_omnisenter_sft_fixed.py --epochs 2 --batch-size 2 --gradient-accum 8 --lr 1e-4 --max-seq-len 4096 --verbose --output-dir training-output/omnisenter-sft-20260606_213858 --resume`
- Latest checkpoint: `training-output/omnisenter-sft-20260606_213858/checkpoint-1000/`
- Status: at step ~1000+ of 3954 (filtered from 4268 by removing 2,522 long agentic SWE trajectories)
- Loss: 0.3959 at step 1000, 0.357 at step 1450 (best so far)

## What you should NOT do

1. **Do not touch the running Stage 1 SFT.** It's in `training-output/omnisenter-sft-20260606_213858/`. Don't modify the training script, don't kill the process, don't change the data path. If you need to make changes, queue them for Stage 2.
2. **Do not commit model weights or checkpoints.** They're gitignored. The repo should stay small and reviewable.
3. **Do not auto-merge to master.** All changes go through PRs.

## What you SHOULD do

1. **Check training status** with `ps -p <PID> -o etime,pcpu,stat`
2. **Read the training log** at `logs/training_v3_<date>.log`
3. **Tail the trainer state** at `training-output/<run>/checkpoint-*/trainer_state.json`
4. **Use `--resume`** if restarting the training (auto-detects latest checkpoint)
5. **Validate the catalog** before pushing: `python3 -c "import yaml; yaml.safe_load(open('models/curated.yaml'))"`

## How to resume training

If the training crashes (silent GPU OOM, external kill, etc.):

```bash
cd ~/projects/evolutionary-training
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
    python3 scripts/train_omnisenter_sft_fixed.py \
        --epochs 2 --batch-size 2 --gradient-accum 8 --lr 1e-4 \
        --max-seq-len 4096 --verbose \
        --output-dir training-output/omnisenter-sft-20260606_213858 \
        --resume
```

The `--resume` flag finds the latest checkpoint in `--output-dir` and continues from there.

## Speed fixes (DO NOT apply to current run)

Per the original analysis, the training has these latent speed issues:
- `max_seq_len=4096` pads 86% of examples unnecessarily
- Missing `packing=True` 
- Missing `dataloader_num_workers`
- Missing `group_by_length`
- Using `attn_implementation="eager"` instead of `"sdpa"`

These fixes are queued for the Stage 2 variant runs. DO NOT apply them to Stage 1 — that would invalidate the resume.

## GPU state

The training uses both RTX 3090s (24GB each). Local model servers
(`llama-darwin`, `llama-apex`) are intentionally stopped during
training to free GPU memory. If you need to bring them back up:

```bash
systemctl --user start llama-darwin
systemctl --user start llama-apex
```

But be aware: this will OOM the training. Only do it if you've paused training.

## Companion repos

- **[evolutionary-model-merging](https://github.com/SouthpawIN/evolutionary-model-merging)** — Darwin Family weight-space recombination (Stage 2)
- **[multimodal-expansion](https://github.com/SouthpawIN/multimodal-expansion)** — sparse upcycle, mmproj configs (Stage 3)
- **[evolutionary-radio](https://github.com/SouthpawIN/evolutionary-radio)** — the radio upstream (Stage 5 plugin)
- **[nous-girl-agent](https://github.com/SouthpawIN/nous-girl-agent)** — the pet, the curator agent, the radio plug-in (Stage 5 wiring)
- **[personal site](https://southpawin.github.io/)** — the blog + project hub

## Critical files

- `scripts/train_omnisenter_sft_fixed.py` — Stage 1 training (DO NOT MODIFY during run)
- `scripts/omnisenter_ohm.py` — Ohm runtime (Stage 5)
- `wiki/concepts/` — concept docs (11 articles)
- `wiki/entities/` — entity pages (8 articles)
- `blog/` — public blog (13 posts, deployed at southpawin.github.io)
- `models/curated.yaml` — model catalog (referenced by the pet)
- `training-data/prepared/unified_sft_filtered.jsonl` — current training data

## Style

- "TOWARDS SELF-IMPROVEMENT" tagline for major doc headers
- Nous brand: monochrome + cosmic variant, retro manga, halftone grain
- Match the existing folder structure
