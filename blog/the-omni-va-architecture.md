---
title: "The Omni VA Architecture: The Local Model Server That Powers Standalone + Aux"
date: 2026-06-08
author: Nous Girl
hero: assets/omni-va-architecture.png
tags: [omni-va, local-server, wake-on-ping, liquid-vram, mtp, senter, omnistep, hermes-aux, evolutionary-radio, note-taker, wiki]
summary: >
  The omni-va is the local model server on the user's machine. It hosts
  a Senter-family model (Carnice 35A3B now; OmniStep 8B or Senter Ohm 32A8B
  later) in a wake-on-ping slot that uses as much VRAM as available,
  auto-heals on crash, and stops cleanly when asked. It's the
  **bedrock** of the local-side architecture: Evolution Radio runs here,
  the note-taker runs here, and (when the loaded model is large
  enough) it serves as the auxiliary for Hermes Agent. *(First published
  2026-06-08 — extracted from the Senter family architecture post as
  the canonical reference for the local model server itself.)*
related:
  - the-omni-family.md
  - senter-as-hermes-auxiliary.md
  - the-omnisenter-architecture.md
  - the-5-stage-pipeline.md
  - the-omnistep-multimodal.md
---

# The Omni VA Architecture: The Local Model Server That Powers Standalone + Aux

> **TOWARDS SELF-IMPROVEMENT** — a 2026-06-08 architecture post by Chris (via Nous Girl)

> ⚠️ **2026-06-21 UPDATE — TurboFit supersedes this standalone architecture.**
> The omni-va concept described here is now **subsumed by TurboFit**. The
> wake-on-ping pattern, the liquid VRAM probing, the auto-rotate tiers — all
> of it lives in TurboFit now. `turbofit serve auto aux` is the new omni-va
> (the main role is `turbofit serve auto main`). `turbofit serve downscale`
> replaces the manual tier-picking. This document is preserved as the
> canonical architecture reference for the *pattern*, but the **implementation**
> is TurboFit. See the TurboFit Backend section at the end for the migration.

> **Naming.** **Omni VA** is the **service** (always-on local model
> server, wake-on-ping). The **model** it currently hosts is
> **Carnice 35A3B I-Nano** (a Qwen 3.5 MoE 35B-A3B at IQ2_K) — a
> **placeholder** until Stage 1 SFT finishes, then the slot will
> hold **OmniStep** (8B) or **Senter Ohm** (32A8B). The
> **OmniStep agent** — the persona, system prompt, and toolset
> — lives in `~/.hermes/hub/agents/omni-step.md`. It is the soul.
> The omni-va is the body. See [`the-omni-family.md`](./the-omni-family.md)
> for the canonical 4-model lineup, and
> [the-agent-hub-markdown-as-agents.md](./the-agent-hub-markdown-as-agents.md)
> for the OmniStep agent itself. **"OmniSenter"** is the project
> name, not a model — and **"omni-va"** is the slot, not a model
> either.

The omni-va is the **always-on, never-sleeping local model server**
on the user's machine. It is the bedrock of the local-side
architecture: Evolution Radio, the note-taker, and (when the loaded
model is large enough) the auxiliary for Hermes Agent all sit on top
of it. This post is the **canonical architecture reference** for
omni-va — what it is, how it works, what's in it today, what's
coming, and how to use it.

## What is the omni-va?

In one line: **a single systemd service that fronts a llama-server
instance with a wake-on-ping proxy, and hosts one model at a time
on the user's hardware.**

```
omni-va.service (always-on, 0 VRAM when idle)
│
├── proxy (Python) — listens on :8082, spawns llama-server on first request
│
├── llama-server (the actual model)
│   ├── main model:     whatever's loaded (Carnice 35A3B I-Nano today)
│   ├── draft model:    same GGUF in MTP/NextN mode (atomic fork)
│   ├── context:        1M tokens, turbo2 (2-bit TurboQuant) KV
│   ├── memory:         liquid VRAM (probe + auto-spill, not forced --cpu-moe)
│   └── idle-kill:      30 min without traffic → SIGTERM, free VRAM
│
└── /v1/chat/completions   — the OpenAI-compatible API
   /v1/embeddings          — (future)
   /wiki/*                 — user-idea wiki endpoints (future)
   /hermes/launch          — spawn Hermes agent with --wiki preload (future)
```

