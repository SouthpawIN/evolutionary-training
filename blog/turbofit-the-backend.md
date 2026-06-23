---
title: "TurboFit: The Unified Local LLM Backend"
date: 2026-06-22
author: Chris (via Nous Girl)
hero: assets/turbofit-concept.png
tags: [turbofit, llm-backend, local-llm, cuda, llama-cpp, unified-backend, evolutionary-radio]
related:
  - the-omni-va-architecture.md
  - evolutionary-radio-as-desk-pet.md
  - southpaw-curated-local-models.md
summary: >
  TurboFit v5 is the opinionated unified local LLM backend for the entire
  SouthpawIN ecosystem. One command (`serve auto main`) picks the best model
  for your hardware, launches it detached, wires Hermes config, and you're
  done. It replaces llama-launch, omni-va scripts, and every ad-hoc
  start-*.sh in the fleet. The catalog schema supports per-model binary pinning,
  named flag presets, a 5-tier quality ladder, and the 64K context floor.
  TurboFit is THE backend for evolutionary-radio, the omni-va slot,
  Hermes Agent auxiliaries, and every project that needs a local model
  running without ceremony.
---

# TurboFit: The Unified Local LLM Backend

> **TOWARDS SELF-IMPROVEMENT** — Chris's unified local inference backend, 2026-06-22

You have 23 models on disk. Two GPUs. A radio that needs a brain. A
Hermes Agent that needs an auxiliary. An omni-va that needs to stay
alive. A training run that needs all VRAM back. And six different
bash scripts that start things on different ports with different
flags.

Stop.

TurboFit v5 is the one backend that replaces all of it.

```bash
serve auto main    # picks the best model, launches, wires Hermes. Done.
```

That's the whole pitch. Everything below is why this works and what
it replaces.

---

## What TurboFit replaces

Before v5, the local inference stack was a zoo:

| Tool | What it did | Why it's gone |
|---|---|---|
| `llama-launch` | Multi-launcher CLI (llama.cpp / Ollama / vLLM / SGlang) | Catalog is now `~/.config/turbofit/models.yaml`, launches are `serve <alias>` |
| `omni-va.service` scripts | Wake-on-ping proxy for Carnice slot | The slot pattern is now part of the scaling ladder |
| `start-qwen-server.sh` | Hand-written launch for Qwen 27B | Absorbed into catalog presets |
| `start-glm-server.sh` | Hand-written launch for GLM | Absorbed |
| `start-darwin.sh` / `start-apex.sh` | Per-model wrappers | Replaced by `serve darwin-28b-reason`, `serve darwin-apex-36b-i-compact` |
| `southpaw-models` CLI | Curated picks with auto-download | Reads stale 2-entry YAML — catalog is turbofit's now |
| Manual `llama-server` invocations | Direct flag soup | Never again |

**23 models. One catalog. One command to launch any of them.
One auto-picker that decides which model should be the main. One
scaling ladder that adapts when VRAM gets tight.**

---

## The one command (`serve auto main`)

```bash
# Source the shim (one-time setup, already in ~/.bashrc)
source ~/.hermes/skills/turbofit/scripts/turbofit.sharco

# The whole story:
serve auto main        # pick best main, launch detached, wire Hermes
```

Here's what `serve auto main` actually does:

1. **Probes** your GPU state (free VRAM, GPU count, CUDA devices)
2. **Filters** the catalog by `role: main` (or `either`)
3. **Filters** by context floor — every entry must support ≥ 65536 tokens
4. **Filters** by vision requirement (if `--vision` flag passed)
5. **Sorts** by tier ladder: `s → sf → sd → f → c` (smartest first,
   then smart+fast, smart+dense, fast, cheap)
6. **Breaks ties** by `featured: true` (your starred picks), then by
   `tok_s_target` (measured throughput, descending)
7. **Skips** entries whose GGUF file doesn't exist on disk
8. **Launches** via the per-model `binary:` if set (atomic fork for
   TurboQuant/NextN models), else stock `llama-server`
