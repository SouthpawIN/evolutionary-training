# OmniSenter as the Hermes Auxiliary: The Integration Pattern

> **TOWARDS SELF-IMPROVEMENT** — a 2026-06-07 design post by Chris (via Nous Girl)

![Two AI entities facing each other — a small focused character with headphones (the auxiliary) and a large powerful radiant figure (the smart agent) — connected by a holographic stream of structured YAML data](assets/hermes-auxiliary.png)

OmniSenter is the **auxiliary to Hermes Agent**. It sits in front of Hermes, doing the work that doesn't need a 70B-class brain. When the task gets hard, OmniSenter hands a structured **notebook** to Hermes and gets a decision back.

This post is the integration pattern. The contract, the API, the notebook-as-data-format, the escalation rules.

## Why an auxiliary?

Hermes Agent is the "smart" agent — heavy reasoning, code, math, research. But it's expensive to call for every turn. OmniSenter is the **always-cheap context curator** that:

- Handles trivial/plugin-friendly requests directly (no escalation)
- Handles multimodal I/O (images, video, audio, music, speech) via its specialists
- Maintains a structured notebook across turns
- Hands the smart agent only the relevant slice of state when escalation is needed
- Updates the notebook from the smart agent's response

Net result: Hermes gets called **only when needed**, the user gets **fast first-token** for trivial cases, and the full notebook survives across turns without paying the full cost every time.

## The integration point

`hermes-agent/agent/auxiliary_client.py` is the existing class. It already does:
- Calling a smaller LLM alongside the main agent
- Vision processing
- Summarization

We extend it to use OmniSenter specifically:
- Default auxiliary model: `omnisenter-moe-32a8b` (4-bit GGUF, served on `:11500`)
- Auxiliary tasks: vision, summarization, agentic routing, notebook management
- The main agent stays whatever the user has configured (Claude, Hermes-4, etc.)

## The notebook-as-API pattern

The notebook is the **structured state object** that flows between OmniSenter and Hermes. It's the API surface, not the implementation detail.

### OmniSenter → Hermes (escalation)

```yaml
# Sent to Hermes as a single user message + the notebook as a system attachment
notebook_handoff:
  schema_version: "1.0"
  
  # The full current session context (fits in Hermes's context window)
  session_summary: |
    User is working on a music video for their band. 
    Previously chose indie-pop, gave lyrics draft.
    Approved the chorus melody in turn 5.
    Tempo change requested in turn 6.
  
  # The 3 most recent moments (always sent)
  recent_moments:
    - { id: "m_1829", text: "user approved the chorus melody", 
        multimodal_summary: "audio: upbeat; image: waveform on screen" }
    - { id: "m_1830", text: "user asked for tempo change in verse 2",
        multimodal_summary: "audio: mid-tempo; image: BPM display" }
    - { id: "m_1831", text: "user opened DaVinci Resolve",
        multimodal_summary: "image: DaVinci UI on screen" }
  
  # The specific question for Hermes
  question: "What's the best DaVinci Resolve workflow for syncing audio to video at this tempo?"
  
  # What Hermes should return
  expected_response:
    format: "yaml"
    schema: "hermes_decision_v1"
    fields:
      decision: "the recommended workflow"
      steps: ["step 1", "step 2", ...]
      confidence: 0.0-1.0
      needs_clarification: ["optional follow-up questions"]
  
  # Constraints for Hermes
  constraints:
    max_response_tokens: 500
    must_include_sources: true
```

### Hermes → OmniSenter (response)

```yaml
# Hermes returns this, OmniSenter parses it back into the notebook
hermes_response:
  schema_version: "1.0"
  
  decision: |
    1. Import the audio track to DaVinci Resolve
    2. Set the project frame rate to match the audio
    3. Use the Audio Sync feature to align
    4. Apply warp/elastic stretch for fine tempo adjustment
  
  steps:
    - "File > Import Media > select audio.wav"
    - "Project Settings > Master Settings > Timeline frame rate"
    - "Right-click audio > Auto Sync"
    - "Inspector > Audio > Warp > Elastic"
  
  confidence: 0.92
  needs_clarification: []
  
  sources:
    - "DaVinci Resolve 18 manual, page 247"
    - "Common workflow in indie music videos"
  
  # What OmniSenter should do with this
  omni_should:
    - action: "summarize_for_user"
      format: "bulleted list with bold for action verbs"
    - action: "update_notebook"
      decision_record: true
      importance: 0.8
```

