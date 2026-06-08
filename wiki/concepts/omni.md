# Omni

> **The multimodal family.** See the full blog post:
> [`../../blog/the-omni-family.md`](../../blog/the-omni-family.md)

## Definition

**Omni** is the **multimodal native** family. Any model called "Omni"
assumes omnimodality — text, vision, audio, video, music. It does
**not** have the agentic core wired in. It does **not** self-evolve.

## Members

### Omni (the umbrella)

The base multimodal family. An "Omni" model is recognisable by the fact
that it has all modalities (text + image + audio + video + music) but
is not an agent and doesn't self-evolve.

### OmniStep

**OmniStep** is Cosmos + AceStep 4B Darwin Family children, fused. It's
the **multimodal + music** model. Useful for generative music, audio
understanding, and any task where the model needs to think in sound.

- **Naming**: "Step" suffix is from the music lineage (ACE-Step)
- **Live on HF**: [`sovthpaw/omnistep-12a3b`](https://huggingface.co/sovthpaw/omnistep-12a3b) —
  12B total / 3B active, 4 GGUFs + 4 safetensors
- **Status**: transitional v1 (the new architecture's OmniStep will
  replace it)

## The two-letter rule

| Word | Means | Adds |
|---|---|---|
| **Omni** | multimodal native | vision, audio, music, video — all in one model |
| **Senter** | the agentic core is wired in | tool use, function calling, planning, notebook |
| **Ohm** | the self-evolution engine is bundled | CMA-ES, genome, validation set, atomic swap |

You can mix them. **Senter Ohm** = agentic + self-evolving. **Omni**
alone = multimodal but not agentic and not self-evolving.

## See also

- Naming source-of-truth: [`../../blog/the-omni-family.md`](../../blog/the-omni-family.md)
- Related: [Senter](./senter.md) · [Ohm](./ohm.md) · [Senter Ohm](./senter-ohm.md) · [OmniStep destination](./omnistep.md) · [Omnimodal fusion](./omnimodal-fusion.md)
- HF: [`sovthpaw/omnistep-12a3b`](https://huggingface.co/sovthpaw/omnistep-12a3b)
