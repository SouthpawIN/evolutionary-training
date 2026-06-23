---
title: "Southpaw's Curated Local Models: Darwin Reason, Prism Eagle, Darwin Apex, and Carnice Apex"
date: 2026-06-10
author: Chris (via Nous Girl)
hero: assets/images/local-models-lineup.png
tags: [local-models, curated, darwin, apex, carnice, prism-eagle, dual-gpu, gguf, llama-cpp, speculative-decoding, mtp, nextn, turboquant]
summary: >
  Four local models, two RTX 3090s, one curated stack. Darwin Reason
  (28B dense, 38 tok/s) for deep thinking. Prism Eagle (27B hybrid,
  121 tok/s MTP) for fast, sharp reasoning. Darwin Apex (36B-A3B MoE,
  107 tok/s NextN) for raw speed. Carnice Apex (35A3B I-Nano,
  wake-on-ping) as the always-on assistant. Why each one earns
  its slot, how they fit together, and how to switch between them
  with one command.
related:
  - the-omni-family.md
  - the-omni-va-architecture.md
  - senter-as-hermes-auxiliary.md
  - evolutionary-radio-as-desk-pet.md
---

# Southpaw's Curated Local Models: Darwin Reason, Darwin Apex, Carnice Apex, and Prism Eagle

> **TOWARDS SELF-IMPROVEMENT** — Chris's curated local model picks, 2026-06-10

Four models. Two RTX 3090s. One `southpaw-models` command to switch
between them. This is the local inference stack that powers the
OmniSenter ecosystem — from the omni-va always-on assistant to the
radio's brain to Hermes Agent's auxiliary model.

## The lineup at a glance

| Model | Architecture | Size | GPU | Speed | Role |
|---|---|---|---|---|---|
| **Darwin Reason** | 28B dense, Q4_K_M | 16.5 GB | GPU 0 | 38 tok/s | Deep reasoning |
| **Prism Eagle** | 27B hybrid, PRISM DQ | 13.7 GB | GPU 0 (shared) | **121 tok/s** (MTP) | Fast, sharp reasoning |
| **Darwin Apex** | 36B-A3B MoE, APEX I-Compact | 17.3 GB | GPU 1 | **107 tok/s** (NextN) | Raw speed |
| **Carnice Apex** | 35A3B MoE, APEX I-Nano | 11.7 GB | GPU 0 (shared) | ~10 tok/s (PCIe) / 30+ (native) | Always-on assistant |

All four run on the same dual RTX 3090 machine via
`llama.cpp` (AtomicBot fork with turboquant + NextN MTP). The
`southpaw-models` CLI handles download, startup, health checks, and
Hermes config wiring — one command to switch presets.

---

## Darwin Reason — the deep thinker

```
Darwin-28B-REASON.Q4_K_M.gguf
16.5 GB · GPU 0 · 38 tok/s · 256K ctx (turbo4 KV)
```

Darwin Reason is the reasoning workhorse. At 28B parameters dense
(not MoE), it's the largest single-model brain in the stack — the one
you reach for when you need careful analysis, multi-step reasoning, or
code review that catches subtle bugs.

**Why it earns GPU 0:**

Darwin gets the primary GPU because it's the model Chris uses for
*thinking*, not just generating. 38 tok/s is fast enough for reading
comfort but slow enough that every token had to earn its place.
Combined with **turbo4 KV cache** (4-bit Walsh-Hadamard Transform),
it fits 256K tokens of context in just ~4 GB of KV cache — enough to
hold an entire codebase, a full conversation history, or a long
research paper in working memory.

**What it's good at:**
- Multi-step reasoning and planning
- Code review and debugging
- Long-context analysis (256K window)
- The "think first, then answer" pattern

**Technical notes:**
- `-ngl 99` — all layers on GPU
- `-c 262144 -ctk turbo4 -ctv turbo4` — 256K context with compressed KV
- `--no-mmap` — direct GPU loading, consistent latency
- Q4_K_M quant — 4-bit with medium quality preservation, 16.5 GB fits comfortably in 24 GB VRAM