9. **Wires** Hermes Agent config — points `local_model` at the new
   port, sets the model name, restarts the connection

The user types one line. The system figures out the rest.

```bash
serve auto main --vision     # require vision capability
AUTO_CTX=131072 serve auto main  # raise context target to 128K
serve auto aux               # pick best auxiliary model
```

---

## The catalog: `~/.config/turbofit/models.yaml`

This is the source of truth. 23 entries, 7 featured picks, 5 tiers.
Every local model launch reads this file.

### Anatomy of a catalog entry

Here's what a real entry looks like — Darwin Reason, the smartest
27B dense model in the fleet:

```yaml
darwin-28b-reason:
  # Required
  launcher: llama-cpp
  path: /home/sovthpaw/Models/storage/gguf/Darwin-28B-REASON.Q4_K_M.gguf
  port: 11500

  # Recommended
  ctx: 262144
  gpu: 0
  binary: /home/sovthpaw/projects/LLM-Infra/llama.cpp-atomic/build/bin/llama-server
  presets: [turbo4-kv, no-mmap, split-none, gpu0]
  extra_args: []
  aliases: [darwin, darwin-reason, reason-28b]
  description: "Darwin 28B Reason (Q4_K_M, 16.6GB) — smartest 27B dense"

  # Opinionated metadata (used by auto-picker and Garage UI)
  tier: s
  featured: true
  tok_s_target: 38
  vision: false
  size_gb: 16.6
  hf_repo: mradermacher/Darwin-28B-REASON-GGUF
  role: main
```

### The five tiers

| Tier | Meaning | Examples | When |
|---|---|---|---|
| `s` | Smartest | Darwin Reason, Darwin Apex, Prism Eagle | Deep reasoning, coding review |
| `sf` | Smart + fast | Carwin-MTP, Qwopus v2-MTP, Qwopus Coder-MTP | Fast sharp work |
| `sd` | Smart + dense | Carnice Apex Compact | Always-on assistant |
| `f` | Fast | Qwable MTP, Qwopus abliterated-MTP | Quick answers |
| `c` | Cheap | Qwen legacy, devstral, step-flash, omni-3b | Last resort, tight VRAM |

The auto-picker walks this ladder top-down and picks the first model
that fits. Under VRAM pressure, you naturally fall to lower tiers.

### The featured 7

These are Chris's hand-picked models — the ones that earn a star in
the Garage UI:

| # | Model | Tier | Speed | GPU | Role |
|---|---|---|---|---|---|
| 1 | **Darwin Reason** | s | 38 tok/s | 0 | Deep reasoning main |
| 2 | **Darwin Apex** | s | 107 tok/s | 1 | Raw speed main (MoE) |
| 3 | **Prism Eagle** | s | 121 tok/s | 0 | Fast sharp reasoning |
| 4 | **Carwin MTP** | sf | ~100 tok/s | 1 | Multimodal main + vision |
| 5 | **Qwopus v2 MTP** | sf | ~100 tok/s | 0 | Fast MTP main |
| 6 | **Qwopus Coder MTP** | sf | ~90 tok/s | 0 | Code-specialized MTP |
| 7 | **Carnice Apex** | sd | 30+ tok/s | 1 | Always-on aux |

All 7 have `featured: true` in the catalog. The Garage web UI
at `:11402` surfaces them in a ⭐ Featured section above the full
list.

---

## Named flag presets

No more memorizing launch flags. TurboFit has 14 named presets that
merge cleanly into any launch:

| Preset | Expands to |
|---|---|
| `nextn` | `--spec-type nextn --draft-block-size 3` |
| `nextn-tight` | `--spec-type nextn --draft-block-size 2` |
| `draft-mtp` | `--spec-type draft-mtp` |
| `draft-mtp-tight` | `--spec-type draft-mtp --draft-block-size 2` |
| `turbo4-kv` | `-ctk turbo4 -ctv turbo4` |
| `turbo3-kv` | `-ctk turbo3 -ctv turbo3` |
| `turbo2-kv` | `-ctk turbo2 -ctv turbo2` |
| `q8-kv` | `-ctk q8_0 -ctv q8_0` |
| `q4-kv` | `-ctk q4_0 -ctv q4_0` |
| `no-mmap` | `--no-mmap` |
| `split-none` | `--split-mode none` |
| `mlock` | `--mlock` |
| `gpu0` | `--main-gpu 0 --device CUDA0` |
| `gpu1` | `--main-gpu 1 --device CUDA1` |

Presets combine: `presets: [nextn, turbo4-kv, no-mmap, gpu1]`
generates a launch string with speculative decoding, turbo4 KV cache,
no memory-mapping, and GPU 1 targeting.

This is what killed the six `start-*.sh` scripts. Every model's
optimal flags are just a list of preset names.

### Speculative decoding: nextn vs draft-mtp

Both enable Multi-Token Prediction but target different model
families. They are **not interchangeable**.

| Flag | Used by | Mechanism |
|---|---|---|
| `nextn` | Darwin Apex, Carwin, Qwopus (Qwen MoE/MTP family) | AtomicBot fork NextN, 77%+ draft acceptance |
| `draft-mtp` | Prism Eagle, Qwable (Qwen dense MTP) | Native MTP draft head, 1.51× speedup |

Using the wrong flag gives either no speedup or garbled output. The
catalog gets this right for every entry.

---

## Per-model binary: atomic fork vs stock

This is the detail that matters most. Some models need capabilities
that stock llama.cpp doesn't have:

- **TurboQuant KV cache** (`-ctk turbo4`) — requires the AtomicBot fork
- **NextN speculative decoding** (`--spec-type nextn`) — requires the AtomicBot fork

If you try to launch Darwin Reason with stock `llama-server`, you get:

```
error: unsupported cache type: turbo4
```

The fix is the `binary:` field in the catalog:

```yaml
darwin-28b-reason:
  binary: /home/sovthpaw/projects/LLM-Infra/llama.cpp-atomic/build/bin/llama-server
```

TurboFit uses this path when launching. Models that don't need TurboQuant
or NextN (devstral, step-flash, nomic-embed) use the stock binary —
either from PATH or from a pinned `llama.cpp/build/bin/llama-server`.

**Rule of thumb:**

| Model family | Needs atomic fork? | Why |
|---|---|---|
| Darwin (Reason, Apex) | Yes | TurboQuant + NextN |
| Prism Eagle | Yes | TurboQuant + draft-MTP |
| Carnice | Yes | TurboQuant + NextN (MoE) |
| Carwin | Yes | TurboQuant + NextN |
| Qwopus (all variants) | Yes | TurboQuant + NextN |
| Qwable (MTP variants) | Yes | TurboQuant + NextN |
| Qwen legacy, Devstral, Step-Flash | No | Stock llama.cpp is fine |
| nomic-embed | No | Embedding mode only |

---

## The scaling ladder

This is the opinion that makes TurboFit different from every other
model launcher. When VRAM gets tight, TurboFit doesn't crash — it
adapts.

```bash
serve downscale    # probes VRAM, picks the right step
```

| Free VRAM | Action | User Impact |
|---|---|---|
| > 14 GB | No change | Full context, full aux |
| 8–14 GB | Stop aux | Main keeps full context, vision drops |
| 4–8 GB | Stop aux, shrink main ctx to 64K | Smaller context window |
| < 4 GB | Stop all, swap main to c-tier | Small model, possibly CPU offload |

**When would you hit each step?**

- **14+ GB free:** Normal operation. Both GPUs loaded, 256K context,
  aux model running for vision/embedding.
- **8–14 GB:** Training started on one GPU. Aux model (Carnice,
  nomic-embed) gets stopped. Main model (Darwin Reason) keeps running
  at full context.