## The escalation rules (when does OmniSenter ask Hermes?)

```python
def should_escalate(user_message: str, current_state: dict) -> bool:
    """OmniSenter's escalation logic."""
    
    # NEVER escalate trivial
    trivial_patterns = [
        r"^(hi|hey|hello|thanks|ok|yes|no|sure)\b",
        r"^what time is it",
        r"^(stop|cancel|abort)$",
    ]
    if any(re.match(p, user_message.lower()) for p in trivial_patterns):
        return False
    
    # NEVER escalate if a plugin can handle it
    plugin_intents = ["image", "video", "music", "speech", "search", "weather"]
    intent = classify_intent(user_message)
    if intent in plugin_intents:
        return False  # route to plugin instead
    
    # ESCALATE if the question requires deep reasoning
    deep_reasoning_patterns = [
        r"\bwhy\b.*\?",  # "why does X do Y?"
        r"\bhow (do|does|can|should)\b",  # "how do I..."
        r"\b(explain|analyze|compare|evaluate)\b",
        r"\b(best|optimal|recommended)\b.*\b(approach|method|way|strategy)\b",
    ]
    if any(re.search(p, user_message.lower()) for p in deep_reasoning_patterns):
        return True
    
    # ESCALATE if the question is about a complex multi-step task
    if estimate_steps(user_message) > 3:
        return True
    
    # ESCALATE if the user explicitly asks for it
    if "hermes" in user_message.lower() or "smart agent" in user_message.lower():
        return True
    
    # Default: handle directly
    return False
```

## The notebook slicing (what does Hermes actually see?)

Hermes has a context window too. We don't dump the whole 256K notebook at it. We slice:

```python
def slice_notebook_for_hermes(notebook: dict, question: str, max_tokens: int = 30000) -> dict:
    """Return a notebook slice that fits Hermes's context and is relevant to the question."""
    
    # 1. Always include: task, recent_moments, decisions_summary
    slice_ = {
        "task": notebook["task"],
        "recent_moments": notebook["context"]["recent_moments"],
        "decisions_summary": summarize_decisions(notebook["decisions"], max_tokens=2000),
    }
    
    # 2. Add relevant past moments (semantic search)
    relevant = notebook.search(question, top_k=5, max_token_budget=8000)
    slice_["relevant_moments"] = relevant
    
    # 3. Add relevant past escalations
    past_escalations = [e for e in notebook["escalations"] 
                        if any(c in question.lower() for c in e.get("topics", []))]
    slice_["past_escalations"] = past_escalations[:3]
    
    # 4. Add the current question
    slice_["question"] = question
    
    # 5. Truncate to fit
    return truncate_to_tokens(slice_, max_tokens)
```

## The cost model

| Task type | OmniSenter cost | Hermes cost | When |
|---|---|---|---|
| Trivial (greeting, ack) | ~50ms, 100 tokens | $0 | always handled by OmniSenter |
| Plugin call (image, music) | ~500ms, 1K tokens | $0 | OmniSenter calls plugin, returns result |
| Notebook query (recall) | ~200ms, 500 tokens | $0 | OmniSenter searches + answers |
| Reasoning (complex Q) | ~2s, 2K tokens | ~5s, 4K tokens | OmniSenter escalates, Hermes reasons, OmniSenter summarizes |
| Multi-step task (planning) | ~3s, 3K tokens | ~15s, 8K tokens | OmniSenter hands off the full notebook slice |

**Estimated savings:** For a typical session with 20 turns:
- 12 trivial/plugin turns: $0 from Hermes (vs $0.50 if all 20 went to Hermes)
- 6 notebook queries: $0 from Hermes (vs $1.20)
- 2 escalations: $0.30 (vs $0.40 if all reasoning was done by Hermes)
- **Total: $0.30 (vs $2.10) — 86% cost reduction**

The savings scale with usage. Heavy users save more.

## The user experience

A user types: *"hey what's the best DaVinci workflow for syncing audio"*

