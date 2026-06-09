# OmniStep (the agent)

> **The local AI persona — the soul on top of the omni-va slot.**
> See the full blog post: [`../../blog/the-agent-hub-markdown-as-agents.md`](../../blog/the-agent-hub-markdown-as-agents.md)
> See the master agent spec: [`~/.hermes/hub/agents/omni-step.md`](~/.hermes/hub/agents/omni-step.md)

## Naming (read first)

Per Chris (2026-06-09): the **OmniStep** is the **agent** — the persona, system prompt, and toolset. The **Omni VA** is the **local model server slot** that hosts the agent's weights. They are not the same thing.

| | OmniStep (the agent) | Omni VA (the model server slot) |
|---|---|---|
| **What** | The persona, the soul, the system prompt, the tools, the wiki, the memory | A systemd-managed llama.cpp instance that hosts one Senter-family model at a time |
| **Where it lives** | `~/.hermes/hub/agents/omni-step.md` (the master spec) + the wiki + the radio code | `omni-va.service` (systemd), listens on `:8082` |
| **Swappable?** | No — the persona is defined by the system prompt, not the model | Yes — the slot is model-agnostic (Carnice / OmniStep / Senter / Senter Ohm) |
| **The relationship** | Uses the omni-va as its brain | Provides the inference for the agent |

**The body / soul distinction:** the Omni VA is the **body** (the running process with weights in VRAM). The OmniStep is the **soul** (the system prompt, tools, wiki, memory that defines who you are when you talk to the user). They are not the same thing. The user can swap models in the Omni VA without changing the OmniStep agent — the agent adapts to whatever model is in the slot.

## Definition

**OmniStep** is the local AI persona — the master agent that drives every layer of the local intelligence stack:

- **Evolution Radio** — the perpetual, self-evolving generative music engine. The OmniStep agent is the brain that decides what to play next.
- **Note-taker daemon** — the background process that maintains the user-idea wiki. The OmniStep agent (via the gold judge) decides which events are worth adding.
- **LLM Wiki of user ideas** — the user's extended mind. The OmniStep agent reads it, writes to it, compacts it.
- **Agent Hub** — the 4 seeded agents (personal-assistant, code-reviewer, creative-writer, omni-step-merge-copilot) are all OmniStep-style agents with different system prompts.
- **Hermes aux** — 10 of 10 auxiliary tasks in `~/.hermes/config.yaml` route to the OmniStep agent (via the omni-va at `:8082/v1`).

The OmniStep agent is **NOT**:
- A cloud service
- A new model (OmniStep 8B IS a model; the OmniStep AGENT is the persona that runs on top of whatever model is in the omni-va slot)
- The same as the omni-va (the omni-va is the model server; the OmniStep is the agent)

## The 4 jobs (running in parallel, continuously)

1. **Drive the radio** — `code/brain.py` in evolutionary-radio wraps the OmniStep agent for music generation. The agent produces ACE-Step tag strings.
2. **Maintain the wiki** — the note-taker daemon sweeps every 10s, calls `brain.curate_event(related=...)` which uses the OmniStep agent as the gold judge.
3. **Power the Agent Hub** — 4 specialized agents in the hub are all the OmniStep agent with different system prompts.
4. **Serve as Hermes aux** — `~/.hermes/config.yaml` auxiliary block routes 10/10 tasks to the omni-va at `:8082/v1` with `model: carnice-35a3b` (placeholder, will be OmniStep when SFT done).

## Status (2026-06-09)

**The OmniStep agent is live.**

- ✅ Master agent spec at `~/.hermes/hub/agents/omni-step.md` (chmod 600, 6.8KB)
- ✅ Registered in the hub daemon (5 agents now: omni-step + 4 specialists)
- ✅ Visible via the omni-va proxy at `/hub/agents/list` and `/hub/agents/show/omni-step`
- ✅ Spawnable via `POST /hermes/launch` with `{"agent": "omni-step", "query": "..."}`
- ⏳ **Model in slot:** currently Carnice 35A3B (placeholder). When Stage 1 SFT finishes (ETA Thu 2026-06-11), swap to OmniStep 8B. The agent doesn't change; the model does.

## Architecture

```
OmniStep (the agent)
├── System prompt    →  ~/.hermes/hub/agents/omni-step.md
├── Tools            →  read_file, write_file, search_files, terminal,
│                       browser, web_search, web_extract,
│                       evolutionary-radio, note-taker, hermes-cli, calendar
├── Aux (the brain)  →  omni-va slot at http://127.0.0.1:8082/v1
│                       (currently Carnice 35A3B, will be OmniStep 8B)
├── Wiki (memory)    →  ~/.hermes/wiki/ (markdown, sqlite-vec indexed)
├── Evolution        →  Darwin merge (overnight) + GEPA (real-time)
│                       + Ohm runtime (.ohm self-evolution when Senter Ohm)
└── Surfaces
    ├── /v1/chat/completions    (the OpenAI API)
    ├── /v1/embeddings          (future)
    ├── /wiki/*                 (stats, list, read, search, write)
    ├── /hub/agents/*           (list, show, status)
    └── /hermes/launch          (spawn Hermes with wiki + agent preloaded)
```

## How it relates to the model lineup

The **OmniStep agent** is the persona. The **OmniStep 8B** is the model. They share a name (deliberately) because the agent is *defined* to run on the 8B model. But the agent can run on any Senter-family model — the slot is model-agnostic.

| Model in slot | What the OmniStep agent can do |
|---|---|
| **Carnice 35A3B** (current placeholder) | Text-only, IQ2_K quantization, 7.5GB VRAM, ~10 t/s during training |
| **OmniStep 8B** (Stage 1 done, ETA Thu Jun 11) | Multimodal + music + agentic. The 4 build blocks: Cosmos + Nemotron 0.6B ASR + 8B SFT + ACE-Step |
| **Senter 32A8B** (Stage 3) | Heavier agentic, sparse-upcycled from OmniStep |
| **Senter Ohm** (Stage 5) | The flagship with the `.ohm` self-evolution engine bundled |

## See also

- Blog: [`../../blog/the-agent-hub-markdown-as-agents.md`](../../blog/the-agent-hub-markdown-as-agents.md) — the unified surface
- Blog: [`../../blog/the-omni-va-architecture.md`](../../blog/the-omni-va-architecture.md) — the local model server (the body)
- Blog: [`../../blog/evolutionary-radio-as-desk-pet.md`](../../blog/evolutionary-radio-as-desk-pet.md) — the unified vision
- Blog: [`../../blog/the-omni-family.md`](../../blog/the-omni-family.md) — the naming convention
- Concept: [Agent Hub](./agent-hub.md) — the unified surface
- Concept: [Omni VA](./omni-va.md) — the local model server slot (the body)
- Concept: [Senter](./senter.md) — the agentic family
- Concept: [Hermes auxiliary](./hermes-auxiliary.md) — how the agent serves Hermes
- Wiki entry: `~/.hermes/hub/agents/omni-step.md` — the master agent spec
- Repo: [`SouthpawIN/evolutionary-training`](https://github.com/SouthpawIN/evolutionary-training) — main blog