Darwin Reason is the model Chris trusts for decisions. When Hermes
Agent needs an auxiliary model for deep reasoning or when the radio's
brain needs to evaluate an idea, this is the judge.

---

## Darwin Apex — the speed demon

```
Qwen3.6-35B-A3B-APEX-MTP-I-Compact.gguf
17.3 GB · GPU 1 · 107 tok/s · 256K ctx (turbo4 + NextN MTP)
```

Darwin Apex is the one you use when you want answers *now*. At
**107 tokens per second**, it reads faster than you can — a full
paragraph appears between blinks. This isn't a smaller model going
fast; it's a **35 billion parameter Mixture-of-Experts** with only
**3 billion active per token**, running on APEX quantization with
NextN speculative decoding.

**The secret sauce: APEX + NextN MTP**

APEX (Adaptive Precision EXpert quantization) is a per-expert
mixed-precision format for MoE models. Each of the model's experts
gets its own quantization tier, so the router experts (used every
token) stay high-precision while the domain experts (used rarely) can
be more aggressive. The **I-Compact** tier targets ~17 GB — the
sweet spot for a dedicated 24 GB GPU.

NextN Multi-Token Prediction takes it further: the model generates
multiple tokens per forward pass, then verifies them in a batch.
The draft model *is* the target model (unlike older Eagle-style
speculative decoding that needs a separate draft model), so there's
no quality loss. At `--draft-block-size 3`, it achieves a **77%
draft acceptance rate** — nearly 3x the throughput of vanilla
generation.

**Without NextN, Darwin Apex does ~40 tok/s. With it: 107 tok/s.**
The flag is `--spec-type nextn --draft-block-size 3`.

**Why it earns GPU 1:**

GPU 1 is the training GPU during Stage 1 SFT, but when training is
idle, Darwin Apex owns it. At 107 tok/s, it's the model for
interactive use — chat, quick lookups, the radio's music generation,
and Hermes auxiliary tasks that need speed over depth.

**What it's good at:**
- Interactive chat and quick Q&A
- Music generation for the Evolutionary Radio
- Hermes auxiliary tasks (compression, title generation, curator)
- Anything where latency matters more than perfect reasoning

**Technical notes:**
- `-ngl 99 -c 262144 -ctk turbo4 -ctv turbo4` — full GPU, 256K ctx
- `--spec-type nextn --draft-block-size 3` — the speed multiplier
- `--no-mmap` — consistent latency
- **Never** use `--cpu-moe` with this model — it drops from 107 tok/s to ~27 tok/s by offloading expert weights to system RAM

---

## Carnice Apex — the always-on assistant

```
Carnice-Qwen3.6-MoE-35B-A3B-APEX-MTP-I-Nano.gguf
11.7 GB · GPU 0 (shared) · wake-on-ping · ~10 tok/s (PCIe) / 30+ (native)
```

Carnice Apex is the **omni-va slot** model — the one that runs
24/7 as the local model server at `http://127.0.0.1:8082/v1`.
It's the same architecture as Darwin Apex (Qwen3.6 35B-A3B MoE)
but at the **I-Nano** quantization tier — 11.7 GB, small enough
to share GPU 0 alongside Darwin Reason without OOMing.

**The wake-on-ping pattern:**

Carnice doesn't sit in VRAM burning watts. The omni-va proxy
(`llama-proxy` on port 8082) keeps the slot empty until a request
arrives. On first request, it probes free VRAM, picks the right
`--ngl` tier, and loads the model. After 30 minutes of no traffic,
it unloads. During SFT training (when GPU 1 is occupied), Carnice
runs **PCIe-bound** at ~10 tok/s — slow but functional. After
training frees the GPU, it moves to full native speed at 30+ tok/s.

**The four roles:**

Carnice serves as **one model, four roles** in the OmniSenter
ecosystem:

1. **Brain** — the radio's note-taker and music curator
2. **Gold Judge** — evaluates ideas, ranks wiki entries, scores prompts
3. **Hermes Aux** — compression, title generation, web extract, curator (9 of 10 aux tasks)
4. **Wikipedia Compactor** — periodically condenses the wiki into a Hermes-preloadable summary

All four roles are the same model, same weights, same slot.
Different system prompts, same Carnice.

**Why I-Nano:**

The I-Nano tier is the smallest "safe" APEX quant — small enough to
fit alongside another model on the same GPU, but still coherent
enough for reliable judging and curation. At 11.7 GB, it leaves
~7 GB free on GPU 0 for Darwin Reason's KV cache and the OS display
(Xorg + gnome-shell).

**What it's good at:**
- Always-on availability (wake-on-ping, never fully "off")
- Multi-role serving (brain, judge, aux, compactor)
- VRAM-polite coexistence with other models
- The glue that connects the radio, wiki, note-taker, and Hermes

**Technical notes:**
- I-Nano quant — 11.7 GB, smallest APEX tier
- Runs via `omni-va.service` (systemd user service, `Restart=on-failure`)
- Wake-on-ping via `llama-proxy` — loads on first request, unloads after 30 min idle
- During training: CPU-tier, ~10 tok/s, polite defers when VRAM < 4 GB
- After training: native GPU tier, 30+ tok/s

---

## Prism Eagle — the sharp-eyed reasoner