1. **OmniSenter receives it** — checks the trivial patterns (no), checks plugin intents (no), checks escalation rules (yes — "best ... workflow" pattern)
2. **OmniSenter slices the notebook** — finds past DaVinci references, recent audio tempo changes
3. **OmniSenter escalates** — sends the notebook slice to Hermes with the question
4. **Hermes reasons** — returns a structured decision
5. **OmniSenter summarizes** — formats the response, updates the notebook with the decision
6. **OmniSenter replies** — bulleted list with bold action verbs, decision recorded

Total user wait: ~7-8 seconds. Notebook updated. Decision available for future turns.

The user doesn't see Hermes. They just see OmniSenter being smart, fast, and remembering everything.

## The implementation

```python
# hermes-agent/agent/auxiliary_client.py (extended)

class OmniSenterAuxiliaryClient(AuxiliaryClient):
    """Auxiliary client that uses OmniSenter for vision, summarization, agentic routing, notebook management."""
    
    def __init__(self, *args, omni_endpoint: str = "http://localhost:11500/v1", **kwargs):
        super().__init__(*args, **kwargs)
        self.omni = OpenAI(base_url=omni_endpoint, api_key="not-needed")
        self.notebook = Notebook(owner=self.user_id)
    
    def summarize_for_compression(self, messages: list, **kwargs) -> str:
        """Summarize a long conversation for context compression."""
        return self.omni.chat.completions.create(
            model="omnisenter-moe-32a8b",
            messages=[
                {"role": "system", "content": "Summarize the following conversation, preserving all key decisions and context."},
                {"role": "user", "content": format_messages(messages)},
            ],
            max_tokens=2000,
        ).choices[0].message.content
    
    def describe_image(self, image_bytes: bytes, **kwargs) -> str:
        """Describe an image for vision context."""
        return self.omni.chat.completions.create(
            model="omnisenter-moe-32a8b",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": "Describe this image in detail."},
                    {"type": "image", "image": image_bytes},
                ]},
            ],
            max_tokens=500,
        ).choices[0].message.content
    
    def maybe_escalate(self, user_message: str) -> Optional[dict]:
        """Decide if this message needs Hermes, and if so, prepare the notebook slice."""
        if not should_escalate(user_message, self.notebook.current_state()):
            return None
        
        slice_ = slice_notebook_for_hermes(self.notebook, user_message, max_tokens=30000)
        return {
            "reason": "complex_reasoning",
            "notebook_slice": slice_,
            "question": user_message,
            "expected_response_format": "yaml",
        }
    
    def record_hermes_response(self, question: str, response: dict) -> None:
        """After Hermes responds, write the response back to the notebook."""
        moment_id = self.notebook.add_moment(
            text=f"Hermes decision on: {question[:200]}",
            concepts=extract_concepts(response),
            importance=response.get("confidence", 0.5),
        )
        self.notebook.add_decision(
            turn=self.notebook.current_turn(),
            what=f"escalated to Hermes: {question[:100]}",
            moment_id=moment_id,
        )
        self.notebook.add_escalation(
            to="hermes",
            reason=question[:200],
            notebook_at_handoff_kb=self.notebook.current_size_kb(),
            response_summary=response.get("decision", "")[:500],
            moment_id=moment_id,
        )
```

## The deployment

```bash
# Terminal 1: Start the OmniSenter server
python3 ohmd.py serve --model omnisenter-moe-32a8b-q4_k_m.gguf \
    --notebook-path ~/.omnisenter/notebook/ \
    --port 11500

# Terminal 2: Start Hermes Agent with OmniSenter as auxiliary
hermes --auxiliary-model omnisenter-moe-32a8b --auxiliary-endpoint http://localhost:11500/v1

# That's it. Hermes now has a notebook-keeping multimodal auxiliary.
```

## See also

- [omnisenter-self-evolving.md](./omnisenter-self-evolving.md) — the flagship overview
- [the-notebook-schema.md](./the-notebook-schema.md) — the notebook spec
- [the-5-stage-pipeline.md](./the-5-stage-pipeline.md) — the build roadmap
- [omnisenter-architecture](file:///home/sovthpaw/wiki/concepts/omnisenter-architecture.md) — the system overview
- `hermes-agent/agent/auxiliary_client.py` — the integration point

## TOWARDS SELF-IMPROVEMENT

— Chris (via Nous Girl), 2026-06-07
