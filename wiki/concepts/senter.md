# Senter

> **The agentic family.** See the full blog post:
> [`../../blog/the-omni-family.md`](../../blog/the-omni-family.md)

## Definition

**Senter** is what happens when you take an [Omni](./omni.md) and wire
the **agentic core** into it. Function calling, tool use, planning, and
— most importantly — **the notebook**. The notebook is what makes
Senter useful as a long-running auxiliary to Hermes Agent: it's the
structured state object that flows back and forth between the two
systems.

A "Senter" model is recognisable by the fact that it has a
`notebook_manager.py` import somewhere.

## Members

### OmniSenter 12B

The small one. Built from Cosmos + Senter + Hermes-trained Qwen VL 8B
Darwin children. The **shipping target** for routine function calling
+ omnimodal fusion on commodity hardware. The "12B" is the aspirational
active-parameter count — the actual merge may come out to ~10-14B
active depending on how the Darwin children stack. It's a **dense-ish**
model, not a MoE.

- **Status**: planned (HF target: `sovthpaw/omnisenter-12b`)

### OmniSenterStep (Omni SS)

**OmniSenterStep**, or **Omni SS** for short, is OmniSenter + AceStep
Darwin fusion. So you get the agentic core, the notebook, the
multimodal vision, **and** the music generation. The most capable
single model in the family short of the flagship.

- **Status**: planned

### Senter Ohm (the flagship)

[`./senter-ohm.md`](./senter-ohm.md) — ~32B-total / 8B-active MoE with
the [Ohm](./ohm.md) self-evolution engine bundled in.

- **Status**: planned (HF target: `sovthpaw/senter-ohm-32a8b`)

## The notebook (the killer feature)

The notebook is the defining artifact of any Senter model. It's a
structured state object that flows between:

- Senter's internal reasoning (across turns)
- Senter and the user (across sessions, via the multimodal life-log)
- Senter and Hermes Agent (escalation handoff)

The 256K context window exists **for the notebook**. See
[`./notebook.md`](./notebook.md) for the full schema.

## See also

- Naming source-of-truth: [`../../blog/the-omni-family.md`](../../blog/the-omni-family.md)
- Blog post: [`../../blog/senter-as-hermes-auxiliary.md`](../../blog/senter-as-hermes-auxiliary.md)
- Related: [Omni](./omni.md) · [Senter Ohm](./senter-ohm.md) · [Notebook](./notebook.md) · [Hermes auxiliary](./hermes-auxiliary.md)
- HF (early): [`sovthpaw/Omni-Senter-3B`](https://huggingface.co/sovthpaw/Omni-Senter-3B)
