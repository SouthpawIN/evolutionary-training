# The Notebook

> **The structured state object.** See the full blog post:
> [`../../blog/the-notebook-schema.md`](../../blog/the-notebook-schema.md)

## Definition

The **notebook** is a structured state object that flows between turns,
between agents, and across process boundaries. It's what makes
[Senter[](../concepts/senter.md) (any model in the Senter family) an **effective**
auxiliary to Hermes Agent rather than just a smaller model.

The notebook is **owned by Senter**, not by Hermes. Hermes is a guest
who reads the relevant slice, makes a decision, and writes back. Senter
does the summarization, indexing, and irrelevant-dropping.

## The schema

A notebook is a directory of YAML files:

```
~/.senter/notebook/
├── sessions/
│   ├── s_2026-06-07_001.yaml      # session file
│   └── s_2026-06-07_001/
│       └── moments/
│           ├── m_1829.yaml         # individual moment
│           └── m_1830.yaml
├── index.yaml                     # cross-session index
└── embeddings.faiss               # vector index
```

Each session has:
- `task` + `task_status`
- `context` (raw_history_size + condensed_history + recent_moments)
- `decisions` (full audit log)
- `pending` (open threads)
- `escalations` (Hermes handoffs)
- `links` (cross-references)
- `stats` (totals, sizes)

Each moment has:
- Multi-modal content (text + audio_signature + image_signature +
  multimodal_embedding)
- Audio/image paths (on-demand, for full retrieval)
- Structured metadata (concepts, retrieval_keys, importance, decay_rate)
- Relations (parent/child/links)
- Agent actions taken

## The compaction policy

| Age | Action |
|---|---|
| 0-7 days | Keep full fidelity |
| 7-30 days | Decay importance; summarize moments with `importance < 0.3` |
| 30-90 days | Daily → weekly summaries |
| 90+ days | Weekly → monthly; archive originals to cold storage |
| Never (concepts) | Concept indices persist forever, detail degrades |

The LLM does the summarization — Senter itself summarizes its own old
moments.

## The privacy model

1. **Owner-only by default** — chmod 600 in `~/.senter/`
2. **Per-modality opt-out** — `~/.senter/config.yaml` flags
3. **Manual redaction** — `nb.redact(moment_id)`, `nb.forget(concept)`
4. **Encrypted-at-rest** — optional, off by default for performance

## The 256K context

The 256K context window exists **for the notebook**. Raw conversations
stay short; structured notebook entries get the long window. This is
Stage 4 (YaRN extension) of the pipeline.

## See also

- Blog post: [`../../blog/the-notebook-schema.md`](../../blog/the-notebook-schema.md)
- Blog post: [`../../blog/senter-as-hermes-auxiliary.md`](../../blog/senter-as-hermes-auxiliary.md)
- Related: [Senter[](../concepts/senter.md) · [Synthesia](./synthesia.md) · [Hermes auxiliary[](../concepts/hermes-auxiliary.md) · [Senter Ohm](./senter-ohm.md)