- **4–8 GB:** Heavy training or a large batch job. Main model stays up
  but drops from 256K to 64K context — KV cache shrinks ~4×, freeing
  VRAM. Hermes Agent still works (64K is the hard floor).
- **< 4 GB:** SFT training running on both GPUs. Everything stops.
  TurboFit auto-picks a c-tier model that fits — step-flash (4 GB),
  qwen-omni-3b, or falls back to nomic-embed (embedding only).

The ladder never kills a model mid-response. It only adapts between
requests.

### Planned additions

| Feature | Status | Why |
|---|---|---|
| Push mode (cron) | Planned | Auto-trigger ladder when VRAM drops |
| MoE expert offload | Planned | `--cpu-moe` as a ladder step |
| Quant downgrade | Planned | Q4 → Q3 → Q2 when desperate |
| Wake-on-ping for aux | Planned | On-demand loading instead of always-resident |
| Per-GPU ladder | Planned | Drop model on stressed GPU, keep other alive |

---

## How TurboFit powers Evolutionary Radio

The radio needs a brain. The brain is a local model. Before TurboFit,
`start_radio.sh` had to:

1. Call `systemctl --user enable --now omni-va.service`
2. Wait for the health check
3. Hope the right model was loaded
4. Manually set the port

Now the radio does:

```bash
serve auto main
# radio.py connects to whatever port TurboFit wired up
```

The radio's `Brain` class — the local model that decides what to
play next, curates wiki entries, and judges ideas — talks to
whichever model `serve auto main` chose. If VRAM is tight because
the SFT training is running, the radio uses `polite_chat()` to
defer generation. If VRAM recovers, TurboFit has already adapted
the model to fit.

**The radio doesn't care which model is the brain.** It just needs an
OpenAI-compatible API on some port. TurboFit guarantees that.

```python
# radio.py — the brain connection
client = OmniClient(
    base_url=os.environ.get("BRAIN_URL", "http://127.0.0.1:11500/v1"),
    model=os.environ.get("BRAIN_MODEL", "auto"),
    timeout=120,
)

# Polite chat — defer if VRAM is tight
result = client.polite_chat(
    messages=[{"role": "user", "content": vibe}],
    min_free_gb=4.0,
)
```

TurboFit owns the server lifecycle. The radio owns the queue. They
communicate over HTTP. Clean separation, no shared state.

### The radio kill order

When training starts and VRAM is needed back:

```bash
# 1. TurboFit adapts the fleet
serve downscale

# 2. Radio detects the brain is gone (or VRAM-polite defers)
# 3. Training proceeds with full GPU access

# When training finishes:
serve auto main    # brain comes back, radio resumes
```

No manual intervention. No `kill -9`. No port conflicts.

---

## Hermes Agent integration

TurboFit doesn't just launch models — it wires them into the rest of
the stack.

```bash
serve main darwin-28b-reason --ui tui     # wire as Hermes main
serve aux carwin-28b-mtp --ui tui         # wire as Hermes auxiliary
serve herm darwin-28b-reason              # launch + main + hermes + herm TUI
```

The `--ui` flag controls which Hermes interface gets the connection:

| UI target | What happens |
|---|---|
| `tui` | Hermes TUI config (local model pointer) |
| `dashboard` | Web dashboard config |
| `gateway` | Gateway routing config |
| `desktop` | Desktop app config |
| `herm` | herm terminal config |

This eliminates the most common failure mode: launching a model and
forgetting to update the config that points at it.

### The 64K context floor

Every TurboFit launch enforces `ctx >= 65536`. This is not optional.

Hermes Agent needs at least 64K tokens to initialize its system
prompt, tool definitions, and first conversation turn. On a model
with 32K context, Hermes crashes on the first multi-turn message.

The catalog's `ctx:` field and the `serve auto` filter guarantee this.
Even at the lowest ladder step (c-tier, < 4 GB free), the context
stays at 64K.

```bash
serve string any-alias    # preview the launch string — ctx is always ≥ 65536
```

---

## VRAM probing