> **Model:** [`Ex0bit/Qwen3.6-27B-PRISM-PRO-DQ`](https://huggingface.co/Ex0bit/Qwen3.6-27B-PRISM-PRO-DQ) — Apache 2.0

```
Qwen3.6-27B-PRISM-PRO-DQ.gguf
13.7 GB · GPU 0 (shared) · 121 tok/s (MTP) · 256K ctx
```

Prism Eagle is the **fast, sharp reasoning model** — a 27 billion
parameter hybrid architecture with PRISM bias removal and native MTP
speculative decoding. At **121 tokens per second** on a single GPU,
it's the second-fastest model in the stack while still being a full
27B dense model (not MoE). It thinks fast and thinks clearly.

**Why it's called Prism Eagle:**

"Prism" comes from the **PRISM project** — a post-training technique
that removes bias and propaganda from the base model while preserving
reasoning capability. The result is a model that's sharper, more
objective, and less prone to hallucinated narratives. "Eagle" is for
the **EAGLE-3 speculative decoding** it supports — a separate drafter
model that chains predictions for even faster inference (though native
MTP is actually faster in llama.cpp at 121 vs 111 tok/s).

**The hybrid architecture:**

Prism Eagle is built on Qwen3.6-27B, which uses a **hybrid attention**
design: 48 GatedDeltaNet linear-attention layers for efficient
long-context processing, plus 16 full-attention layers for complex
reasoning. This isn't a pure transformer — it's a next-gen
architecture that scales better to long contexts. Hidden size 5120,
vocabulary 248,320 tokens.

**PRISM Dynamic Quantization (DQ):**

The PRISM DQ recipe is a llama.cpp-native dynamic quantization that
preserves the model's full capabilities:
- **MTP draft head** (15 tensors) — kept at high precision for
  accurate speculative decoding
- **Full vision tower** (333 tensors) — Prism Eagle is multimodal,
  capable of vision-language tasks
- **13.7 GB total** — fits alongside Darwin Reason and Carnice Apex
  on GPU 0 with room to spare

**Speculative decoding options:**

| Mode | tok/s | Speedup | Notes |
|---|---|---|---|
| No-spec baseline | 80 | 1.00× | Solid baseline for a 27B |
| **Native MTP** | **121** | **1.51×** | Built-in draft head, fastest |
| EAGLE-3 chain | 111 | 1.39× | Separate drafter, lossless |

Native MTP is the winner — the model's built-in Multi-Token Prediction
head generates draft tokens that are verified in batch, achieving a
51% speedup with **zero quality loss** (output is token-identical to
non-speculative greedy decoding). The EAGLE-3 drafter is available
separately at `Ex0bit/Qwen3.6-27B-PRISM-EAGLE3` for setups that
prefer the chain approach.

**Quick start:**

```bash
# Baseline
./llama-server --model Qwen3.6-27B-PRISM-PRO-DQ.gguf

# Native MTP (fastest — 121 tok/s)
./llama-server --model Qwen3.6-27B-PRISM-PRO-DQ.gguf \
    --spec-type draft-mtp --spec-draft-n-max 1 --spec-draft-n-min 1
```

**Why it earns a spot:**

Prism Eagle fills the gap between Darwin Reason (deep, slow, 38 tok/s)
and Darwin Apex (fast, MoE, 107 tok/s). At 27B dense, it reasons
better than the 3B-active MoE of Darwin Apex, but at 121 tok/s it's
nearly as fast. It's the model for when you need **both speed and
depth** — code review that catches subtle bugs, research questions
that need careful answers, or agentic tasks where quality matters
but you don't want to wait.

**What it's good at:**
- Fast, sharp reasoning (121 tok/s, 27B dense)
- Bias-resistant analysis (PRISM post-training)
- Multimodal tasks (preserved vision tower)
- The "both speed and depth" sweet spot

**Technical notes:**
- PRISM DQ quant — 13.7 GB, preserves MTP head + vision tower
- Hybrid architecture: 48 DeltaNet + 16 attention layers
- `--spec-type draft-mtp` for 121 tok/s (1.51× speedup)
- Apache 2.0 license — same as base Qwen3.6-27B
- Shares GPU 0 with Darwin Reason + Carnice Apex (13.7 + 16.5 + 11.7 = 41.9 GB theoretical, wake-on-ping manages actual usage)

---

## How they fit together

```
┌─────────────────────────────────────────────────┐
│                  DUAL RTX 3090                    │
│                                                   │
│  GPU 0 (24 GB)              GPU 1 (24 GB)         │
│  ┌─────────────────┐       ┌─────────────────┐   │
│  │ Darwin Reason    │       │ Darwin Apex      │   │
│  │ 28B dense        │       │ 36B-A3B MoE      │   │
│  │ 16.5 GB          │       │ 17.3 GB          │   │
│  │ 38 tok/s         │       │ 107 tok/s        │   │
│  │ 256K ctx         │       │ 256K ctx         │   │
│  │                  │       │ NextN MTP        │   │
│  └─────────────────┘       └─────────────────┘   │
│  ┌─────────────────┐                              │
│  │ Prism Eagle      │                              │
│  │ 27B hybrid       │                              │
│  │ 13.7 GB (shared) │                              │
│  │ 121 tok/s MTP    │                              │
│  └─────────────────┘                              │
│  ┌─────────────────┐                              │
│  │ Carnice Apex     │                              │
│  │ 35A3B I-Nano     │                              │
│  │ 11.7 GB (shared) │                              │
│  │ wake-on-ping     │                              │
│  └─────────────────┘                              │
│                                                   │
│  Xorg + gnome-shell: ~3 GB                        │
│  Free (for KV cache): variable (wake-on-ping)     │
└─────────────────────────────────────────────────┘
```

Darwin Reason, Prism Eagle, and Carnice Apex **share GPU 0** — Darwin
for deep reasoning, Prism Eagle for fast sharp answers, Carnice as
the always-on multi-role assistant. With wake-on-ping, only the
actively-used models occupy VRAM. Darwin Apex gets **GPU 1**[^1] to
itself for maximum speed. During SFT training, Darwin Apex and Prism
Eagle step aside (GPU 1 is occupied, GPU 0 is tight), and Carnice
drops to CPU-tier — slow but still available.

[^1]: Darwin Apex runs on physical GPU 1, which may appear as
`CUDA0` when `CUDA_VISIBLE_DEVICES=1` is set. This is correct
behavior — the GPU index in logs is relative to the visible set.

**During training (current state, June 2026):**
- GPU 0: Darwin Reason (idle) + Prism Eagle (idle) + Carnice (PCIe-bound, ~10 tok/s)
- GPU 1: S1 SFT training (occupied, ~48s/step)

**After training (post-Stage 1):**
- GPU 0: Darwin Reason (38 tok/s) + Prism Eagle (121 tok/s MTP) + Carnice (30+ tok/s, native)
- GPU 1: Darwin Apex (107 tok/s, full speed)

---

## Switching between them

The `southpaw-models` CLI makes switching trivial:

```bash
# Full local stack (both GPUs)
southpaw-models darwin+apex

# Darwin only (GPU 0) + API aux
southpaw-models darwin

# Back to cloud API
southpaw-models api

# Check what's running
southpaw-models status

# List available presets
southpaw-models list
```

Under the hood, the CLI:
1. Auto-detects hardware and selects the right quant tier
2. Downloads GGUFs from HuggingFace on first use
3. Starts systemd services and waits for health checks
4. Updates `~/.hermes/config.yaml` to wire Hermes to the local models

The services are systemd-managed (`llama-darwin.service`,
`llama-apex.service`) with `Restart=on-failure` — they survive
crashes, reboots, and shell disconnects.

---

## Why these four?

Chris's picks follow a clear philosophy:

1. **One model for depth, one for speed, one for both.** Darwin Reason
   thinks carefully (38 tok/s, 28B dense). Prism Eagle delivers fast
   sharp reasoning (121 tok/s, 27B hybrid). Darwin Apex responds
   instantly (107 tok/s, 36B MoE). Different jobs, different models,
   same GPU budget.

2. **Always-on doesn't mean always-loaded.** Carnice Apex uses
   wake-on-ping — it's available 24/7 without wasting VRAM. When the
   radio needs a brain or Hermes needs an aux, it's there. When idle,
   the slot is empty.

3. **No cloud fallback for the judge.** The gold judge — the model
   that evaluates ideas, ranks wiki entries, and scores prompts — is
   always local. Never Gemini 3 Flash, never a cloud default. You
   trust what you run.

4. **One command to switch.** `southpaw-models darwin+apex` or
   `southpaw-models api` — the entire stack reconfigures in seconds.
   No manual config edits, no port juggling.

---

## Performance reference

| Model | Tok/s | Context | KV Type | Key Flag |
|---|---|---|---|---|
| Darwin Reason | 38 | 256K | turbo4 | `-ngl 99 --no-mmap` |
| **Prism Eagle (native MTP)** | **121** | 256K | turbo4 | `--spec-type draft-mtp` |
| Prism Eagle (no spec) | 80 | 256K | turbo4 | `-ngl 99 --no-mmap` |
| Darwin Apex (no NextN) | ~40 | 256K | turbo4 | `-ngl 99 --no-mmap` |
| Darwin Apex (NextN) | **107** | 256K | turbo4 | `--spec-type nextn --draft-block-size 3` |
| Carnice Apex (PCIe, training) | ~10 | 1M | turbo2 | `--cpu-moe -ngl 10` |
| Carnice Apex (native, post-training) | 30+ | 256K | turbo4 | `-ngl 99 --no-mmap` |

---

## TurboFit Integration — the unified backend

> **2026-06-21 update.** All four curated models are now managed by **TurboFit**.
> The `southpaw-models` CLI delegates to TurboFit under the hood. TurboFit
> IS the backend that launches, manages, and adapts these models.

The curated model catalog lives in a YAML file (`models/curated.yaml`) that
TurboFit reads to know which models are available, their GGUF paths, quant
tiers, and optimal launch flags. Each model has a **TurboFit alias** that
maps to its launch configuration:

```yaml
# models/curated.yaml (simplified)
models:
  darwin-reason:
    gguf: Darwin-28B-REASON.Q4_K_M.gguf
    gpu: 0
    ctx: 262144
    kv: turbo4
    flags: "-ngl 99 --no-mmap"
  apex-36b-i-compact:
    gguf: Qwen3.6-35B-A3B-APEX-MTP-I-Compact.gguf
    gpu: 1
    ctx: 262144
    kv: turbo4
    flags: "-ngl 99 --spec-type nextn --draft-block-size 3"
  carnice-apex-i-nano:
    gguf: Carnice-Qwen3.6-MoE-35B-A3B-APEX-MTP-I-Nano.gguf
    gpu: 0
    ctx: 1048576
    kv: turbo2
    flags: "--cpu-moe -ngl 10"
  prism-eagle:
    gguf: Qwen3.6-27B-PRISM-PRO-DQ.gguf
    gpu: 0
    ctx: 262144
    kv: turbo4
    flags: "-ngl 99 --spec-type draft-mtp"
```

**TurboFit commands for the curated models:**

```bash
# Launch a specific curated model by its alias
turbofit serve darwin-reason          # GPU 0, deep reasoning
turbofit serve apex-36b-i-compact     # GPU 1, 107 tok/s speed
turbofit serve carnice-apex-i-nano    # GPU 0, always-on assistant
turbofit serve prism-eagle            # GPU 0, 121 tok/s sharp reasoning

# Auto-pick the best model for available VRAM
turbofit serve auto main              # main slot (radio brain, gold judge)
turbofit serve auto aux               # aux slot (Hermes compression, titles, etc.)

# Print the full llama-server launch string WITHOUT starting it
# (useful for debugging, scripting, or seeing exactly what flags apply)
turbofit serve string darwin-reason
turbofit serve string apex-36b-i-compact
turbofit serve string prism-eagle

# Adapt under VRAM pressure — drops to a smaller model automatically
turbofit serve downscale
```

**`serve downscale`** is the key feature for the dual-GPU setup. When training
starts on GPU 1 or a game eats GPU 0, TurboFit automatically swaps to a smaller
model from the catalog rather than crashing or OOMing. The radio keeps playing
music, Hermes keeps compressing — just at a smaller model tier. When VRAM frees
up, `serve auto` scales back up.

**`serve string <alias>`** is the debugging cheat code. It prints the exact
`llama-server` command that would run, with all flags resolved from the YAML
catalog, without actually launching anything. Use it to verify quant tiers,
check GPU assignment, or copy the command into a custom script.

```bash
$ turbofit serve string apex-36b-i-compact
CUDA_VISIBLE_DEVICES=1 /opt/llama.cpp/llama-server \
  --model /home/sovthpaw/Models/storage/gguf/Qwen3.6-35B-A3B-APEX-MTP-I-Compact.gguf \
  -ngl 99 -c 262144 -ctk turbo4 -ctv turbo4 \
  --spec-type nextn --draft-block-size 3 \
  --port 11501 --no-mmap
```

## The reading order

1. This post — the curated model picks
2. [`the-omni-va-architecture.md`](./the-omni-va-architecture.md) —
   the local model server that runs Carnice (now powered by TurboFit)
3. [`evolutionary-radio-as-desk-pet.md`](./evolutionary-radio-as-desk-pet.md) —
   how these models power the radio + wiki + note-taker
4. [`senter-as-hermes-auxiliary.md`](./senter-as-hermes-auxiliary.md)
   — Darwin Reason + Darwin Apex as Hermes auxiliaries

If you want to **run these yourself:**

```bash
# Clone the tooling
git clone https://github.com/SouthpawIN/southpaw-turbohaul
cd southpaw-turbohaul && bash install.sh

# Start the full stack (TurboFit handles everything now)
southpaw-models darwin+apex

# Or use TurboFit directly
turbofit serve auto main              # best model for main slot
turbofit serve auto aux               # best model for aux slot
turbofit serve string darwin-reason   # see exact launch command

# Verify
curl http://127.0.0.1:11500/v1/models  # Darwin Reason
curl http://127.0.0.1:11501/v1/models  # Darwin Apex
```

---

*TOWARDS SELF-IMPROVEMENT.*

— Chris (via Nous Girl), 2026-06-10