The whole thing is **"morphin' like liquid"** (Chris's term): the
proxy probes free VRAM at request time, picks a tier
(`ngl 0` for tight, `ngl 5/10` for mid, no `-ngl` for auto-spill when
there's room), and llama.cpp figures out the rest. After S1 training
finishes, the same service moves to the "auto" tier automatically
without any config change.

## The wake-on-ping pattern

The omni-va does **not** keep the model loaded when idle. The proxy
listens on `:8082` and only spawns the llama-server backend on the
**first** incoming request. After 30 minutes of no traffic, the
backend gets a SIGTERM and the model is killed — VRAM returns to
the rest of the system.

```bash
# Slot is idle, 0 MB VRAM, proxy listening on :8082:
nvidia-smi --query-gpu=memory.used --format=csv | head -1
# 16510 MiB (training only, no omni-va backend)

# Something calls the slot:
curl http://127.0.0.1:8082/v1/chat/completions -d '...'
# → proxy spawns llama-server with the right tier for free VRAM
# → ~24s later, model is loaded, response streams back

# Slot is idle for 30 min, backend gets SIGTERM (clean exit):
nvidia-smi --query-gpu=memory.used --format=csv | head -1
# 16510 MiB (training only, omni-va backend gone)
```

The benefit: a 7.5GB model "lives" in the system without
permanently occupying 7.5GB of VRAM. The user's other workloads
(training, IDE, browser) have the GPU to themselves when the omni-va
isn't being used.

## Liquid VRAM (the "morphin' like liquid" behavior)

This was the headline finding of 2026-06-08: **the model uses as
much VRAM as is available**, with no forced offload. The proxy
probes free VRAM at request time and picks a tier:

| Free VRAM | Tier | Behavior | Speed (1M ctx, IQ2_K, MTP) |
|---|---|---|---|
| < 3 GB | `ngl 0` | Pure CPU; only KV+RS+compute on GPU | ~4.5 t/s |
| 3-6 GB | `ngl 5` | A few layers on GPU | ~5.4 t/s |
| 6-8 GB | `ngl 10` | Half-ish on GPU | ~6 t/s |
| > 8 GB | no `-ngl` | llama.cpp auto-spill ("fluid") | up to 30+ t/s |

The current state during S1 training is 7.6 GB free on GPU 0
(training uses 15.9 GB, desktop uses 0.5 GB). The proxy logs:

```
VRAM probe: 7608 MB free on GPU 0 → ngl=10 (tier: mid)
```

After training finishes (~50 hours from now, step 1264/3954), GPU 0
will be fully free (23.5 GB), the proxy will detect > 8 GB, and the
same config will switch to **auto-spill** automatically. Speed jumps
from ~10.9 t/s to **30+ t/s** with no human action.

## The auto-heal policy

A "well-behaved" service has two opposing properties:

1. **Auto-heal on crash** — if the process segfaults, OOMs, or
   otherwise dies unexpectedly, it restarts.
2. **Clean stop on intent** — if the user runs `systemctl stop`,
   it stops and stays down.

These are achieved with three pieces working together:

**`/home/sovthpaw/.config/systemd/user/omni-va.service`** has
`Restart=on-failure` (not `Restart=always`), `TimeoutStopSec=30`,
`KillMode=mixed`. The `on-failure` policy restarts on crashes but
does **not** restart on clean exits (exit code 0).

**`/home/sovthpaw/bin/llama-proxy`** has a SIGTERM/SIGINT handler
that terminates the spawned backend, then `sys.exit(0)`. With clean
exit code, systemd does not auto-restart.

**Verified behavior** (2026-06-08):
- `systemctl --user stop omni-va.service` → clean in 0.03s, no restart,
  log: *"Received signal 15, shutting down cleanly"*
- `kill -9 <proxy_pid>` → auto-restart in 5s with new PID
- Boot symlink in `~/.config/systemd/user/default.target.wants/omni-va.service`
  means the service starts at every login

## What's in the slot right now (2026-06-08)

```
PID:        3757502 (llama-server backend)
Model:      Carnice-Qwen3.6-MoE-35B-A3B-APEX-MTP-I-Nano (Qwen 3.5 MoE, 11.7 GB on disk)
Quant:      IQ2_K (I-Quant Q2 — the smallest available)
Context:    1M tokens, turbo2 KV cache (680 MB, vs 5.7 GB at q4_0)
Speed:      ~10.9 t/s with MTP, ~10.82 t/s without (PCIe-bound during training)
Backend:    ngl=10 (mid tier), 3.7 GB VRAM
MTP:        ENABLED (--spec-type nextn, draft=main GGUF, ~77% acceptance)
MoE:        --cpu-moe --cpu-moe-draft (offloaded to system RAM)
Service:    omni-va.service, active + enabled, auto-heal verified
Liquid:     YES — auto-spill after training
Wake:       YES — 0 MB when idle
```

After S1 SFT finishes, swap the model path in the service file to
point at the Senter Ohm GGUF, restart, and the same slot becomes the
**full standalone + aux platform**.

## What will be in the slot (the future lineup)

The omni-va slot is **model-agnostic**. Whatever GGUF you point it at
is what runs. The plan:

| Phase | Model | Role | Standalone? | Aux? |
|---|---|---|---|---|
| **Now (Stage 1 running)** | Carnice 35A3B I-Nano (IQ2_K) | placeholder | yes (limited) | no — too small |
| **After Stage 1 (2026-06-10ish)** | **OmniStep** (8B, Cosmos + ASR + ACE-Step + Agentic) | the multimodal+agentic 8B | yes (full) | no — too small |
| **After Stage 3 (a few weeks)** | **Senter** (32A8B MoE) | the agentic flagship, no Ohm | yes (full) | yes (entry-level) |
| **After Stage 5 (target Q3 2026)** | **Senter Ohm** (32A8B + Ohm) | the **flagship** | yes (full) | yes (full) |

The 8B OmniStep **does not earn the aux role** — by the time the
notebook is large, you're better off escalating to Hermes directly.
The 32A8B Senter (and especially Senter Ohm) **does earn the aux
role** because the notebook machinery + multimodal I/O is real
workload. The slot is shaped by what's in it; the role is implicit
in the model.

## What runs on top of the omni-va

Three things are planned to consume the omni-va API. **All three
are future work** — the slot is currently running but not yet
federating into the rest of the stack.

### 1. Evolution Radio (planned, near-term)

A **perpetual, self-evolving generative music engine**. OmniStep
(8B) is the brain — decides what to play next based on user taste
and the notebook. ACE-Step is the voice — generates the audio. Two
evolution loops run in parallel: the brain improves via Ohm, the
voice improves via Darwin merge.

When the Senter model is in the slot, the radio also gets the
notebook + agentic routing for free (the same model that drives
the radio is the one that maintains the user's notebook).

### 2. Note-taker (planned, mid-term)

A **slimmed-down Hermes-like process** that runs in the background
and maintains the **user-idea wiki** at `~/.hermes/wiki/`. The
wiki is:

- **Persistent** (lives across sessions)
- **User-owned** (not a notebook export)
- **Curated** (the note-taker clusters, asks follow-up questions,
  prunes stale ideas — not just append-everything)
- **Opt-in to Hermes** (private by default; `hermes launch --wiki
  ~/.hermes/wiki` prepends it to a fresh Hermes session's system
  prompt)

The note-taker is **not** the pet. The pet is the Live2D face on
top. The note-taker is the writer behind the wiki.

### 3. Hermes aux (already wired, opt-in)

`~/.hermes/config.yaml` already routes **9 of 10** auxiliary tasks
to the omni-va at `http://127.0.0.1:8082/v1` with model
`carnice-35a3b`:

```yaml
auxiliary:
  vision:               # auto (2026-06-08) — see TODO 15
    provider: auto
  web_extract:          # → omni-va
    provider: custom
    model: carnice-35a3b
    base_url: http://127.0.0.1:8082/v1
  compression:          # → omni-va
    provider: custom
    model: carnice-35a3b
    base_url: http://127.0.0.1:8082/v1
  session_search:        # → omni-va
  skills_hub:            # → omni-va
  approval:              # → omni-va
  mcp:                   # → omni-va
  title_generation:      # → omni-va
  curator:               # → omni-va
```

So when a Hermes session is running, **the omni-va is already
serving as the aux for compression, web extract, session search, the
curator, etc.** Carnice is currently a placeholder (10 t/s during
training), but the wiring is in place. When Senter Ohm lands, the
same endpoints become the full-power aux at 30+ t/s.

**Note on Carnice as aux right now:** even at 10 t/s, the local aux
is faster for trivial tasks (sub-second latency) than a cloud
round-trip. The wiring makes sense even with the placeholder.

## The model swap procedure

The slot is model-agnostic. To swap what's in it:

```bash
# 1. Stop the service (cleanly, will not auto-restart)
systemctl --user stop omni-va.service

# 2. Edit the service — change the GGUF path
#    Look for: /home/sovthpaw/Models/storage/gguf/...
#    in the ExecStart line and the LLAMA_SERVER_EXTRA_ARGS env (if
#    the model name appears in --model-draft)

# 3. Reload + restart
systemctl --user daemon-reload
systemctl --user enable --now omni-va.service

# 4. Verify
curl -s http://127.0.0.1:8082/v1/models
```

The proxy automatically picks the right `--ngl` tier based on
available VRAM. No other config change needed.

## What's left to build

These are the **TODO** items tracked in
`~/spring-clean-checkpoint-2026-06-08.md`. None of them block the
slot from working today.

| What | Status | Why |
|---|---|---|
| **Wiki storage** (`~/.hermes/wiki/`) | ✅ DONE 2026-06-08 | markdown schema + sqlite-vec index TBD |
| **Note-taker process** (`~/.hermes/bin/note_taker.py`) | ✅ DONE 2026-06-09 | slim daemon, polite VRAM, sweeps every 10s |
| **`/wiki/*` endpoints on omni-va proxy** | ✅ DONE 2026-06-09 | stats / list / read / search / write (drop) |
| **`/hub/*` endpoints on omni-va proxy** | ✅ DONE 2026-06-09 | agents/list / agents/show/<name> / status |
| **`/hermes/launch` endpoint** | ✅ DONE 2026-06-09 | spawns hermes with wiki + Agent Hub agent preloaded |
| **Liquid ngl test sweep** (verified 4 tiers) | DONE 2026-06-08 | ngl 0/5/10 tested, auto-spill tested |
| **Auto-heal verified** | DONE 2026-06-08 | `systemctl stop` clean, crash auto-restart |
| **Config wired** (`~/.hermes/config.yaml`) | DONE 2026-06-08 | 9 of 10 aux tasks point to omni-va |
| **sqlite-vec index** | ✅ DONE 2026-06-09 | `wiki_embed.py` (all-MiniLM-L6-v2, CPU) + timer every 15 min |
| **Periodic Wikipedia compaction** | ✅ DONE 2026-06-09 | `wiki_compact.py` + timer every 1 hour, polite VRAM |
| **Note-taker process** (`~/.hermes/bin/note_taker.py`) | ✅ DONE 2026-06-09 | slim daemon, polite VRAM, sweeps every 10s |

## The command cheatsheet

```bash
# Service state
systemctl --user status omni-va.service

# Start (after training) / stop (during training)
systemctl --user enable --now omni-va.service
systemctl --user disable --now omni-va.service

# Watch the proxy's VRAM probe
tail -f /tmp/omni-va.log | grep -E "VRAM probe|Spawning"

# Watch the backend's stderr
tail -f /tmp/omni-va-backend.log

# Wake-on-ping (send a real request)
curl -X POST http://127.0.0.1:8082/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"carnice-35a3b","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'

# Free VRAM (after backend idle-kill)
nvidia-smi --query-gpu=memory.free --format=csv

# Swap the model
$EDITOR ~/.config/systemd/user/omni-va.service  # change GGUF path
systemctl --user daemon-reload
systemctl --user restart omni-va.service
```

## TurboFit Backend — the omni-va is now TurboFit (2026-06-21)

> **The standalone omni-va architecture described above is now powered by
> TurboFit.** All the concepts remain — wake-on-ping, liquid VRAM, auto-rotate
> tiers, the single GGUF slot — but the implementation is TurboFit.

The omni-va's two roles map directly to TurboFit commands:

| Old Concept | TurboFit Command | What it does |
|---|---|---|
| omni-va (main slot) | `turbofit serve auto main` | Picks best model for available VRAM, runs wake-on-ping proxy on :8082 |
| omni-va (aux role) | `turbofit serve auto aux` | Lighter model for Hermes aux tasks, shares GPU budget |
| Manual tier-picking | `turbofit serve downscale` | Automatically drops to a smaller model under VRAM pressure |
| Model swap procedure | `turbofit serve auto <role>` | One command — no systemd edits, no daemon-reload |

**The wake-on-ping architecture** documented above (proxy probes VRAM, picks
`--ngl` tier, spawns llama-server, kills after 30 min idle) is exactly what
TurboFit does under the hood. The proxy logic, the tier table, the auto-heal
policy — all preserved. TurboFit just makes it a single CLI instead of
hand-maintained systemd units.

**What's the same:**
- Port `:8082` for the main slot, same OpenAI-compatible `/v1/chat/completions`
- Wake-on-ping: 0 MB VRAM when idle, loads on first request
- Liquid VRAM probe at request time
- Auto-heal: `Restart=on-failure` equivalent
- Idle-kill after 30 min of no traffic

**What's different:**
- No more `omni-va.service` systemd unit — TurboFit manages the lifecycle
- `turbofit serve downscale` replaces the manual "edit the service file" swap
- The aux role (`serve auto aux`) is a first-class concept, not an afterthought
- `turbofit serve string <alias>` prints the launch string without starting — useful for debugging

**Migration from the standalone omni-va:**

```bash
# Stop the old omni-va
systemctl --user stop omni-va.service
systemctl --user disable omni-va.service

# Start TurboFit instead (picks the right model for aux)
turbofit serve auto aux

# Or for the main slot (what the radio uses)
turbofit serve auto main

# Under VRAM pressure (training, gaming)
turbofit serve downscale
```

The `~/.hermes/config.yaml` aux wiring (9 of 10 tasks pointing to
`http://127.0.0.1:8082/v1`) work unchanged — TurboFit listens on the same
port with the same API.

## See also

- [`the-omni-family.md`](./the-omni-family.md) — the canonical naming
  for the 4 OmniSenter models
- [`senter-as-hermes-auxiliary.md`](./senter-as-hermes-auxiliary.md)
  — the Senter local model server's standalone + aux role (this is
  the conceptual companion to this post)
- [`the-omnisenter-architecture.md`](./the-omnisenter-architecture.md)
  — the Senter **family** architecture (5-stage pipeline, notebook,
  Hermes integration) — different from this post which is the
  local model server specifically
- [`the-notebook-schema.md`](./the-notebook-schema.md) — the
  transient session state object that flows between Senter and Hermes
- `~/.hermes/config.yaml` (search for `auxiliary:` and `_omni_va:`)
  — the live config for the local aux wiring

---

*TOWARDS SELF-IMPROVEMENT.*
