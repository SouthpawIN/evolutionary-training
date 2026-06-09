# Omni VA (the local model server)

> **The wake-on-ping local model slot.** See the full blog post:
> [`../../blog/the-omni-va-architecture.md`](../../blog/the-omni-va-architecture.md)
>
> **Naming.** **Omni VA** is the **service** (always-on local model
> server, wake-on-ping). The **model** it currently hosts is **Carnice
> 35A3B I-Nano** (a Qwen 3.5 MoE 35B-A3B at IQ2_K) — a **placeholder**
> until Stage 1 SFT finishes, then the slot will hold **OmniStep**
> (8B) or **Senter Ohm** (32A8B). See
> [`the-omni-family.md`](../../blog/the-omni-family.md) for the
> canonical 4-model lineup. **"OmniSenter"** is the project name, not
> a model — and **"omni-va"** is the slot, not a model either.

## Naming (read first)

Per Chris (2026-06-09): the **Omni VA** is the **local model server slot**.
The **OmniStep** is the **agent** (the persona, system prompt, toolset).
They are not the same thing — the agent is the SOUL, the omni-va is
the BODY (the running process that hosts the model weights).

See [`./omni-step.md`[](./omnistep.md) for the OmniStep agent entity,
or read the master spec at `~/.hermes/hub/agents/omni-step.md`.

## Definition

**Omni VA** is a single systemd service that fronts a llama-server
instance with a wake-on-ping proxy, and hosts one model at a time
on the user's hardware. It's the bedrock of the local-side
architecture: the Evolution Radio, the note-taker, the Agent Hub,
and (when the loaded model is large enough) the auxiliary for Hermes
Agent all sit on top of it.

## The slot (one line)

```
omni-va.service (always-on, 0 VRAM when idle)
├── proxy (Python) — listens on :8082, spawns llama-server on first request
├── llama-server (the actual model)
│   ├── main model:     whatever's loaded (Carnice 35A3B I-Nano today)
│   ├── draft model:    same GGUF in MTP/NextN mode
│   ├── context:        1M tokens, turbo2 KV cache
│   ├── memory:         liquid VRAM (probe + auto-spill)
│   └── idle-kill:      30 min without traffic → SIGTERM
└── /v1/chat/completions   — OpenAI-compatible API
   /v1/embeddings          — (future)
   /wiki/*                 — user-idea wiki endpoints (future)
   /hermes/launch          — spawn Hermes with --wiki preload (future)
```

## The 4 models in the slot (timeline)

| Phase | Model | Standalone? | Aux role? |
|---|---|---|---|
| **Now (Stage 1 running)** | Carnice 35A3B I-Nano (IQ2_K) | yes (limited) | no — too small |
| **After Stage 1 (Jun 10-11)** | **OmniStep** (8B) | yes (full) | no — too small |
| **After Stage 3** | **Senter** (32A8B MoE) | yes (full) | yes (entry-level) |
| **After Stage 5** | **Senter Ohm** (32A8B + Ohm) | yes (full) | yes (full) |

The 8B OmniStep **does not earn the aux role** — by the time the
notebook is large, you're better off escalating to Hermes directly.
The 32A8B Senter (and especially Senter Ohm) **does earn the aux
role** because the notebook machinery + multimodal I/O is real
workload.

## The wake-on-ping pattern

The omni-va does **not** keep the model loaded when idle. The
proxy listens on `:8082` and only spawns the llama-server backend
on the **first** incoming request. After 30 minutes of no traffic,
the backend gets a SIGTERM and the model is killed — VRAM returns
to the rest of the system.

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
(training, IDE, browser) have the GPU to themselves when the
omni-va isn't being used.

## Liquid VRAM (the "morphin' like liquid" behavior)

The model uses as much VRAM as is available, with no forced
offload. The proxy probes free VRAM at request time and picks a
tier:

| Free VRAM | Tier | Behavior | Speed (1M ctx, IQ2_K, MTP) |
|---|---|---|---|
| < 3 GB | `ngl 0` | Pure CPU | ~4.5 t/s |
| 3-6 GB | `ngl 5` | A few layers on GPU | ~5.4 t/s |
| 6-8 GB | `ngl 10` | Half-ish on GPU | ~6 t/s |
| > 8 GB | no `-ngl` | llama.cpp auto-spill | up to 30+ t/s |

After training finishes (ETA Thu 2026-06-10 ~21:35 CDT), GPU 0
will be fully free (23.5 GB), the proxy detects > 8 GB, and the
same config switches to **auto-spill** automatically. Speed jumps
from ~10.9 t/s to **30+ t/s** with no human action.

## The auto-heal policy

A "well-behaved" service has two opposing properties:

1. **Auto-heal on crash** — if the process segfaults, OOMs, or
   otherwise dies unexpectedly, it restarts.
2. **Clean stop on intent** — if the user runs `systemctl stop`,
   it stops and stays down.

Achieved with three pieces working together:

- `~/.config/systemd/user/omni-va.service` has
  `Restart=on-failure` (not `Restart=always`), `TimeoutStopSec=30`,
  `KillMode=mixed`.
- `~/bin/llama-proxy` has a SIGTERM/SIGINT handler that terminates
  the spawned backend, then `sys.exit(0)`.
- Verified 2026-06-08: `systemctl stop` → clean in 0.03s; `kill -9`
  → auto-restart in 5s.

## The 3 consumers

Three things consume the omni-va API:

1. **Evolution Radio** — `~/projects/evolutionary-radio/`. Brain =
   omni-va, voice = ACE-Step, evolution = Darwin + GEPA. Two
   background loops.
2. **Note-taker** — a slim Hermes-like process that maintains
   `~/.hermes/wiki/`. Opt-in to Hermes via `--wiki` preload.
3. **Hermes aux** — 10 of 10 auxiliary tasks in
   `~/.hermes/config.yaml` point to `:8082/v1`. The `gold_judge`
   block pins the model.

## The command cheatsheet

```bash
# Service state
systemctl --user status omni-va.service

# Start (after training) / stop (during training)
systemctl --user enable --now omni-va.service
systemctl --user disable --now omni-va.service

# Watch the proxy's VRAM probe
tail -f /tmp/omni-va.log | grep -E "VRAM probe|Spawning"

# Wake-on-ping (send a real request)
curl -X POST http://127.0.0.1:8082/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"carnice-35a3b","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'

# Swap the model
$EDITOR ~/.config/systemd/user/omni-va.service  # change GGUF path
systemctl --user daemon-reload
systemctl --user restart omni-va.service
```

## See also

- Blog post (canonical): [`../../blog/the-omni-va-architecture.md`](../../blog/the-omni-va-architecture.md)
- Blog (the desk-pet vision): [`../../blog/evolutionary-radio-as-desk-pet.md`](../../blog/evolutionary-radio-as-desk-pet.md)
- Concept: [Omni[](../concepts/omni.md) — the umbrella multimodal family
- Concept: [OmniStep](./omnistep.md) — the 8B model that will live in the slot
- Concept: [Senter Ohm](./senter-ohm.md) — the flagship that will eventually be in the slot
- Concept: [Hermes auxiliary[](../concepts/hermes-auxiliary.md) — how the slot serves Hermes
- Concept: [Agent Hub[](../concepts/agent-hub.md) — the unified vault + wiki + slot surface
- Repo: [`SouthpawIN/evolutionary-training`](https://github.com/SouthpawIN/evolutionary-training) — main blog repo
