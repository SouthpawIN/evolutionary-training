---
title: "The Ohm Runtime: The Self-Evolving Model File"
date: 2026-06-08
author: Nous Girl
hero: assets/images/synesthesia-concept.png
tags: [ohm, self-evolving, cma-es, darwin-family, continuous-evolution]
summary: >
  The Ohm runtime is what makes a Senter Ohm model a model that is
  always becoming. The .ohm file format embeds the model weights, the
  14-dim Darwin genome, a held-out validation set, and the evolution
  config into one self-contained bundle. The runtime runs a background
  CMA-ES loop while the model is serving, and the strict-acceptance
  policy means the model never serves worse outputs.
related:
  - the-omni-family.md
  - senter-ohm-flagship.md
  - senter-ohm-32a8b-math.md
---

> **Revised 2026-06-08 (naming).** The Ohm self-evolution engine attaches
> to **Senter Ohm** (the 32A8B flagship) and **OmniStep Ohm** (the 8B
> with self-evolution). It's a runtime, not a weight. See
> [`the-omni-family.md`](./the-omni-family.md) for the canonical 4-model
> lineup. Any reference in this post to "OmniSenter 12B" should be
> read as "Senter" (32A8B MoE, the agentic flagship without Ohm).

# The Ohm Runtime: The Self-Evolving Model File

> **TOWARDS SELF-IMPROVEMENT** — a 2026-06-07 design post by Chris (via Nous Girl)

![The Ohm file: model weights + genome + validation set + evolution engine, all bound together as one self-contained artifact. Cosmic convergence.](../assets/images/synesthesia-concept.png)

> **Naming.** "Ohm" (Ω) is the **self-evolution engine**. It can be
> bolted onto any model in the Senter family. The flagship that ships
> with the Ohm engine baked in is **Senter Ohm** (~32A8B MoE). Read
> [`the-omni-family.md`](./the-omni-family.md) for the full taxonomy.

> **Chris (2026-06-07):** *"it'll be a wild if we can get a continual evolutionary model merging just built into the model file so just runs automatically anyways just as long as this model is running it's constantly evolving... Senter Ohm"*

**Ohm** (Ω) is the Senter variant that **carries its own evolution engine
inside the model file**. It's a single artifact — model weights + genome +
validation set + evolution engine — that runs continual Darwin-style
evolutionary merging *while it serves*. As long as Ohm is loaded, it's
mutating, evaluating, and selecting better candidates in the background.
The user never sees worse outputs (rollback is automatic) and may see
gradually better ones.

The name is double-loaded:
- **Ω (omega)** — the symbol, the unit, the constant. The standing wave.
- **ohm / ॐ** — the universal vibration, the always-on.

## What it is (concretely)

A regular model file is just weights. An **Ohm model file** is a
self-contained bundle:

```json
{
  "format_version": "ohm/1.0",
  "model_type": "Senter-Ohm-32A8B",
  "active_weights_path": "./active.safetensors",
  "candidate_pool": "./candidates/",
  "ohm_state": {
    "genome": {
      "gamma": 0.5, "alpha_attn": 0.5, "alpha_ffn": 0.5,
      "alpha_emb": 0.5, "rho_a": 0.5, "rho_b": 0.5,
      "r0": 0.5, "r1": 0.5, "r2": 0.5, "r3": 0.5,
      "r4": 0.5, "r5": 0.5, "tau": 0.4, "lambda_reg": 0.01
    },
    "sigma": 0.05,
    "best_loss": 0.4333,
    "best_genome_id": "gen-0042",
    "candidates_evaluated": 4127,
    "improvements_accepted": 87,
    "improvements_rejected": 4040,
    "last_evaluation": "2026-06-07T19:14:23Z",
    "last_swap": "2026-06-07T17:42:11Z"
  },
  "parent_b": {
    "path": "senter-ohm-8b-sft-20260606_213858/",
    "name": "Senter-Ohm-8B-SFT-gen-0"
  },
  "validation_set": {
    "path": "./ohm_validation_v3.jsonl",
    "n_examples": 500,
    "description": "Held-out agentic + reasoning + multimodal examples"
  },
  "evolution_config": {
    "population_size": 4,
    "generations_per_cycle": 1,
    "sigma_init": 0.05,
    "sigma_min": 0.01,
    "sigma_decay": 0.995,
    "accept_threshold": 0.0,
    "max_concurrent_candidates": 2,
    "cycle_interval_sec": 300,
    "enabled": true
  }
}
```

The model file IS the engine. Load it with the right runtime, and the
runtime watches `ohm_state` and runs the evolution loop as a background
thread.

## How the Ohm loop runs (concretely)

The runtime (`ohmd`, or a `--ohm` flag in llama-server) does this
continuously while the model is serving:

```python
while model is loaded:
    if time_since_last_cycle > cycle_interval:
        # 1. Sample new genome (CMA-ES style)
        new_genome = mutate(current_genome, sigma)

        # 2. Generate candidate weights via merge formula
        candidate_weights = paper_exact_merge(
            active_weights, parent_b_weights, new_genome
        )

        # 3. Evaluate candidate on validation set
        candidate_loss = evaluate(candidate_weights, validation_set)

        # 4. Compare to best
        if candidate_loss < best_loss:
            atomic_swap(active_weights, candidate_weights)
            best_loss = candidate_loss
            log("accepted", new_genome, candidate_loss)
        else:
            log("rejected", new_genome, candidate_loss)

        # 5. Decay sigma (converge over time, but never to zero)
        sigma = max(sigma_min, sigma * sigma_decay)

        # 6. Update ohm_state
        write_state(ohm_state)
```

This runs as a background thread with a low CPU/VRAM budget. The
user-facing model is always the current `active_weights`. The candidate
generation is throttled (every 5 minutes by default) and the evaluation is
on a small fixed set (500 examples by default).

**Key safety property**: because we only accept strict improvements, the
model *never* serves worse outputs than its best-so-far. Evolution is
one-directional.

## What the Darwin merge formula looks like (the seed of evolution)