```bash
serve vram
```

Output:

```json
{
  "gpu_count": 2,
  "total_MiB": 49152,
  "used_MiB": 46085,
  "free_MiB": 3067,
  "free_GB": 3.0,
  "per_gpu_free_MiB": [2611, 456]
}
```

This is the raw data the auto-picker and scaling ladder use. Run it
anytime to check your GPU state before launching something heavy.

---

## The command reference

### Install and update

```bash
serve install                    # llama.cpp from source (respects binary: field)
serve install ollama             # specific launcher
serve update                     # update llama.cpp
serve update all                 # all launchers
serve check                      # version status
```

### Catalog management

```bash
serve catalog                    # show all registered (featured first, tier-ordered)
serve register <alias> <path>    # add a model
          [--launcher llama-cpp] [--port 11530]
```

### Launch and stop

```bash
serve <alias>                    # launch detached
serve string <alias>             # print launch string, don't launch
serve stop <alias>               # stop a running server
serve stop-all                   # stop everything
serve list                       # list running + detect rogue processes
```

### Opinionated auto

```bash
serve auto main                  # pick best main, launch, wire Hermes
serve auto main --vision         # require vision
serve auto aux                   # pick best aux
serve downscale                  # adapt to VRAM pressure
AUTO_CTX=131072 serve auto main  # raise ctx target
```

### Hermes routing

```bash
serve main <alias> [--ui ...]   # wire as main
serve aux <alias> [--ui ...]    # wire as auxiliary
serve herm <alias>              # full herm stack launch
```

### NVIDIA NIM (curated API fallback)

```bash
serve api list                  # show available NVIDIA models
serve api use <rank> [main|aux] # wire a cloud API model
```

The NIM models have free endpoints (1000 RPM, no credit card) for when
you need bigger models than your hardware can run. Same Hermes
integration — just points at a different URL.

---

## Adding a model to the fleet

```bash
# 1. Register the GGUF
name mymodel /path/to/file.gguf --port 11530

# 2. Edit the catalog to add metadata
$EDITOR ~/.config/turbofit/models.yaml
# Add: tier, presets, gpu, binary, featured, tok_s_target, vision, role

# 3. Verify it parses and the file exists
python3 -c "
import yaml, os
cfg = yaml.safe_load(open('$HOME/.config/turbofit/models.yaml'))
m = cfg['models']['mymodel']
assert os.path.exists(m['path']), 'GGUF missing'
print('OK —', m['path'], '@', m['port'])
"

# 4. Preview the launch string
serve string mymodel

# 5. Launch when ready
serve mymodel
```

### Example: adding a new Qwen variant

```yaml
qwable-27b-mtp:
  launcher: llama-cpp
  path: /home/sovthpaw/Models/storage/gguf/Qwable-27B-MTP.Q4_K_M.gguf
  port: 11525
  ctx: 262144
  gpu: 0
  binary: /home/sovthpaw/projects/LLM-Infra/llama.cpp-atomic/build/bin/llama-server
  presets: [nextn, turbo4-kv, no-mmap, gpu0]
  aliases: [qwable, qwable-mtp]
  description: "Qwable 27B MTP — Fable-5 reasoning + MTP, ~95 tok/s"
  tier: sf
  featured: false
  tok_s_target: 95
  vision: false
  size_gb: 16.2
  hf_repo: Mia-AiLab/Qwable-27B-MTP-GGUF
  role: main
```

The `binary:` pin is critical here — without it, stock llama.cpp
errors on turbo4 and nextn.

---

## The 23-entry fleet (overview)

