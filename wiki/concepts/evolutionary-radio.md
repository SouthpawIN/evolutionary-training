# Evolutionary Radio

> **The perpetual, self-evolving generative music engine.** See the
> full blog post:
> [`../../blog/evolutionary-radio-as-desk-pet.md`](../../blog/evolutionary-radio-as-desk-pet.md)
>
> **Status (2026-06-09):** 🟢 **fully functional, radio_bridge wired.**
> The 14 Python files in `~/projects/evolutionary-radio/code/` are
> working. The radio runs as a background daemon, generates tracks
> via ACE-Step, plays via mpv, and maintains a perpetual queue. Two
> evolution loops (Darwin + GEPA) run in parallel. The brain is the
> omni-va slot. The radio_bridge.py module syncs the radio with the
> wiki handoff.

## Definition

The **Evolutionary Radio** is a perpetual, self-evolving generative
music engine. It's not a streaming music app — it **generates** every
track on the fly, based on a "vibe" the user requests, and evolves
its own weights in the background to match the user's taste over
time. It runs as a background daemon, plays through mpv, and
maintains a queue of generated tracks.

## The two evolution loops

The radio improves itself via **two parallel evolution loops**:

1. **Darwin merge (hours/overnight)** — re-merges the radio's
   weights (Darwin Family style) using the gold judge's scoring of
   recent outputs. Slow, expensive, but the changes are real weight
   updates.
2. **GEPA prompt evolution (minutes)** — rewrites the radio's
   prompt template using a genetic algorithm. Fast, cheap, the
   changes are prompt-level.

Combined: the radio's **prompts** improve in real time, the
radio's **weights** improve overnight, and the user just hears
better tracks.

## The 14 files (the radio code)

Located at `~/projects/evolutionary-radio/code/`:

| File | Role |
|---|---|
| `acestep_client.py` | HTTP client for ACE-Step music generation |
| `brain.py` | Brain class wrapping OmniClient + WikiManager + GoldJudge |
| `config.yaml` | Radio config (vibe, queue size, evolution params) |
| `darwin.py` | CMA-ES weight evolution |
| `feedback.py` | User feedback logger (skips, favorites) |
| `gepa.py` | Prompt evolution (genetic algorithm) |
| `mpv_player.py` | mpv wrapper for playback |
| `omni_client.py` | HTTP client for omni-va (with `polite_chat()` deferring when VRAM tight) |
| `prompt_template.py` | The prompt template (evolved by GEPA) |
| `queue.py` | Queue helpers |
| `skip_logger.py` | Skip logger (for feedback evolution) |
| `track_queue.py` | The main RadioQueue (track + queue state) |

Plus `radio.py` (the main entry), `start_radio.sh` (launcher),
`SKILL.md` (skill spec), `README.md` (project readme),
`references/`, `tests/`.

## The two async loops

The radio's `radio.py` runs two async loops in parallel:

**Loop 1 (Playback):**
```
Dequeue next track → mpv → wait for EOF → next
```

**Loop 2 (Queue Fill):**
```
If queue < 5:
    vibe → omni-va (brain) → ACE-Step (voice) → enqueue track
```

The brain (omni-va) decides **what to generate** based on the
vibe + the user's taste profile. ACE-Step decides **how to generate
it** (the actual audio).

## The brain's note-taker role

The brain (via `brain.py`) is no longer just a music generator.
It has two new roles:

1. **`brain.curate_event(event)`** — the note-taker. Listens for
   events (chat, voice, calendar, manual), politely checks VRAM
   (defers if tight), asks the gold judge "is this a new idea worth
   adding?", and writes to `~/.hermes/wiki/` via `wiki_manager.py`.

2. **`brain.compact_wikipedia(max_entries=30)`** — the compactor.
   Reads the top N wiki entries by importance, asks the gold judge
   to compose a Wikipedia-style summary, writes to
   `~/.hermes/wiki/index.md`.

Both methods use the gold judge under the hood. Both gracefully
defer (return None) when VRAM is tight.

## The radio_bridge (the wiki ↔ radio connection)

`~/projects/nous-girl-agent/plugins/evolution-radio/radio_bridge.py`
is the bridge between the radio daemon and the wiki handoff. It:

1. Reads curated notes from `~/wiki/pet-curated/` for taste signals
2. Updates the taste profile with the current vibe
3. Optionally writes back "listening context" notes when the user
   engages with the radio

CLI:

```bash
python3 radio_bridge.py sync      # one-shot wiki → taste.yaml
python3 radio_bridge.py signal    # push current track to wiki
python3 radio_bridge.py evolve    # trigger evolution + write note
```

## How the radio starts

`~/projects/evolutionary-radio/start_radio.sh start --vibe="..."`:

1. omni-va.service is enabled + started (the local model server)
2. The vault directory is prepared (`~/.hermes/vault/templates/`)
3. The radio's main loop starts
4. The brain agent starts watching for ideas
5. The Evolution Radio queue fill loop starts generating tracks
6. mpv starts playing
7. Everything is live (~30 seconds total)

What the user can do:
- Talk to the brain: `curl :8082/v1/chat/completions`
- Inspect the wiki: `curl :8082/wiki/stats`
- Spawn a Hermes session with the wiki preloaded:
  `curl -X POST :8082/hermes/launch`
- Add a new idea to the wiki: just talk to the radio / write a file
- Pick a profile template: `cp ~/.hermes/vault/templates/X.yaml ~/.hermes/vault/profiles/myprofile.yaml`

## The radio evolves the omni-va

The Darwin merge in `darwin.py` operates on the model's weights.
In the future (when OmniStep or Senter is in the slot), the radio
will be able to evolve the **same model that drives it** — the
brain, the judge, the aux, all the same model, all evolving
together. That's the "self-contained OmniStep Ohm or Senter Ohm"
that Chris mentioned.

## See also

- Blog (canonical): [`../../blog/evolutionary-radio-as-desk-pet.md`](../../blog/evolutionary-radio-as-desk-pet.md)
- Blog (older integration post): [`../../blog/omnisenter-integration.md`](../../blog/omnisenter-integration.md)
- Concept: [Omni VA[](../concepts/omni-va.md) — the slot the radio's brain lives in
- Concept: [Ohm](./ohm.md) — the self-evolution engine (will eventually power the radio's evolution)
- Concept: [Agent Hub[](../concepts/agent-hub.md) — the unified vault + wiki + radio surface
- Repo: [`SouthpawIN/evolutionary-radio`](https://github.com/SouthpawIN/evolutionary-radio) — the radio upstream
- Repo: [`SouthpawIN/nous-girl-agent`](https://github.com/SouthpawIN/nous-girl-agent) — the vendored copy + radio_bridge
- Skill: `evolutionary-radio` — see `~/.hermes/skills/`