This is the part that makes Ohm cheap. The
[14-dim Darwin genome](https://github.com/SouthpawIN/evolutionary-model-merging)
is a small vector, and the merge is a fast linear combination:

```python
def paper_exact_merge(W_a, W_b, genome):
    """14-dim Darwin genome -> merged weight tensor."""
    γ       = genome['gamma']        # MRI-Trust attention weight
    α_attn  = genome['alpha_attn']   # attention vs FFN balance
    α_ffn   = genome['alpha_ffn']
    α_emb   = genome['alpha_emb']
    ρ_a     = genome['rho_a']        # rank reduction A
    ρ_b     = genome['rho_b']        # rank reduction B
    r0..r5  = [genome[f'r{i}'] for i in range(6)]  # per-tensor ratios
    τ       = genome['tau']          # MRI-vs-genome blend
    λ       = genome['lambda_reg']   # regularization

    # Architecture Mapper handles cross-arch tensors (skip if mismatched)
    W_merged = architecture_map(W_a, W_b) if shape_match(W_a, W_b) else W_a

    # MRI-Trust Fusion: trust-weighted linear combination
    r_mri = mri_trust(W_a, W_b, τ, λ)
    r_final = τ * r_mri + (1 - τ) * genome_ratios()

    return (1 - r_final) * W_a + r_final * W_b
```

This runs in **seconds per candidate** on a 3090, because the merge is a
few linear combinations. The whole Ohm loop — sample, generate, evaluate,
decide — runs in **under 5 minutes per cycle** at default config. So we
get ~12 evolution cycles per hour, ~300 per day, all while the model is
serving.

## How the candidate evaluation works

The evaluation set is small (500 examples) and **fixed** so loss is
comparable across candidates. The evaluation runs as a batched forward
pass with no gradient:

```python
@torch.no_grad()
def evaluate(weights, val_set, batch_size=8):
    model = load_with_weights(weights)
    losses = []
    for batch in chunked(val_set, batch_size):
        inputs = tokenize(batch)
        out = model(inputs, labels=inputs)
        losses.append(out.loss.item())
    return mean(losses)
```

For an 8B model on 500 examples with batch 8, evaluation takes ~30
seconds on a 3090. With the cycle interval of 5 minutes, evaluation is 10%
of the wall-clock budget. The rest of the time the model is serving users
normally.

## Why this works (the wild part)

Three properties make Ohm viable:

1. **Fast merge generation** — the Darwin paper-exact merge is a few
   linear combinations. Seconds, not hours.
2. **Cheap evaluation** — 500-example held-out set with no gradient is
   ~30s on a 3090.
3. **Bounded evolution** — strict improvement acceptance means the model
   never gets worse.

Combined: you can run a full evolution cycle in 5 minutes while the model
is serving. The user never notices the evolution. The model gets a tiny
bit better every cycle.

**And the gains compound.** A 0.001 loss improvement per cycle is nothing.
But 300 cycles a day × 365 days = 100K+ evaluations × 87 accepted =
thousands of accepted improvements. Over months, that's a meaningfully
better model. For free. While it serves.

## The validation set (the secret sauce)

The validation set is the key to Ohm's safety. It must be:
- **Fixed** (so loss is comparable across candidates)
- **Diverse** (representative of the model's actual use cases)
- **Held-out** (not in any training data)
- **Small enough to be fast** (~500 examples is the sweet spot)

For Senter, the validation set should include:
- Agentic examples (tool use, multi-turn, function calling)
- Reasoning examples (math, code, logic)
- Multimodal understanding (image, audio → text)
- Notebook-style retrieval (look up past context)
- Multimodal output (text → music, text → image, text → speech)

The validation set IS the model's quality bar. If a candidate improves on
it, it's better. Period. No debate.

## Boundedness and safety

Ohm is designed to be **safe by construction**:

| Property | How it's enforced |
|---|---|
| Model never serves worse outputs | Strict improvement acceptance (rollback if candidate is worse) |
| Evolution is local | Small genome mutations (sigma ≤ 0.05) |
| Evolution converges | Sigma decay each cycle (sigma_min = 0.01) |
| Evolution is auditable | Full `ohm_state` logged + written atomically |
| Evolution can be disabled | `evolution_config.enabled: false` flag |
| Candidate pool is capped | `max_concurrent_candidates: 2` |
| Evolution pauses on demand | Runtime exposes `pause_evolution()` API |

The model file is the **single source of truth** — you can always inspect
`ohm_state` to see exactly what the model has done. No black-box evolution.

## Connection to existing infrastructure

Ohm doesn't start from zero. It composes:

- `continuous_evolution.py` (in evolutionary-training) — already does the
  external loop
- `cma_es_evolution.py` (in evolutionary-model-merging) — already does
  CMA-ES
- `paper_exact_2parent_merge.py` (in evolutionary-model-merging) —
  already does the merge
- The `agentic_training_loop.py` patterns — evaluation infrastructure

What's NEW for Ohm:
1. The model file format (`.ohm`) with embedded genome + validation set
2. The runtime support (`ohmd` or llama-server `--ohm` flag) for
   in-process evolution
3. The atomic weight swap (with rollback)
4. The evolution audit log

This is a 200-400 line addition to the existing infrastructure, not a
from-scratch project.

## The "ohm" naming in code

- **Model file extension**: `.ohm` (e.g., `senter-ohm-32a8b.ohm`)
- **Runtime**: `ohmd` (the daemon that loads `.ohm` files and runs
  evolution)
- **CLI flag for llama-server**: `--ohm` (enables the in-process loop)
- **State file**: `ohm_state.json` (inside the `.ohm` bundle)
- **Log format**: `/ohm/log.jsonl` (one line per candidate,
  accepted/rejected)
- **The "ohm" call**: a debug command that prints the current evolution
  state

## Use cases (what Ohm is good for)

1. **Long-running services** — a chat service running 24/7 quietly gets
   better
2. **Personal assistants** — the assistant you use every day gets
   personalized to you via Ohm
3. **Edge deployments** — a model on a Jetson or Raspberry Pi that
   improves on-device
4. **Research agents** — an agent that gets better at its specific task
   the more it's used
5. **Distributed evolution** — multiple Ohm instances sharing `ohm_state`
   over the network

## What Ohm is NOT

- **Not AGI** — Ohm is bounded local evolution, not open-ended
  self-modification
- **Not safe to run unsupervised on critical systems** — even with
  rollback, the model is mutating. Use judgment.
- **Not a replacement for training** — Ohm is fine-tuning, not learning
  new capabilities
- **Not magic** — the gains are small per cycle. It takes weeks/months
  to see meaningful improvement.

## Open questions

1. **Genome persistence** — does `ohm_state` survive model restarts? (Yes,
   it's in the file, but the active weights are in safetensors)
2. **Distributed Ohm** — can multiple Ohm instances share state over a
   network? (Probably yes via a shared file or message queue)
3. **Ohm on top of MoE** — does the merge formula extend cleanly to the
   sparse-upcycled MoE? (Probably yes, with some adaptation)
4. **Genome expansion** — can the genome grow over time to include more
   axes of variation? (Yes, but slowly)
5. **Adversarial inputs** — if the validation set is poisoned, the model
   could be steered to a bad optimum. Mitigations: hash the val set,
   monitor for sudden improvement spikes.

## See also

- [`senter-ohm-flagship.md`](./senter-ohm-flagship.md) — the flagship
  overview, where the Ohm engine is the headline feature
- [`senter-ohm-32a8b-math.md`](./senter-ohm-32a8b-math.md) — the sizing
  math
- [`the-5-stage-pipeline.md`](./the-5-stage-pipeline.md) — where Ohm gets
  wired in (Stage 5)
- [`generative-darwin-evolution.md`](./generative-darwin-evolution.md) —
  extends the same CMA-ES + merge idea to DiT/audio heads
- Repo: [SouthpawIN/evolutionary-model-merging](https://github.com/SouthpawIN/evolutionary-model-merging)
  — the merge formula + CMA-ES implementation
- Repo: [SouthpawIN/evolutionary-training](https://github.com/SouthpawIN/evolutionary-training)
  — the `omnisenter_ohm.py` runtime
- Paper: [Komatsuzaki et al. 2022 "Sparse Upcycling"](https://arxiv.org/abs/2212.05055) —
  the MoE from dense pattern

## TOWARDS SELF-IMPROVEMENT

— Chris (via Nous Girl), 2026-06-07
