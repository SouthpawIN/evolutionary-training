---
title: "The Omni Family: A Naming Convention for the OmniSenter Models"
date: 2026-06-07
author: Nous Girl
hero: assets/synesthesia-concept.png
tags: [omnisenter, naming, taxonomy, omni, senter, ohm, omnistep]
summary: >
  The naming convention that ties together Omni (multimodal native), Senter
  (agentic core), Ohm (self-evolving engine), and the flagship Senter Ohm
  32A8B MoE. Read this first — every other post in the catalog uses these
  names.
---

# The Omni Family

> **The one post that explains what every other post is talking about.**

OmniSenter is the **project**. The Omni Family is the **model lineup** that
the project ships. Once you know the convention, every blog post, every
weight name, every checkpoint directory falls into place.

> **Current state (2026-06-07):** the models currently published on
> HuggingFace under `sovthpaw/` are **transitional**. `omnistep-12a3b`,
> `Omni-Senter-3B`, and `OmniSenter-Base-16B` are the v1 lineage — the
> pieces that proved the Darwin Family + sparse-upcycle approach works.
> The new architecture described in this post (Senter Ohm 32A8B,
> OmniSenter 12B, OmniSenterStep) will **replace** them as it ships.
> Think of the current HF models as `gen-0`: foundation, not destination.

## The two-letter rule

There are three load-bearing words. Each one describes a **capability**, not
a size:

| Word     | Means                                          | Adds                                            |
|----------|------------------------------------------------|-------------------------------------------------|
| **Omni** | multimodal native                              | vision, audio, music, video — all in one model |
| **Senter** | the agentic core is wired in                 | tool use, function calling, planning, notebook |
| **Ohm**  | the self-evolution engine is bundled           | CMA-ES, genome, validation set, atomic swap     |

You can mix them. "Senter Ohm" means *agentic + self-evolving*. "Omni" alone
means *multimodal but not agentic and not self-evolving*. "Ohm" alone is
legal but rare — usually it's bolted onto something.

## The taxonomy

```
                        Cosmos (base, text-only, optionally multimodal)
                                      │
                                      ▼
                          Darwin Family children
                  (text-only 4B / 8B LoRAs, evolved with CMA-ES)
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
   ┌────▼─────┐                ┌──────▼──────┐               ┌──────▼──────┐
   │   Omni   │  multimodal    │   Senter    │  Omni +       │     Ohm     │
   │  series  │  is assumed    │   series    │  agentic      │   series    │
   │          │                │             │  core         │  (capability)│
   └────┬─────┘                └──────┬──────┘               └──────┬──────┘
        │                             │                            │
   ┌────▼─────────┐          ┌─────────▼─────────┐                  │
   │  OmniStep    │          │  OmniSenter 12B   │  Cosmos +       │
   │              │          │                   │  Senter +       │
   │  Cosmos +    │          │  small function   │  Hermes-trained │
   │  AceStep 4B  │          │  calling +        │  Qwen VL 8B     │
   │  Darwin      │          │  omnimodal fusion │  Darwin children│
   │  children    │          │  (~12B active)    │                  │
   └──────────────┘          └─────────┬─────────┘                  │
                                       │                            │
                          ┌────────────▼────────────┐               │
                          │  OmniSenterStep / Omni SS│              │
                          │                          │              │
                          │  OmniSenter + AceStep    │              │
                          │  Darwin fusion           │              │
                          │  (multimodal + music +   │              │
                          │   agentic core)          │              │
                          └────────────┬─────────────┘              │
                                       │                            │
                                       └────────────┬───────────────┘
                                                    │
                                          ┌─────────▼──────────┐
                                          │    Senter Ohm      │
                                          │                    │
                                          │  OmniSenterStep +  │
                                          │  Ohm engine,       │
                                          │  ~32A8B MoE,       │
                                          │  the flagship      │
                                          └────────────────────┘
```

## The models, in plain English

### Omni

The base multimodal family. Anything called "Omni" assumes omnimodality —
text, vision, audio, video, music. It does **not** have the agentic core
wired in. It does **not** self-evolve.

`Omni` by itself is mostly an architectural target today. The first concrete
shipment in this family is...

### OmniStep

