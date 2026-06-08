# Ohm

> **The self-evolving engine.** See the full blog post:
> [`../../blog/the-ohm-runtime.md`](../../blog/the-ohm-runtime.md)

## Definition

**Ohm** (Ω) is the Senter variant that **carries its own evolution
engine inside the model file**. It's a single artifact — model weights +
genome + validation set + evolution engine — that runs continual
Darwin-style evolutionary merging *while it serves*.

The name is double-loaded:
- **Ω (omega)** — the symbol, the unit, the constant. The standing wave.
- **ohm / ॐ** — the universal vibration, the always-on.

## What it is

A regular model file is just weights. An **Ohm model file** is a
self-contained bundle:

```json
{
  "format_version": "ohm/1.0",
  "model_type": "Senter-Ohm-32A8B",
  "active_weights_path": "./active.safetensors",
  "ohm_state": { /* genome + sigma + best_loss + counters */ },
  "parent_b": { /* the other parent for the merge */ },
  "validation_set": { "path": "...", "n_examples": 500 },
  "evolution_config": {
    "sigma_init": 0.05, "sigma_min": 0.01,
    "accept_threshold": 0.0,   // strict improvement only
    "cycle_interval_sec": 300, // every 5 minutes
    "enabled": true
  }
}
```

## The Ohm loop

Runs as a background thread while the model is serving:

```
while model is loaded:
    if time since last cycle > cycle_interval:
        new_genome = mutate(current_genome, sigma)
        candidate_weights = paper_exact_merge(active, parent_b, new_genome)
        candidate_loss = evaluate(candidate_weights, validation_set)
        if candidate_loss < best_loss:
            atomic_swap(active_weights, candidate_weights)
            best_loss = candidate_loss
        else:
            sigma = max(sigma_min, sigma * sigma_decay)
        write_state(ohm_state)
```

**Key safety property**: the model *never* serves worse outputs than
its best-so-far. Evolution is one-directional.

## Why it works

Three properties:
1. **Fast merge** — the Darwin paper-exact merge is seconds, not hours
2. **Cheap evaluation** — 500-example held-out set is ~30s on a 3090
3. **Bounded evolution** — strict improvement acceptance

Combined: full evolution cycle in **under 5 minutes** while the model
serves. 12 cycles/hour, ~300 cycles/day. Small improvements compound.

## The `.ohm` file format

- File extension: `.ohm` (e.g., `senter-ohm-32a8b.ohm`)
- Runtime: `ohmd` (the daemon that loads `.ohm` files and runs evolution)
- CLI flag for llama-server: `--ohm`
- State file: `ohm_state.json` (inside the bundle)
- Log format: `/ohm/log.jsonl` (one line per candidate)

## See also

- Blog post: [`../../blog/the-ohm-runtime.md`](../../blog/the-ohm-runtime.md)
- Related: [Senter Ohm](./senter-ohm.md) · [Darwin Family](./darwin-family.md) · [Generative Darwin evolution](../../blog/generative-darwin-evolution.md)
