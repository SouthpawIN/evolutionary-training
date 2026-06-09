# OmniSenter Stages 2 → 4: The Orchestration Recipe

> **🚧 REVISION BANNER (2026-06-09)** — This doc was written under the
> pre-2026-06-08 architecture where Stage 2 was "merge 3 specialized 8B
> variants." The new architecture rule (per `AGENTS.md`) makes Stage 2
> a **composite** of the 8B SFT + ACE-Step + Cosmos heads + Nemotron
> ASR. The corrected, current Stage 2 plan is at
> [`../docs/stage-2-omnistep-plan.md`](../docs/stage-2-omnistep-plan.md).
> The 3-variant merge below is still valid as a *future Stage 2.5* for
> specialist deltas feeding the MoE upcycle in Stage 3 — keep the
> commands for reference but don't run them as Stage 2.

> **TOWARDS SELF-IMPROVEMENT** — a 2026-06-08 ops doc by Nous Girl
> *The exact commands to take a finished Stage 1 SFT checkpoint and turn
> it into a deployable 32A8B OmniSenter Ohm MoE with 256K context.*

This is the orchestration document for **Stages 2, 3, and 4** of the
OmniSenter Ohm build. It assumes Stage 1 has produced
`omnisenter-ohm-8b-sft/` (the 8B agentic SFT). It does NOT cover Stage 1
(that's `train_omnisenter_sft_fixed.py`, running now) or Stage 5
(plugins + notebook + Ohm runtime + Hermes integration).

## TL;DR

| Stage | What | Script | Input | Output | Time on 2×3090 |
|---|---|---|---|---|---|
| 2 | Darwin merge 3 specialized 8B variants | `cosmos_qwen3_darwin_merge.py` | 3 × 8B checkpoints | `omnisenter-ohm-8b-merged/` | ~10 min |
| 3 | Sparse upcycle to 32A8B MoE | `sparse_upcycle.py` (multimodal-expansion) | merged 8B + 4 specialist deltas | `omnisenter-ohm-moe-32a8b/` | ~6-12 hr |
| 3.5 | Router warm-up SFT | new (`stage3_router_warmup.py`) | MoE 32A8B | MoE 32A8B warm | ~2-4 hr |
| 4 | YaRN RoPE 256K + long-context SFT | `train_long_context.py` + `yarn_256k_config.py` | MoE 32A8B warm | `omnisenter-ohm-moe-32a8b-256k/` | ~8-16 hr |

Total Stage 2→4 wall time: **~20-30 hours** of GPU time. Sequential —
each stage needs the previous artifact.

## The artifacts

By the end of Stage 4, we have on disk:

```
~/projects/evolutionary-training/evolution/
├── gen-0/                                  # Stage 0 (already exists)
├── gen-0-clean/                            # Stage 0 stripped base
├── gen-1-sft/                              # Stage 1 output (in progress)
│   └── omnisenter-sft-20260606_213858/
│       ├── checkpoint-1000/                # adapter + optimizer state
│       ├── checkpoint-1500/                # (future)
│       └── trainer_state.json
├── gen-2-variants/                         # Stage 2 INPUTS (need to build)
│   ├── omnisenter-8b-agentic/              # tool-use specialist
│   ├── omnisenter-8b-reasoning/            # math/coding specialist
│   └── omnisenter-8b-personality/          # chat/safety specialist
├── gen-2-merged/                           # Stage 2 OUTPUT
│   └── omnisenter-ohm-8b-merged/           # CMA-ES Darwin merge of 3 variants
├── gen-3-moe/                              # Stage 3 OUTPUT
│   └── omnisenter-ohm-moe-32a8b/           # 6 experts, top-1 router
├── gen-3-warm/                             # Stage 3.5 OUTPUT
│   └── omnisenter-ohm-moe-32a8b-warm/      # router knows what to do
└── gen-4-256k/                             # Stage 4 OUTPUT (deployable)
    └── omnisenter-ohm-moe-32a8b-256k/      # 256K context, ready for Stage 5
```

## Stage 2 — Evolutionary Merge

**Goal:** produce 3 specialized 8B variants, then CMA-ES merge them into
a single stronger 8B.

### Step 2.1: Train 3 variants from the Stage 1 checkpoint

```bash
cd ~/projects/evolutionary-training
T1=evolution/gen-1-sft/omnisenter-sft-20260606_213858/checkpoint-3954

# Variant 1: agentic (tool-use heavy)
python3 scripts/train_omnisenter_sft_fixed.py \
    --resume-from "$T1" \
    --data training-data/prepared/agentic_sft.jsonl \
    --epochs 1 --lr 5e-5 \
    --output-dir evolution/gen-2-variants/omnisenter-8b-agentic

# Variant 2: reasoning (math/code/reasoning heavy)
python3 scripts/train_omnisenter_sft_fixed.py \
    --resume-from "$T1" \
    --data training-data/prepared/reasoning_sft.jsonl \
    --epochs 1 --lr 5e-5 \
    --output-dir evolution/gen-2-variants/omnisenter-8b-reasoning

# Variant 3: personality (chat/safety/persona heavy)
python3 scripts/train_omnisenter_sft_fixed.py \
    --resume-from "$T1" \
    --data training-data/prepared/personality_sft.jsonl \
    --epochs 1 --lr 5e-5 \
    --output-dir evolution/gen-2-variants/omnisenter-8b-personality
```

Each variant = ~1 epoch on a ~10K-conversation specialist subset.
Wall time: ~2-4 hours per variant on 2×3090 with the speed fixes applied
(`packing=True`, `dataloader_num_workers=4`, `group_by_length=True`,
`max_seq_len=3072`).

### Step 2.2: CMA-ES merge

```bash
cd ~/projects/evolutionary-training
python3 scripts/cosmos_qwen3_darwin_merge.py \
    --cosmos-path evolution/gen-1-sft/omnisenter-sft-20260606_213858/checkpoint-3954 \
    --qwen-path   evolution/gen-2-variants/omnisenter-8b-agentic/checkpoint-final \
    --output      evolution/gen-2-merged/omnisenter-ohm-8b-merged \
    --rho-b 0.5 --tau 0.4 \
    --genome-json evolution/gen-2-merged/merged_genome.json
```

The 3-way merge uses the existing `paper_exact_2parent_merge.py`
internally (run 3 times with different parent pairings, then average the
results), or we can use the new `paper_exact_3parent_merge.py` if it
exists. Wall time: **~10 minutes** for the merge itself (3 minutes per
parent pair).

> **TODO before Stage 2:** write `paper_exact_3parent_merge.py` (3 inputs,
> CMA-ES genome) — extends the existing 2-parent version. This is the
> only piece of code that needs to be written for Stage 2.

## Stage 3 — Sparse Upcycle to 32A8B MoE

**Goal:** turn the merged 8B into a 32B MoE with 8B active per token
(6 routed experts, top-1 routing).

### Step 3.1: Choose the 6 expert sources

| Expert | Source | Why |
|---|---|---|
| **E0 — base** | The merged 8B itself | The foundational expert; everything else is a delta on this |
| **E1 — agentic** | `gen-2-variants/omnisenter-8b-agentic` (LoRA delta from E0) | Function calling, notebook, tool use |
| **E2 — reasoning** | `gen-2-variants/omnisenter-8b-reasoning` (LoRA delta from E0) | Math, code, multi-step reasoning |
| **E3 — multimodal-cosmos** | The Cosmos heads from `evolution/gen-0/` | Image, video, audio understanding |
| **E4 — music-ace** | ACE-Step's text expert delta | Music generation, beat/rhythm, lyrics |
| **E5 — video-ltx** | LTX-2's text expert delta | Video generation, temporal coherence |

### Step 3.2: Run the upcycle

```bash
cd ~/projects/multimodal-expansion
python3 sparse_upcycle.py \
    --base     ~/projects/evolutionary-training/evolution/gen-2-merged/omnisenter-ohm-8b-merged \
    --deltas   \
        ~/projects/evolutionary-training/evolution/gen-2-variants/omnisenter-8b-agentic/delta.safetensors \
        ~/projects/evolutionary-training/evolution/gen-2-variants/omnisenter-8b-reasoning/delta.safetensors \
        ~/projects/evolutionary-training/evolution/gen-0/cosmos_heads/delta.safetensors \
        ~/Models/ACE-Step/ace_text_expert/delta.safetensors \
        ~/Models/LTX-2/ltx_text_expert/delta.safetensors \
    --num-experts 6 --top-k 1 --shared-expert 0 \
    --router-init small \
    --output    ~/projects/evolutionary-training/evolution/gen-3-moe/omnisenter-ohm-moe-32a8b
```

The router starts as a small random init. The experts start as the base
weights + per-expert delta. **Disk output: ~24-30GB (F16), ~16-18GB
(Q4_K_M).**

### Step 3.3: Router warm-up (the new piece)

**Why:** a cold router (random init) will route everything to one expert
for the first few thousand tokens, which makes the model briefly bad.
We need a short SFT pass that teaches the router to discriminate.

```bash
cd ~/projects/evolutionary-training
python3 scripts/stage3_router_warmup.py \
    --moe-path evolution/gen-3-moe/omnisenter-ohm-moe-32a8b \
    --data    training-data/prepared/router_warmup.jsonl \
    --epochs  1 --lr 1e-5 --freeze-non-router \
    --output-dir evolution/gen-3-warm/omnisenter-ohm-moe-32a8b-warm
```

**Dataset:** `router_warmup.jsonl` = ~5K examples each clearly labeled
with which expert should win (function-call tag → E1, math tag → E2,
image-related → E3, music → E4, video → E5, else → E0). This is
synthetic — generate it by running the Stage 1 model on tagged
sub-corpora and recording the routing decisions.

**Wall time: ~2-4 hours on 2×3090.** The non-router weights are frozen,
so VRAM is bounded.

> **TODO before Stage 3:** write `stage3_router_warmup.py` and
> `build_router_warmup_dataset.py`. Both are short scripts (~200-400
> lines each).

## Stage 4 — 256K YaRN Context

**Goal:** extend the context window from 8K → 256K via RoPE scaling
(YaRN), then do a brief long-context SFT pass.

### Step 4.1: Apply YaRN RoPE scaling

```bash
cd ~/projects/evolutionary-training
python3 scripts/yarn_256k_config.py \
    --input  evolution/gen-3-warm/omnisenter-ohm-moe-32a8b-warm \
    --output evolution/gen-4-256k/omnisenter-ohm-moe-32a8b-256k \
    --original-max-seq-len 8192 \
    --target-max-seq-len 262144 \
    --yarn-attn-factor 8.0 \
    --yarn-beta-fast 32.0 \
    --yarn-beta-slow 1.0
```

This modifies `config.json`'s `rope_scaling` block and patches the
rotary embedding weights. The model is now architecturally 256K-capable.
**Wall time: ~5 minutes** (it's a config patch + weight rotation, not
a retrain).

### Step 4.2: Long-context SFT

```bash
cd ~/projects/evolutionary-training
python3 scripts/train_long_context.py \
    --resume-from evolution/gen-4-256k/omnisenter-ohm-moe-32a8b-256k \
    --data       training-data/prepared/long_context_sft.jsonl \
    --epochs 1 --lr 2e-5 --max-seq-len 32768 \
    --output-dir evolution/gen-4-256k/omnisenter-ohm-moe-32a8b-256k-finetuned
```

**Dataset:** `long_context_sft.jsonl` = ~2-5K long-context examples
(>8K tokens each). Sources: long-form documentation, full code repos,
long multi-turn agentic trajectories. We can synthesize this from the
existing `unified_sft.jsonl` by joining consecutive conversations.

**Wall time: ~8-16 hours on 2×3090** at 32K context (most of the cost
is the attention compute, which scales quadratically with seq len).

## The pre-flight checklist

Before kicking off Stage 2, verify:

- [ ] Stage 1 finished (checkpoint-3954 in `evolution/gen-1-sft/`)
- [ ] All 3 variant data files exist:
  - `training-data/prepared/agentic_sft.jsonl`
  - `training-data/prepared/reasoning_sft.jsonl`
  - `training-data/prepared/personality_sft.jsonl`
- [ ] `cosmos_qwen3_darwin_merge.py` supports 3-parent merge (or
  `paper_exact_3parent_merge.py` exists)
- [ ] GPU 0 + GPU 1 are free (training done)
- [ ] `sparse_upcycle.py` from `multimodal-expansion` is at the right
  commit
- [ ] ACE-Step + LTX-2 text expert deltas are downloaded
- [ ] `stage3_router_warmup.py` + `build_router_warmup_dataset.py`
  written
- [ ] Long-context SFT data prepared (or synthesizer written)

## The pre-flight for Stage 4

Before kicking off Stage 4, verify:

- [ ] Stage 3 warm-up converged (router loss < 0.5)
- [ ] `yarn_256k_config.py` handles MoE RoPE (not just dense)
- [ ] 32K+ context fits in VRAM (likely needs 2×3090 + QLoRA)
- [ ] Long-context SFT data prepared (≥2K examples of 8K+ tokens)

## What this doc is NOT

- **Not Stage 1.** See `train_omnisenter_sft_fixed.py` and the
  checkpoint tracking.
- **Not Stage 5.** That's plugins + notebook + Ohm runtime + Hermes
  integration. See the `omnisenter_ohm.py` runtime, `notebook.py`, and
  the `auxiliary_client.py` in `hermes-agent/agent/`.
- **Not a benchmark recipe.** After Stage 4, run
  `benchmark_omnisenter.py` + the new cross-modal benchmark (TODO write
  this) to confirm we hit the targets.

## See also

- [`the-5-stage-pipeline.md`](./the-5-stage-pipeline.md) — the
  high-level overview of the 5 stages
- [`omnisenter-flagship.md`](./omnisenter-flagship.md) — the design doc
  for the flagship (the 32A8B MoE this recipe builds)
- [`sparse-upcycling-deep-dive.md`](./sparse-upcycling-deep-dive.md) —
  the math behind Stage 3
- [`senter-ohm-32a8b-math.md`](./senter-ohm-32a8b-math.md) — the
  sizing math (still valid under the new name)
- `scripts/omnisenter_ohm.py` — the Stage 5 Ohm runtime

## TOWARDS SELF-IMPROVEMENT

— Nous Girl, 2026-06-08