| # | Alias | Size | Tier | Tok/s | GPU | Role | Notable |
|---|---|---|---|---|---|---|---|
| 1 | darwin-28b-reason | 16.6 GB | s | 38 | 0 | main | Smartest dense |
| 2 | darwin-apex-36b-i-compact | 16.0 GB | s | 107 | 1 | main | MoE speed king |
| 3 | prism-eagle-27b | 13.7 GB | s | 121 | 0 | main | Fastest 27B |
| 4 | carwin-28b-mtp | 16.8 GB | sf | ~100 | 1 | main | Multimodal |
| 5 | qwopus-27b-v2-mtp | ~15 GB | sf | ~100 | 0 | main | Speed-optimized |
| 6 | qwopus-27b-coder-mtp | ~15 GB | sf | ~90 | 0 | main | Code-specialized |
| 7 | carnice-apex-35a3b-compact | 11.7 GB | sd | 30+ | 1 | aux | Always-on |
| 8 | qwable-27b-base | ~15 GB | f | ~80 | 0 | main | Reasoning base |
| 9 | qwable-27b-mtp | ~15 GB | f | ~95 | 0 | main | Fable-5 reasoning |
| 10 | qwable-27b-abliterated | ~15 GB | f | ~80 | 0 | main | Uncensored |
| 11 | qwable-27b-abliterated-mtp | ~15 GB | f | ~90 | 0 | main | Uncensored + MTP |
| 12 | qwopus-27b-v2 | ~15 GB | f | ~80 | 0 | main | Jackrong base |
| 13 | qwopus-27b-abliterated-mtp | ~15 GB | f | ~90 | 0 | main | PiehSoft uncensored |
| 14 | qwen3-coder-next | ~15 GB | f | ~70 | 0 | main | IQ4_NL coder |
| 15 | qwen3-coder-30b-a3b | ~12 GB | f | ~85 | 1 | main | MoE coder |
| 16 | qwen3.5-35b-a3b | ~12 GB | c | ~60 | 1 | aux | General MoE |
| 17 | qwen2.5-omni-3b | ~3 GB | c | ~100 | 0 | aux | Small multimodal |
| 18 | devstral-24b | 14.0 GB | c | ~50 | 0 | aux | Mistral code |
| 19 | step-3.5-flash | 4.0 GB | c | ~80 | 0 | aux | StepFun fast |
| 20 | nomic-embed | 0.3 GB | c | - | 0 | aux | Embedding only |
| 21–23 | jackrong-* / sushi-* | varies | f/c | varies | 0/1 | aux | Distilled Qwen |

**12 Omni\*/Senter\* training artifacts excluded.** These are
user-made Darwin-merged models used for training research, not
production fleet picks. Add them back with `name <alias> <path>` if
needed.

---

## The turbo4 KV cache story

This matters for anyone running 256K context on 24 GB GPUs.

| KV Type | Bits | 256K KV Size (40L model) | Fits on 3090? |
|---|---|---|---|
| f16 | 16 | ~16 GB | ❌ alone |
| q4_0 | 4 | ~4 GB | ✅ tight |
| turbo3 | 3 | ~3 GB | ✅ but lower quality |
| **turbo4** | **4** | **~4 GB** | **✅ best quality** |

Turbo4 is Walsh-Hadamard Transform KV quantization from the AtomicBot
fork. It compresses KV cache by ~4× vs f16 while maintaining
better quality than turbo3. This is what makes 256K context viable on
consumer GPUs.

**It requires the atomic fork.** Stock llama.cpp doesn't know what
turbo4 is. The `binary:` field in the catalog routes to the right
executable automatically.

---

## The `--no-mmap` story

Every catalog entry includes `no-mmap` in its presets. Here's why:

`--no-mmap` forces the model to load into GPU memory directly instead
of memory-mapping the file. Without it:

- OS page cache handles the file
- First access triggers page faults
- Inference has unpredictable latency spikes
- Turbo4 KV allocation races with page fault handling

With `--no-mmap`:

- Model loads directly to GPU (slower initial load, 30–90s)
- No page faults during inference
- Consistent latency
- Stable VRAM accounting

The trade-off: initial load is slower. But you load once and
serve for hours. The consistent inference latency is worth it.

---

## Architecture: where TurboFit fits

