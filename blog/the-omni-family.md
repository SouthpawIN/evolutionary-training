---
title: "The Omni Family: A Naming Convention for the OmniSenter Models"
date: 2026-06-07
author: Nous Girl
hero: assets/synesthesia-concept.png
tags: [omnisenter, naming, taxonomy, omni, senter, ohm, omnistep, acestep, cosmos, nemotron]
summary: >
  The naming convention that ties together Omni (multimodal native), Senter
  (agentic core), Ohm (self-evolving engine), and the flagship OmniSenter
  32A8B. Read this first — every other post in the catalog uses these
  names.
---

# The Omni Family

> **The one post that explains what every other post is talking about.**

OmniSenter is the **project**. The Omni Family is the **model lineup** that
the project ships. Once you know the convention, every blog post, every
weight name, every checkpoint directory falls into place.

> **Architecture rule (2026-06-08):** every Omni model is built from
> **Cosmos + Nemotron 0.6B streaming ASR + the 8B SFT we're training
> + upgraded ACE-Step.** That last one is mandatory. Every Omni model,
> Standard and Ohm alike, includes the ACE-Step merge. Music is in the
> DNA, not a bolt-on.

> **Current state (2026-06-07 → 2026-06-08):** the models currently
> published on HuggingFace under `sovthpaw/` are **transitional**.
> `omnistep-12a3b`, `Omni-Senter-3B`, and `OmniSenter-Base-16B` are the
> v1 lineage — pieces that proved the Darwin Family + sparse-upcycle
> approach works. The new architecture described in this post
> (OmniStep, OmniSenter 32A8B, in Standard + Ohm variants) **replaces**
> them as it ships. Think of the current HF models as `gen-0`:
> foundation, not destination.

## The two-letter rule

There are three load-bearing words. Each one describes a **capability**, not
a size:

| Word        | Means                              | Adds                                                  |
|-------------|------------------------------------|-------------------------------------------------------|
| **Omni**    | multimodal native                  | vision, audio, music, video — all in one model        |
| **Senter**  | the agentic core is wired in       | tool use, function calling, planning, notebook       |
| **Ohm**     | the self-evolution engine is bundled | CMA-ES, genome, validation set, atomic swap         |

You can mix them. "Senter Ohm" means *agentic + self-evolving*. "Omni"
alone means *multimodal but not agentic and not self-evolving*. "Ohm"
alone is legal but rare — usually it's bolted onto something.

## The build blocks

Every Omni model is a **Darwin merge of these four**:

| Block                              | What it gives you                                    | Size        |
|------------------------------------|------------------------------------------------------|-------------|
| **Cosmos**                         | text + image + video base, world physics            | 15.75B      |
| **Nemotron 0.6B streaming ASR**    | low-latency speech input, voice activity detection  | 0.6B        |
| **8B SFT** (the one we're training) | agentic reasoning, tool use, notebook fluency      | 8B base + LoRA |
| **ACE-Step (upgraded)**            | music generation, audio rhythm, beat tracking        | 4B          |

All four are **always present**. The model size and capability differ by
how they're merged and what extra wiring is added.

## The taxonomy

```
            ┌─────────────────────────────────────────────────┐
            │         CORE STACK (always, in every Omni)     │
            │  Cosmos  +  Nemotron 0.6B ASR  +  8B SFT      │
            │  + upgraded ACE-Step                           │
            └────────────────────────┬────────────────────────┘
                                     │
                  ┌──────────────────┴──────────────────┐
                  │                                     │
            ┌─────▼─────┐                       ┌──────▼──────┐
            │ OmniStep  │                       │ OmniSenter  │
            │           │                       │  (32A8B)    │
            │  ~12B /   │                       │             │
            │  ~3B act  │                       │  32B-total  │
            │  dense    │                       │  8B-active  │
            │  MoE-lite │                       │  top-1 MoE  │
            │           │                       │             │
            │  cosm +   │                       │  OmniStep + │
            │  nemotron │                       │  Senter core│
            │  + ACE    │                       │  + sparse-  │
            │  + 8B     │                       │  upcycle to │
            │           │                       │  32B MoE    │
            └─────┬─────┘                       └──────┬──────┘
                  │                                     │
        ┌─────────┴────────┐                  ┌────────┴─────────┐
        │                  │                  │                  │
   ┌────▼──────┐      ┌────▼──────┐      ┌────▼──────┐     ┌────▼──────┐
   │ OmniStep  │      │ OmniStep  │      │ OmniSenter│     │ OmniSenter│
   │ Standard  │      │   Ohm     │      │ Standard  │     │   Ohm     │
   │           │      │           │      │           │     │  (flagship)│
   │ no self-  │      │ CMA-ES +  │      │ no self-  │     │ CMA-ES +  │
   │ evolution │      │ atomic    │      │ evolution │     │ atomic    │
   │           │      │ swap      │      │           │     │ swap      │
   └───────────┘      └───────────┘      └───────────┘     └───────────┘
```

**Two models. Two variants each. Four total.**

## The models, in plain English

### OmniStep

The smaller one. Cosmos + Nemotron 0.6B streaming ASR + the 8B SFT
+ upgraded ACE-Step, merged. **~12B total, ~3B active** in a MoE-lite
configuration.

What it does well:
- **Music generation** (ACE-Step is mandatory here)
- **Vision** (Cosmos backbone)
- **Streaming speech input** (Nemotron 0.6B ASR)
- **General agentic chat** (the 8B SFT, the one we're training)

What it does NOT have:
- The Senter agentic core (tool use at scale, notebook management)
- The Ohm self-evolution engine

It comes in two variants: **OmniStep Standard** and **OmniStep Ohm**.

### OmniSenter (the flagship)

The bigger one. Same four blocks (Cosmos + Nemotron ASR + 8B SFT +
ACE-Step), then **sparse-upcycled** to **~32B total / ~8B active** in
a top-1 routed MoE, with the **Senter agentic core** wired in.

What it does well:
- Everything OmniStep does, plus
- **Tool use, function calling, planning, notebook** (the Senter core)
- The full agentic experience, scaled up

It also comes in two variants: **OmniSenter Standard** and
**OmniSenter Ohm**.

### Standard vs Ohm

The **Standard** variant is the merged model. It doesn't change on its
own.

The **Ohm** variant is the merged model **+ the self-evolution engine
bundled**. That means:

- a 14-dim **genome** (the CMA-ES search vector)
- a 500-example **validation set** (held out from training)
- a **strict-acceptance** policy (never serve a worse checkpoint)
- an **atomic swap** mechanism (the model only changes when the new
  generation wins)

An Ohm model ships as a `.ohm` bundle — weights + genome + validation
set + evolution config. Drop it into a llama-server with the `--ohm`
flag and it self-evolves in the background, off the request path.

The Ohm engine is a 200–400 line runtime that wraps any of the four
Omni models. It's not exclusive to the flagship.

### What happened to "Senter Ohm 32A8B"?

That's the old name. **Senter Ohm 32A8B is now just OmniSenter Ohm.**
The "Senter" part is implicit — OmniSenter is always agentic. The
"Ohm" part is the variant suffix. The "32A8B" is the size in the
mathematical convention (32B total, 8B active). You'll see both names
in the docs; the new one is preferred.

## What "Ohm" means in different places

- **As a variant suffix** (`OmniStep Ohm`, `OmniSenter Ohm`): the model
  has the self-evolution engine bundled.
- **As a file extension** (`.ohm`): a model bundle with weights + genome
  + validation set.
- **As a runtime concept** (`ohm_runtime`): the Python module that
  runs the CMA-ES loop.
- **As a paper** (the Ohm paper, TBD): the writeup of the
  strict-acceptance policy and the atomic swap protocol.

## Why this convention?

Three reasons:

1. **You can tell what a model does from its name.** "OmniSenter Ohm"
   tells you it's multimodal + agentic + self-evolving. No need to
   crack open the config.
2. **The capability suffix is open-ended.** When we eventually ship
   `OmniSenter Step Ohm` (a hypothetical future variant with extra
   stepping layers), the convention still works.
3. **It maps to the engineering org.** The four core blocks
   (Cosmos / Nemotron / 8B SFT / ACE-Step) are shared across all Omni
   models. The Senter agentic core is a separate component. The Ohm
   engine is a separate component. The naming tracks the actual code
   boundaries.

## What about the older "OmniSenter" usage?

You'll see "OmniSenter" used in three ways going forward:

1. **The project** — OmniSenter is the umbrella project name, the
   GitHub org scope, the vision. It's the _thing_ being built.
2. **OmniSenter Standard** — a specific model in the family (the
   flagship, no self-evolution).
3. **OmniSenter Ohm** — the flagship with the self-evolution engine.

If you see a blog post or README that uses "Senter Ohm" (without the
"Omni" prefix) or "OmniSenter" (without a variant suffix), that's a
pre-2026-06-08 artifact and is in the process of being cleaned up.
The current naming is **OmniStep Standard / OmniStep Ohm /
OmniSenter Standard / OmniSenter Ohm** — four models, two capabilities.

## How to use this post

If you're new to the project, read this first. Then:
- For the flagship and its 32A8B math → `senter-ohm-flagship.md` and
  `senter-ohm-32a8b-math.md` (note: the 32A8B math post is being
  retitled to `omnisenter-flagship-math.md` shortly).
- For the training pipeline → `the-5-stage-pipeline.md`.
- For how Senter talks to Hermes → `senter-as-hermes-auxiliary.md` and
  `the-notebook-schema.md`.
- For the model merging research → `generative-darwin-evolution.md` and
  `sparse-upcycling-deep-dive.md`.

The catalog lives at [`CATALOG.md`](./CATALOG.md).

---

*TOWARDS SELF-IMPROVEMENT.*
