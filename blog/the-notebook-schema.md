# The Notebook Schema: How Senter Remembers What Hermes Doesn't

> **Revised 2026-06-08 (naming).** The notebook is the **transient
> session state** between Senter (32A8B MoE) and Hermes Agent. It is
> **NOT the wiki** — the wiki is a separate, persistent, user-owned
> LLM-friendly knowledge base curated by the note-taker. See
> [`senter-as-hermes-auxiliary.md`](./senter-as-hermes-auxiliary.md)
> for the full notebook-vs-wiki distinction.


> **TOWARDS SELF-IMPROVEMENT** — a 2026-06-07 design post by Chris (via Nous Girl)

![The notebook as cosmic holographic artifact: open pages emanating beams of text, audio waveforms, and image fragments, observed by the Nous Girl character](../assets/images/notebook-schema.png)

> **Naming.** The notebook is the defining feature of every model in the
> **Senter** family (any Omni model with the agentic core wired in —
> Senter, OmniStep, Senter Ohm). If a model is a Senter, it
> has a notebook. The 256K context window exists *for the notebook*. Read
> [`the-omni-family.md`](./the-omni-family.md) for the full taxonomy.

The notebook is what makes Senter valuable as an **auxiliary to Hermes
Agent**. It's a structured state object that flows between turns, between
agents, and across process boundaries. It's what the 256K context window
is *for*. It's how the agent gets "proactive awareness" — detecting that
the user is doing something related to a past event and offering context.

This post is the spec.

## The problem (and why text-only memory isn't enough)

A user starts asking a question via voice, then switches to typing, then opens a screenshot. Standard text-only memory: three siloed traces that may or may not be linked. The agent loses the thread when the user switches modalities.

The notebook solves this by encoding every moment as a **structured multi-sensory artifact** — text + audio signature + image signature + concepts + links — that the agent can retrieve by *any* modality, not just text. This is the [Synthesia](./the-synthesia-layer.md) idea applied to the agent's working memory.

## The schema

A notebook is a directory of YAML files. One file per session, one entry per significant moment. Plus a global index for cross-session retrieval.

```yaml
# ~/.senter/notebook/sessions/<session_id>.yaml
notebook:
  schema_version: "1.0"
  session_id: "s_2026-06-07_001"
  created_at: "2026-06-07T18:30:14Z"
  last_touched: "2026-06-07T19:14:23Z"
  owner: "chris@sovthpaw"
  
  # === TOP-LEVEL TASK ===
  task: "user wants a 2min music video for their band"
  task_status: "in_progress"  # pending | in_progress | blocked | done
  
  # === CURRENT CONTEXT (curated, fits in 256K) ===
  context:
    raw_history_size_tokens: 4823
    condensed_history: |
      User is working on a music video. Asked for a 2min song with their lyrics.
      Previous turn: chose indie-pop genre, gave lyrics draft.
    
    # The 3 most recent moments (always included in context)
    recent_moments:
      - moment_id: "m_1829"
        timestamp: "2026-06-07T19:12:01Z"
        text: "user approved the chorus melody"
        audio_signature_hash: "a3f2b1..."
        image_signature_hash: "i8e4d2..."
      - moment_id: "m_1830"
        timestamp: "2026-06-07T19:13:45Z"
        text: "user asked for a tempo change in verse 2"
        audio_signature_hash: "d7c9a4..."
        image_signature_hash: "f2b1e8..."
      - moment_id: "m_1831"
        timestamp: "2026-06-07T19:14:23Z"
        text: "user opened the DaVinci Resolve video editor"
        audio_signature_hash: "e5a3c1..."
        image_signature_hash: "g9d4f7..."
  
  # === DECISIONS (full audit log) ===
  decisions:
    - turn: 3
      what: "routed to music expert"
      result: "got 30s clip"
      moment_id: "m_1810"
    - turn: 4
      what: "routed to video expert"
      result: "extended to 2min"
      moment_id: "m_1815"
    - turn: 5
      what: "user changed tempo"
      result: "regenerated music with new BPM"
      moment_id: "m_1829"
  
  # === PENDING (open threads) ===
  pending:
    - "needs final lyrics from user"
    - "needs to confirm video export settings"
  
  # === ESCALATIONS (Hermes handoffs) ===
  escalations:
    - when: "2026-06-07T18:23:14Z"
      to: "hermes-4"
      reason: "video editing question beyond my capability"
      notebook_at_handoff_kb: 47
      response_summary: "use DaVinci Resolve, here's the workflow"
      moment_id: "m_1800"
    - when: "2026-06-07T19:01:55Z"
      to: "hermes-4"
      reason: "complex chord progression question"
      notebook_at_handoff_kb: 52
      response_summary: "use a I-vi-IV-V in the chorus for that feel"
      moment_id: "m_1825"
  
  # === LINKS (cross-references to other sessions/moments) ===
  links:
    - "moments/m_0042.yaml"  # the moment from yesterday where we discussed the band
    - "sessions/s_2026-06-05_001.yaml"  # the session where the lyrics were drafted
  
  # === STATS ===
  stats:
    total_moments: 89
    total_decisions: 12
    total_escalations: 2
    state_size_kb: 47
    compaction_count: 0
```