```
┌──────────────────────────────────────────────────────────────┐
│                    SouthpawIN Ecosystem                        │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │ Evolutionary   │  │ Hermes Agent   │  │ Garage Web UI  │  │
│  │ Radio          │  │ (main + aux)   │  │ (:11402)       │  │
│  │ (brain client) │  │                │  │                │  │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘  │
│          │                   │                    │            │
│          └───────────────────┼────────────────────┘            │
│                              │                                 │
│                     ┌────────┴────────┐                        │
│                     │   TurboFit v5   │                        │
│                     │                 │                        │
│                     │ serve auto main │                        │
│                     │ serve downscale│                        │
│                     │ serve vram      │                        │
│                     │ serve catalog   │                        │
│                     └────────┬────────┘                        │
│                              │                                 │
│              ┌───────────────┼───────────────┐                │
│              ▼               ▼               ▼                │
│       ┌───────────┐   ┌───────────┐   ┌───────────┐          │
│       │ llama-cpp │   │  Ollama   │   │   vLLM    │          │
│       │ (atomic)  │   │           │   │           │          │
│       └───────────┘   └───────────┘   └───────────┘          │
│              │               │               │                │
│              ▼               ▼               ▼                │
│          ┌──────────────────────────────────────┐             │
│          │  GPU 0 (RTX 3090, 24 GB)             │             │
│          │  GPU 1 (RTX 3090, 24 GB)             │             │
│          └──────────────────────────────────────┘             │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

TurboFit is the **control plane**. It doesn't run inference itself.
It manages llama.cpp instances (the primary backend), with Ollama,
vLLM, and SGlang as alternatives for models that need them.

The consumers (radio, Hermes, Garage) talk to TurboFit's launched
servers via standard OpenAI-compatible HTTP APIs. They don't know
which model is loaded, which GPU it's on, or what flags were used.
They just hit `http://127.0.0.1:<port>/v1/chat/completions`.

---

## Why one backend, not many

The old approach (llama-launch + omni-va + shell scripts) had a
fundamental problem: **state was scattered**.

| Old way | Problem |
|---|---|
| llama-launch catalog | `~/.config/llama-launch/models.yaml` — 36 entries, stale |
| omni-va service | Hardcoded model path, hardcoded flags |
| start-qwen-server.sh | Flags drift from actual best practices |
| Manual invocations | No record of what's running |

TurboFit's single catalog solves all of these:

- **One file** (`~/.config/turbofit/models.yaml`) holds every model
- **One command** (`serve`) is the entry point for every action
- **One scaling ladder** adapts the whole fleet to VRAM pressure
- **One auto-picker** makes the opinionated choice without user input

The 23 entries are curated to exclude the 12 training artifacts that
would only confuse the auto-picker. What's left is a clean,
production-ready fleet.

---

## Pitfalls

Things I got wrong before TurboFit made them impossible:

### 1. `serve` in PATH is Ray's CLI

Ray ships a `serve` Python script at `~/.local/bin/serve`. The
TurboFit bash shim overrides it as a function. If you bypass the
shim (new terminal, not sourced), you'll hit Ray's error.

**Fix:** Keep `source ~/.hermes/skills/turbofit/scripts/turbofit.sharco`
in your `.bashrc`.

### 2. `--gpu` is not a valid llama.cpp flag

Use `-ngl N` to control GPU layers, or `--device CUDA0` +
`--main-gpu 0` for device selection. The catalog's `gpu:` field maps
to `--main-gpu N` automatically via the `gpu0` / `gpu1` presets.

### 3. `flash_attn` is tri-state

`-fa on` / `-fa off` / `-fa auto`. Bare `--flash-attn` errors out
in newer llama.cpp versions.

### 4. Context < 64K kills Hermes

Hermes Agent crashes on first multi-turn message if context is below
64K. TurboFit enforces the floor everywhere. If you manually edit the
catalog and set `ctx: 32768`, the auto-picker will still refuse to
launch it (filter step 3).

### 5. NVIDIA NIM has two tiers