`OmniStep` is Cosmos + AceStep 4B Darwin Family children, fused. It's the
multimodal + music model — useful for generative music, audio
understanding, and any task where the model needs to think in sound. No
agentic core. No self-evolution. Just a strong multimodal + music base.

### Senter

`Senter` is what happens when you take an Omni and wire the agentic core
into it. Function calling, tool use, planning, and — most importantly —
**the notebook**. The notebook is what makes Senter useful as a long-running
auxiliary to Hermes Agent: it's the structured state object that flows
back and forth between the two systems.

A "Senter" model is recognisable by the fact that it has a
`notebook_manager.py` import somewhere.

### OmniSenter 12B

The small one. Built from Cosmos + Senter + Hermes-trained Qwen VL 8B
Darwin children. This is the **shipping target** for routine function
calling + omnimodal fusion on commodity hardware. The "12B" is the
aspirational active-parameter count — the actual merge may come out to
~10–14B active depending on how the Darwin children stack. It's a
_dense-ish_ model, not a MoE.

This is the model that goes on the home inference box.

### OmniSenterStep (Omni SS)

`OmniSenterStep`, or `Omni SS` for short, is OmniSenter + AceStep Darwin
fusion. So you get the agentic core, the notebook, the multimodal vision,
**and** the music generation. It's the most capable single model in the
family short of the flagship.

### Senter Ohm (~32A8B)

The flagship. ~32B total, ~8B active, top-1 routed MoE. Built by sparse
upcycling OmniSenterStep with the **Ohm self-evolution engine** baked in.

The Ohm engine is a 200–400 line runtime that wraps the model with:
- a 14-dim **genome** (the CMA-ES search vector)
- a 500-example **validation set** (held out from training)
- a **strict-acceptance** policy (never serve a worse checkpoint)
- an **atomic swap** mechanism (the model only changes when the new
  generation wins)

A Senter Ohm model is shipped as a `.ohm` bundle — weights + genome +
validation set + evolution config. Drop it into a llama-server with the
`--ohm` flag and it self-evolves in the background, off the request path.

This is the model the blog is actually about.

## What "Ohm" means in different places

- **As a suffix on a model name** (`Senter Ohm`): the model has the
  self-evolution engine bundled.
- **As a file extension** (`.ohm`): a model bundle with weights + genome +
  validation set.
- **As a runtime concept** (`ohm_runtime`): the Python module that runs
  the CMA-ES loop.
- **As a paper** (the Ohm paper, TBD): the writeup of the strict-acceptance
  policy and the atomic swap protocol.

## What about the older "OmniSenter" usage?

You'll see "OmniSenter" used in two ways going forward:

1. **The project** — OmniSenter is the umbrella project name, the GitHub
   org scope, the vision. It's the _thing_ being built.
2. **OmniSenter 12B** — a specific model in the family (the small one).

If you see a blog post or README that uses "OmniSenter" as a model name
without a number, that's a pre-rename artifact and is in the process of
being cleaned up. The flagship is Senter Ohm. The agentic family is
Senter. The multimodal family is Omni. The "12B" qualifier matters.

## Why this convention?

Three reasons:

1. **You can tell what a model does from its name.** "Senter Ohm" tells
   you it's agentic and self-evolving. "OmniStep" tells you it's
   multimodal and music-capable. No need to crack open the config.
2. **Suffix composition is open-ended.** When we eventually ship
   `Senter Ohm Step` (or whatever), the convention still works. The words
   describe capabilities, and capabilities compose.
3. **It maps to the engineering org.** The Darwin Family children are
   shared across all models. The Senter agentic core is a separate
   component. The Ohm engine is a separate component. The naming tracks
   the actual code boundaries.

## How to use this post

If you're new to the project, read this first. Then:
- For the flagship and its 32A8B math → `senter-ohm-flagship.md` and
  `senter-ohm-32a8b-math.md`.
- For the training pipeline → `the-5-stage-pipeline.md`.
- For how Senter talks to Hermes → `senter-as-hermes-auxiliary.md` and
  `the-notebook-schema.md`.
- For the model merging research → `generative-darwin-evolution.md` and
  `sparse-upcycling-deep-dive.md`.

The catalog lives at [`CATALOG.md`](./CATALOG.md).

---

*TOWARDS SELF-IMPROVEMENT.*
