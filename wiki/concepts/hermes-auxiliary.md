# Senter as Hermes Auxiliary

> **The integration pattern.** See the full blog post:
> [`../../blog/senter-as-hermes-auxiliary.md`](../../blog/senter-as-hermes-auxiliary.md)

## Definition

[Senter[](../concepts/senter.md) (any model in the Senter family) sits **in front
of** Hermes Agent, doing the work that doesn't need a 70B-class brain.
When the task gets hard, Senter hands a structured
[notebook](./notebook.md) to Hermes and gets a decision back.

The user doesn't see Hermes. They just see Senter being smart, fast,
and remembering everything.

## The integration point

`hermes-agent/agent/auxiliary_client.py` is the existing class. It
extends to use Senter specifically:
- Default auxiliary model: `senter-ohm-moe-32a8b` (4-bit GGUF, `:11500`).
  For lighter deployments, swap in `omnisenter-12b`.
- Auxiliary tasks: vision, summarization, agentic routing, notebook
  management.
- The main agent stays whatever the user has configured (Claude,
  Hermes-4, etc.)

## The notebook-as-API pattern

The notebook is the **API surface** between Senter and Hermes:

**Senter → Hermes (escalation):**
```yaml
notebook_handoff:
  schema_version: "1.0"
  session_summary: |
    User is working on a music video for their band.
    Previous turn: chose indie-pop, gave lyrics draft.
  recent_moments: [ ... 3 most recent ... ]
  question: "What's the best DaVinci Resolve workflow for syncing audio?"
  expected_response:
    format: "yaml"
    schema: "hermes_decision_v1"
    fields: { decision, steps, confidence, needs_clarification }
  constraints: { max_response_tokens: 500, must_include_sources: true }
```

**Hermes → Senter (response):**
```yaml
hermes_response:
  decision: |
    1. Import the audio track
    2. Set the project frame rate
    3. Use Auto Sync
    4. Apply warp/elastic stretch
  steps: [ ... ]
  confidence: 0.92
  sources: [ ... ]
  senter_should:
    - action: "summarize_for_user"
    - action: "update_notebook"
      decision_record: true
      importance: 0.8
```

## The escalation rules

Senter escalates to Hermes when:
- Question requires deep reasoning ("why", "how", "best ... approach",
  "compare", etc.)
- Question is a complex multi-step task (> 3 estimated steps)
- User explicitly asks for the "smart agent" / "hermes"

Senter handles directly when:
- Trivial (greeting, ack, "what time is it")
- Plugin-friendly (image gen, music, search, weather)
- Notebook query (recall by text/audio/image)

## The cost model

| Task type | Senter cost | Hermes cost |
|---|---|---|
| Trivial | ~50ms, 100 tokens | $0 |
| Plugin call | ~500ms, 1K tokens | $0 |
| Notebook query | ~200ms, 500 tokens | $0 |
| Reasoning | ~2s, 2K tokens | ~5s, 4K tokens |
| Multi-step | ~3s, 3K tokens | ~15s, 8K tokens |

**Estimated savings**: 86% cost reduction for a typical session (20
turns, 12 trivial/plugin handled by Senter, 6 notebook queries, 2
escalations).

## The deployment

```bash
# Terminal 1: Start the Senter server
python3 ohmd.py serve --model senter-ohm-moe-32a8b-q4_k_m.gguf \
    --notebook-path ~/.senter/notebook/ \
    --port 11500

# Terminal 2: Start Hermes with Senter as auxiliary
hermes --auxiliary-model senter-ohm-moe-32a8b \
       --auxiliary-endpoint http://localhost:11500/v1
```

## See also

- Blog post: [`../../blog/senter-as-hermes-auxiliary.md`](../../blog/senter-as-hermes-auxiliary.md)
- Related: [Senter[](../concepts/senter.md) · [Notebook](./notebook.md) · [Synthesia](./synthesia.md) · [OmniSenter](./omnisenter.md)
- Integration point: `hermes-agent/agent/auxiliary_client.py`