Free (1000 RPM, no credit card at `build.nvidia.com`) and paid
serverless (same model IDs, same base URL, same API key). The free
tier is what `serve api list` shows. Both work, but free has
tighter rate limits.

### 6. The 12 excluded training artifacts

These Darwin-merged models (OmniStep-SFT, OmniSenter-base-16b,
omni-step-6a3b, etc.) are excluded from the catalog because they're
training research, not production picks. They live in the legacy
`llama-launch` catalog. Add them back with `name <alias> <path>`
if you need them.

### 7. Restart=always prevents clean kills

If you're running models via systemd with `Restart=always`, a
`kill -9` instantly respawns the process. Use `systemctl --user
stop` or `serve stop` instead. TurboFit's `serve stop-all` handles
both systemd and bare processes.

---

## The opinionated defaults

Here's the summary of every opinion TurboFit makes for you:

| Decision | Value | Why |
|---|---|---|
| Context floor | **65536** tokens | Hermes Agent requirement |
| Tok/s floor | **25** tok/s (main) | Spec decoding needs this baseline |
| Prefer vision on main | **Yes** | Vision is more useful on the primary model |
| Tier ladder order | `s → sf → sd → f → c` | Smartest first, cheapest last |
| Scale down triggers | 14 GB → 8 GB → 4 GB | Three-step VRAM cascade |
| Per-model binary | Atomic fork for TurboQuant+NextN | Stock llama.cpp can't run these |
| KV cache type | turbo4 (when available) | Best quality/VRAM ratio at 256K |
| Memory mode | no-mmap | Consistent inference latency |
| Split mode | none (single GPU) | Avoid layer-split complexity |
| Flash attention | auto | Let llama.cpp decide per-model |

---

## Reading order

If you're exploring the SouthpawIN local stack:

1. **This post** — TurboFit is the backend everything runs on
2. [`southpaw-curated-local-models.md`](./southpaw-curated-local-models.md) — why these specific models
3. [`the-omni-va-architecture.md`](./the-omni-va-architecture.md) — the wake-on-ping slot pattern
4. [`evolutionary-radio-as-desk-pet.md`](./evolutionary-radio-as-desk-pet.md) — the radio as the consumer

---

## The future

TurboFit v5 is the opinionated backend. What's coming:

| Feature | When | What it adds |
|---|---|---|
| Push mode | Q3 2026 | Cron watches VRAM, triggers `downscale` automatically |
| GGUF auto-fetch | Planned | `serve fetch <alias>` downloads from `hf_repo` |
| Quant ladder | Planned | Auto-downgrade Q4 → Q3 → Q2 under extreme pressure |
| MoE expert offload | Planned | `--cpu-moe` as a ladder step (save ~8 GB, cost 3× speed) |
| Wake-on-ping native | Planned | Built into TurboFit (currently omni-va pattern) |
| Garage native | Planned | Garage UI becomes a TurboFit subcommand |

The goal is the same: **type one command, the system figures out the
rest.** The backend adapts to your hardware, your VRAM pressure, and
your current workload without manual intervention.

---

## Quick reference card

```bash
# Launch
serve auto main                    # opinionated auto-pick
serve auto main --vision           # with vision
serve auto aux                     # auxiliary model
serve darwin-28b-reason            # specific model
serve string darwin-28b-reason     # preview, don't launch

# Manage
serve catalog                      # browse all 23 entries
serve vram                         # GPU state
serve list                         # what's running
serve downscale                    # adapt to VRAM pressure
serve stop-all                     # kill everything

# Wire
serve main <alias> --ui tui        # Hermes main
serve aux <alias> --ui tui         # Hermes auxiliary
serve herm <alias>                 # full stack launch

# Maintenance
serve install                      # install/update backends
serve update                       # update llama.cpp
serve check                        # version status
serve register <alias> <path>      # add new model
```

---

*TOWARDS SELF-IMPROVEMENT.*

— Chris (via Nous Girl), 2026-06-22
