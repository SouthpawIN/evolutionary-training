---
title: "The Omni Family: A Naming Convention for OmniSenter"
date: 2026-06-08
author: Nous Girl
hero: assets/images/synesthesia-concept.png
tags: [omnisenter, naming, taxonomy, omni, senter, ohm, omnistep]
summary: >
  The naming convention for the 4 OmniSenter models. Four models, four
  names: OmniStep, OmniStep Ohm, Senter, Senter Ohm. Read this first —
  every other post in the catalog uses these names. *(Revised 2026-06-08
  from the 2026-06-07 version which had "OmniSenter 12B" and "OmniSenterStep"
  as model names — both gone now.)*
---

# The Omni Family

> **The one post that explains what every other post is talking about.**

OmniSenter is the **project**. The Omni Family is the **model lineup** that
the project ships. Once you know the convention, every blog post, every
weight name, every checkpoint directory falls into place.

> **2026-06-08 revision.** The 4-model lineup is now canonical:
>
> | Model | Size | Capabilities |
> |---|---|---|
> | **OmniStep** | 8B (active) | Cosmos + Nemotron ASR + ACE-Step + Agentic |
> | **OmniStep Ohm** | 8B + Ohm engine | same + self-evolution |
> | **Senter** | 32A8B MoE | agentic flagship, no Ohm |
> | **Senter Ohm** | 32A8B MoE + Ohm | the **flagship** with self-evolution |
>
> Previous names that are **gone**:
> - ~~"OmniSenter 12B"~~ → was a placeholder, replaced by **Senter** (32A8B MoE)
> - ~~"OmniSenterStep" / "Omni SS"~~ → replaced by **OmniStep** (8B)
> - ~~"OmniSenter Ohm"~~ → replaced by **Senter Ohm** (the flagship)
> - ~~"OmniSenter Standard" / "OmniSenter Flagship"~~ → all replaced
>
> **Every Omni model always includes all four blocks:** Cosmos (multimodal
> base) + Nemotron 0.6B streaming ASR + the agentic SFT (currently the
> 8B SFT we're training in Stage 1) + ACE-Step (music). The Ohm engine
> is optional (it's a runtime, not a weight). See
> [`AGENTS.md`](https://github.com/SouthpawIN/evolutionary-training) for
> the canonical training-pipeline naming.

## The two-letter rule

There are three load-bearing words. Each one describes a **capability**, not
a size:

| Word     | Means                                          | Adds                                            |
|----------|------------------------------------------------|-------------------------------------------------|
| **Omni** | multimodal native                              | vision, audio, music, video — all in one model |
| **Senter** | the agentic core is wired in                 | tool use, function calling, planning, notebook |
| **Ohm**  | the self-evolution engine is bundled           | CMA-ES, genome, validation set, atomic swap     |

You can mix them. "Senter Ohm" means *agentic + self-evolving*. "OmniStep"
means *multimodal + music + agentic* (the 8B). "OmniStep Ohm" means
*8B + self-evolution*. "Ohm" alone is legal but rare — usually it's bolted
onto something.

## The taxonomy (4 models)

```
                  Cosmos + Nemotron ASR + Agentic SFT + ACE-Step
                  (these four blocks are in every Omni model)
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
   OmniStep                      OmniStep Ohm                  Senter (32A8B MoE)
   8B active                     8B + Ohm engine              agentic flagship
   multimodal+music+                                        (no Ohm)
   agentic, no Ohm                       │                         │
                                         │                         │
                                         └────────┬────────────────┘
                                                  │
                                                  ▼
                                            Senter Ohm
                                       32A8B + Ohm engine
                                       THE FLAGSHIP
```

**Read this diagram bottom-up for the build order:**

1. **OmniStep** (8B) — the agentic SFT we're training right now,
   merged with Cosmos + ACE-Step text encoder. Multimodal+music+agentic
   in one 8B. The "small" model in the lineup.
2. **OmniStep Ohm** — same 8B + the Ohm self-evolution engine. The
   self-evolving 8B.
3. **Senter** (32A8B MoE) — the 32B MoE built by sparse-upcycling
   OmniStep. 8B active per token, 32B total. The "agentic flagship"
   without self-evolution.
4. **Senter Ohm** — Senter + the Ohm engine. **The flagship.** The
   32A8B MoE that self-evolves.

## The models, in plain English

### OmniStep

The 8B with **everything in it** (except Ohm): Cosmos for vision, Nemotron
0.6B for speech input, the agentic SFT for tool use + planning, ACE-Step
for music. It's the model that fits on a single 24GB GPU at 1M context
with the right offload config. Use it as: the **standalone** in the
local model server, the Evolution Radio's brain, the note-taker's brain.

**Recognition test:** a `Cosmos × ACE-Step` Darwin merge, then fine-tuned
with the agentic SFT data.

### OmniStep Ohm

OmniStep + the Ohm self-evolution engine. The 8B that gets better over
time. Same footprint as OmniStep, just with the evolution runtime
attached. Useful when the local model server is long-lived and you
want the model to keep improving without re-training.

**Recognition test:** same GGUF as OmniStep, plus a `.ohm` bundle
(genome + validation set + evolution config).

### Senter (32A8B MoE)

The **agentic flagship** (without self-evolution). 32B-total, 8B-active
per token, top-1 routed MoE. Built by sparse-upcycling OmniStep:
the FFN becomes 4 parallel experts + a router, and the active 8B
per token chooses which experts to fire.

Use Senter when the workload needs the **real** agentic heavyweight:
complex multi-step planning, large notebook, deep reasoning. This is
the model that goes on the **auxiliary** slot of Hermes Agent when
you're not skimping on inference budget.

**Recognition test:** a 32B-total MoE with 8B active per token, the
agents + notebook wired in, no Ohm engine.

### Senter Ohm (the flagship)

Senter + the Ohm self-evolution engine. **The flagship model.** 32A8B
that self-evolves. Use it when Senter is the daily driver AND you want
it to keep getting better.

The Ohm engine is a 200–400 line runtime that wraps the model with:
- a 14-dim **genome** (the CMA-ES search vector)
- a 500-example **validation set** (held out from training)
- a **strict-acceptance** policy (never serve a worse checkpoint)
- an **atomic swap** mechanism (the model only changes when the new
  generation wins)

A Senter Ohm model is shipped as a `.ohm` bundle — weights + genome +
validation set + evolution config. Drop it into a llama-server with the
`--ohm` flag and it self-evolves in the background, off the request path.

**This is the model the blog is actually about.**

## What "Ohm" means in different places

- **As a suffix on a model name** (`Senter Ohm`, `OmniStep Ohm`): the model
  has the self-evolution engine bundled.
- **As a file extension** (`.ohm`): a model bundle with weights + genome +
  validation set.
- **As a runtime concept** (`ohm_runtime`): the Python module that runs
  the CMA-ES loop.
- **As a paper** (the Ohm paper, TBD): the writeup of the strict-acceptance
  policy and the atomic swap protocol.

## The current state (2026-06-08)

The models currently published on HuggingFace under `sovthpaw/` are the
**v1 transitional** lineage:

- `sovthpaw/omnistep-12a3b` — 12B total / 3B active, transitional
  OmniStep baseline
- `sovthpaw/Omni-Senter-3B` — 3B early Senter (predecessor of Senter)
- `sovthpaw/OmniSenter-Base-16B` — 16B base, multimodal (predecessor
  of Senter 32A8B)

The Stage 1 SFT (8B agentic, in progress) is the seed for the new
**OmniStep** when merged with Cosmos + ACE-Step. The Stage 3 sparse
upcycle produces the new **Senter** (32A8B). Stage 5 wires in the
Ohm engine for **Senter Ohm**.

## How to use this post

If you're new to the project, read this first. Then:
- For the flagship and its 32A8B math → `senter-ohm-flagship.md` and
  `senter-ohm-32a8b-math.md`.
- For the training pipeline → `the-5-stage-pipeline.md` and
  `stages-2-to-4-prep.md`.
- For how Senter talks to Hermes → `senter-as-hermes-auxiliary.md` and
  `the-notebook-schema.md`.
- For the model merging research → `generative-darwin-evolution.md` and
  `sparse-upcycling-deep-dive.md`.

The catalog lives at [`CATALOG.md`](./CATALOG.md).

---

*TOWARDS SELF-IMPROVEMENT.*