Each moment is a separate file:

```yaml
# ~/.senter/notebook/sessions/s_2026-06-07_001/moments/m_1829.yaml
moment:
  id: "m_1829"
  session_id: "s_2026-06-07_001"
  timestamp: "2026-06-07T19:12:01Z"
  
  # === MULTI-MODAL CONTENT ===
  modalities:
    text: "user approved the chorus melody"
    audio_signature: "a3f2b18e4d29c7e5..."  # 512-d audio embedding hash
    image_signature: "i8e4d2f7b1e8d4f7..."  # 512-d image embedding hash
    multimodal_embedding: "j7k2m1n9p4q6r8s0..."  # 4096-d joint embedding hash
  
  # === THE FULL AUDIO/IMAGE (on-demand) ===
  audio_clip_path: "~/.senter/notebook/audio/m_1829.wav"  # 5s clip
  image_clip_path: "~/.senter/notebook/images/m_1829.png"  # screen capture
  
  # === STRUCTURED METADATA ===
  concepts: ["music", "chorus", "approval"]
  retrieval_keys: ["chorus", "approved", "indie-pop"]
  importance: 0.7  # 0-1, LLM-rated
  decay_rate: 0.001  # per day, for compaction policy
  
  # === RELATIONS ===
  parent_moment: "m_1825"
  child_moments: ["m_1830"]
  linked_to: ["m_0042"]
  
  # === AGENT ACTIONS ===
  actions_taken:
    - "regenerated chorus with new tempo"
    - "saved to working/music_v2.wav"
```

## The index (cross-session)

```yaml
# ~/.senter/notebook/index.yaml
notebook_index:
  schema_version: "1.0"
  last_compacted: "2026-06-07T04:00:00Z"
  
  # === SESSIONS ===
  sessions:
    - id: "s_2026-06-07_001"
      task: "music video for the band"
      last_touched: "2026-06-07T19:14:23Z"
      state_size_kb: 47
    - id: "s_2026-06-05_001"
      task: "lyrics draft"
      last_touched: "2026-06-05T17:42:11Z"
      state_size_kb: 22
  
  # === CONCEPT INDEX (for fast retrieval) ===
  concepts:
    music:
      moment_count: 47
      last_seen: "2026-06-07T19:12:01Z"
    cooking:
      moment_count: 12
      last_seen: "2026-06-04T20:15:00Z"
    work-omnisenter:
      moment_count: 89
      last_seen: "2026-06-07T19:14:23Z"
  
  # === EMBEDDING INDEX (for cross-modal retrieval) ===
  # FAISS-style vector index, persisted to disk
  embedding_index:
    type: "faiss"
    path: "~/.senter/notebook/embeddings.faiss"
    size: 14523  # number of moments indexed
    last_updated: "2026-06-07T19:14:23Z"
  
  # === COMPACTION LOG ===
  compaction_log:
    - when: "2026-06-07T04:00:00Z"
      moments_compacted: 234
      bytes_saved_kb: 89
      method: "LLM-summarize every 100th moment"
```

## The write/read API

The notebook manager is a Python module that the Senter runtime imports. It exposes a clean API:

```python
from notebook_manager import Notebook

nb = Notebook(owner="chris@sovthpaw")

# === WRITE ===
moment_id = nb.add_moment(
    text="user approved the chorus melody",
    audio_signature=audio_emb,  # 512-d torch.Tensor
    image_signature=image_emb,  # 512-d torch.Tensor
    multimodal_embedding=joint_emb,  # 4096-d torch.Tensor
    concepts=["music", "chorus", "approval"],
    audio_clip_path="~/.senter/notebook/audio/m_1829.wav",
    image_clip_path="~/.senter/notebook/images/m_1829.png",
)

nb.add_decision(turn=5, what="user changed tempo", moment_id=moment_id)
nb.add_escalation(to="hermes-4", reason="complex chord progression", 
                  notebook_at_handoff_kb=52, response_summary="use I-vi-IV-V")

# === READ (cross-modal retrieval) ===
# Text query
results = nb.query("chorus melody approval", top_k=5)
# Returns: list of Moment objects, sorted by relevance

# Audio query (find moments that sound like this)
results = nb.query_by_audio(audio_emb, top_k=5)

# Image query (find moments that look like this)
results = nb.query_by_image(image_emb, top_k=5)

# Cross-modal query (sound + image + text)
results = nb.query_multimodal(
    text="cooking",
    audio_emb=kitchen_sound_emb,
    image_emb=pasta_image_emb,
    top_k=5,
)

# === COMPACTION (periodic) ===
nb.compact()  # summarize old moments, decay importance scores
```

## The compaction policy (when does a "moment" become a "memory"?)

The notebook can't grow forever. The compaction policy decides what stays detailed and what gets summarized:

| Age | Action |
|---|---|
| 0-7 days | Keep full fidelity (text + audio + image) |
| 7-30 days | Decay `importance`; moments with `importance < 0.3` get summarized into a "week summary" entry |
| 30-90 days | Daily entries collapse into weekly summaries |
| 90+ days | Weekly summaries collapse into monthly summaries; the original moment file is archived to cold storage |
| Never (concepts) | Concept indices (e.g., "music", "work-senter") persist forever, but the detail degrades |

The LLM does the summarization — Senter itself summarizes its own old moments. The summary is itself a new moment, with a `parent_moment` link to the originals.

## The privacy model

The notebook captures everything — audio signatures, image signatures, full text. Three privacy controls:

1. **Owner-only by default** — files are chmod 600, in `~/.senter/`
2. **Per-modality opt-out** — `~/.senter/config.yaml` can disable audio/indexing, image/indexing, etc.
3. **Manual redaction** — `nb.redact(moment_id)` removes the audio/image but keeps the text; `nb.forget(concept)` removes all moments tagged with that concept
4. **Encrypted-at-rest** — the audio/image signatures can be encrypted with the owner's key (optional, off by default for performance)

The Synthesia indexer is *passive and local* — it never uploads anything. The notebook is the user's private data, on the user's machine.

## The "how this helps" summary (the 10 benefits)

For the full "how does this help us" list, see [synthesia.md](./the-synthesia-layer.md). The headline wins:

1. **Better memory retrieval** — recall by sound, image, or text
2. **True continuity** — voice → text → screenshot, one thread
3. **Proactive awareness** — the agent notices relevant past events
4. **Richer Hermes context** — escalation passes a multimodal snapshot
5. **Continuous life-log** — every 30s, a moment gets stamped
6. **Cross-modal training signal** — the stream IS training data
7. **Dimensional memory** — multimodal embeddings have more "slots"
8. **Reduced forgetting** — same memory indexed by all modalities
9. **Multi-sensory artifact** — the notebook feels like a real memory
10. **Fused expert** — the synesthesia expert is both multimodal AND agentic

## Implementation status

| Component | Status |
|---|---|
| Schema (this doc) | ✅ defined |
| YAML serialization | ⏳ to implement (PyYAML) |
| FAISS embedding index | ⏳ to implement (faiss-cpu) |
| Cross-modal retrieval | ⏳ to implement (the Synesthesia expert in the MoE) |
| Compaction policy | ⏳ to implement (LLM-summarize on cron) |
| Privacy controls | ⏳ to implement (chmod, opt-out flags) |
| Hermes integration | ⏳ via `auxiliary_client.py` (already exists in hermes-agent) |

Estimated code: 400-600 lines of Python for the manager + 200 lines for the Synesthesia expert. Builds on existing `faiss-cpu`, `pyyaml`, `torch` (all already in the env).

## See also

- [senter-architecture](./the-omnisenter-architecture.md) — the system overview
- [synthesia](./the-synthesia-layer.md) — the cross-modal memory indexer
- [senter-ohm](./the-ohm-runtime.md) — the self-evolving model file
- [the-5-stage-pipeline](./the-5-stage-pipeline.md) — the build roadmap
- [sparse-upcycling-deep-dive](./sparse-upcycling-deep-dive.md) — Stage 3 of the pipeline

## TOWARDS SELF-IMPROVEMENT

— Chris (via Nous Girl), 2026-06-07
