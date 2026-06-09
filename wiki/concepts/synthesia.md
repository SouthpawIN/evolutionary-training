# Synthesia

> **The cross-modal memory indexer.** See the full blog post:
> [`../../blog/the-synthesia-layer.md`](../../blog/the-synthesia-layer.md)

## Definition

**Synthesia** is the Senter subsystem that **embeds, indexes, and
retrieves memories across all modalities simultaneously** (text + audio +
image + video). It's the "memory layer" that makes the notebook a
multi-sensory artifact instead of a chat log.

The name comes from the neurological condition *synesthesia* — where
stimulation of one sensory pathway triggers experiences in another.
**Synthetic synesthesia** in Senter means: every memory in the notebook
is encoded as a **joint multi-modal embedding** (one vector space that
text, audio, and image all share), so retrieval can be triggered by *any*
of the modalities the user has access to.

## Where it lives

In the architecture, Synthesia is **Layer 1.5** — between the Senter
Ohm MoE (Layer 1) and the notebook. It receives multimodal tokens
from Layer 0 (Nemotron ASR + Cosmos NaViT), encodes them into a joint
embedding, indexes them in the notebook, and retrieves relevant entries
on cross-modal query.

```
Layer 0 (stream I/O)
   ↓
Layer 1 (Senter Ohm MoE) ← has a "synthesia" expert
   ↓
Layer 1.5 (Synthesia indexer)  ← THE NEW LAYER
   ↓
Notebook (256K context, every entry indexed by all modalities)
   ↓
Layer 3 (Hermes Agent)
```

## The 10 concrete benefits

1. **Better memory retrieval** — recall by sound, image, or text
2. **True continuity** — voice → text → screenshot, one thread
3. **Proactive awareness** — agent notices relevant past events
4. **Richer Hermes context** — escalation passes a multimodal snapshot
5. **Continuous life-log** — every 30s, a `(text, audio, image)` tuple
6. **Cross-modal training signal** — the stream IS training data
7. **Dimensional memory** — multimodal embeddings have more "slots"
8. **Reduced forgetting** — same memory indexed by all modalities
9. **Multi-sensory notebook** — entries are multi-sensory artifacts
10. **Fused expert** — the synesthesia expert is both multimodal AND
    agentic

## The MoE expert

The synesthesia expert is one of the top-k routed experts in the Senter
Ohm MoE. Trained on a mix of:

| Data | Modalities |
|---|---|
| ImageBind pre-train | image + text + audio + depth + thermal + IMU |
| AudioCaps / Clotho | audio + text |
| VGGSound | video + audio |
| HowTo100M | video + speech + text |
| EPIC-KITCHENS / Ego4D | egocentric video + audio + narration |
| LLaVA / ShareGPT4V | vision-language instruction |
| Hermes function-calling v1 | text + tool calls |
| Nemotron agentic v2 | text + multi-turn tool use |
| + user's own passive stream | text + audio + image |

## See also

- Blog post: [`../../blog/the-synthesia-layer.md`](../../blog/the-synthesia-layer.md)
- Related: [Notebook schema](./notebook.md) · [Senter as Hermes auxiliary[](../concepts/hermes-auxiliary.md) · [Senter Ohm](./senter-ohm.md)
