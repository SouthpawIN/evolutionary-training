# 🧬 Southpaw's Evolutionary AI Architecture — Full Breakdown

*A connected ecosystem of models, agents, and self-evolving pipelines built on the Darwin Family technique, designed for edge deployment and integrated with Hermes Agent.*

---

## Overview

This document describes the complete architecture for a series of interconnected AI projects that share a common foundation: **Darwin Family evolutionary merging** (arXiv:2605.14386, Kim et al., 2026) applied to multimodal, agentic models that operate within the **Hermes Agent** framework.

The system is designed to be **self-improving** — models continuously evolve through genome recombination, benchmark themselves, and replace their own weights when better versions are found. No manual intervention required.

---

## 🏗️ Project 1: Local Model Server

### Purpose
A unified, always-on local inference server running Chris's hand-picked fine-tunes of his favorite architectures. Two models on two GPUs, auto-starting on first request, auto-killing after idle.

### Models

| Slot | Model | Quant | GPU | Context | Special |
|------|-------|-------|-----|---------|---------|
| **Main** | [Darwin-28B-REASON](https://huggingface.co/FINAL-Bench/Darwin-28B-REASON) | Q4_K_M (16.6GB) | GPU 0 | 262K | Flash Attention, Q4 KV cache |
| **Aux** | [Qwen3.6-35B-A3B-APEX-MTP](https://huggingface.co/mudler/Qwen3.6-35B-A3B-APEX-MTP-GGUF) | I-Compact (17.3GB) | GPU 1 | 1M | CPU MoE offload, MTP draft decoding |

### Darwin-28B-REASON (Main — GPU 0)
- **Architecture:** Qwen3.5ForConditionalGeneration (hybrid linear + full attention)
- **Parameters:** 27.6B dense
- **Strengths:** Graduate-level STEM reasoning (GPQA Diamond 89.39% with DELPHI engine), 262K context for long-chain reasoning
- **Use case:** Primary reasoning engine, complex problem solving, code generation

### APEX-MTP I-Compact (Aux — GPU 1)
- **Architecture:** Qwen3.5MoeForCausalLM (36B total, 3B active per token)
- **Experts:** 256 routed + 1 shared (8 active per token), 40 trunk layers + 1 MTP layer
- **Strengths:** MoE efficiency, self-speculative decoding via MTP head (`--draft-mtp`), imatrix-optimized APEX quantization
- **Use case:** Fast inference, tool calling, multi-turn conversations, drafting
- **CPU MoE strategy:** All expert weights offloaded to CPU (`--cpu-moe`), GPU holds only attention layers + KV cache → enables 1M context on 24GB VRAM

### Infrastructure
- **Proxy:** `llama-proxy` — wake-on-ping pattern, lazy-loads models on first request, auto-kills after 30min idle
- **Systemd services:** `llama-proxy-main.service` / `llama-proxy-aux.service` — auto-restart, environment-based config
- **Ports:** Main on :8080 (backend :9080), Aux on :8081 (backend :9081)

---

## 🏗️ Project 2: Curated Models Skill (`/models-southpaw`)

### Purpose
Replace the default `/models` command with Chris's curated picks — both API models available through Nous/Hermes and local models with auto-download + hardware-optimized inference settings.

### Design

```
/models-southpaw
├── 🌐 API Models (Nous Portal)
│   ├── qwen3.7-max (Nous API — best reasoning)
│   ├── qwen3.6-flash (Nous API — fast + smart)
│   ├── claude-sonnet-4 (Nous API — coding)
│   └── [curated additions over time]
│
└── 🖥️ Local Models (self-hosted)
    ├── Darwin-28B-REASON — STEM reasoning champion
    ├── APEX-MTP 35B-A3B — fast MoE with speculative decoding
    └── [curated additions over time]
```

### Hardware Auto-Optimization
When a user selects a local model, the skill detects their GPU VRAM and auto-configures:

| VRAM | Strategy | Example |
|------|----------|---------|
| **8GB** | Q2_K quant, -ngl 20, CPU offload heavy layers, 8K ctx | Laptop GPUs |
| **16GB** | Q3_K_M quant, -ngl 40, partial CPU offload, 32K ctx | RTX 4060/4070 |
| **24GB** | Q4_K_M quant, -ngl 99, full GPU, 128K+ ctx | RTX 3090/4090 |
| **32GB** | Q5_K_M quant, full GPU, 256K ctx, flash attention | RTX 5090/A6000 |
| **48GB+** | Q6_K/Q8_0, full GPU, 512K+ ctx, all optimizations | A6000 Ada, dual GPU |

### Features
- Auto-downloads GGUF if not present locally
- Generates optimized `llama-server` command for detected hardware
- Supports both single-GPU and multi-GPU (tensor split) configurations
- Shareable as a skill — anyone using Hermes Agent can install it
- Maintains a curated `models.json` with Chris's picks, updated via HF API

---

## 🏗️ Project 3: OmniStep — Omnimodal Voice-to-Voice + Music Model

### Purpose
The base model for all downstream work. An omnimodal streaming model that handles voice, music, text, and tool calls — all-modalities-in, all-modalities-out.

### Architecture

```
OmniStep 12A3B
├── Cosmos3-Nano (16B) ──── Video/Image/Audio/Action generation
│   └── Mixture-of-Transformers (autoregressive text + diffusion continuous)
├── Nemotron 3 0.6B ─────── Streaming ASR (replaces previous ASR components)
│   └── Real-time speech-to-text with low latency
└── AceStep 4B (largest) ── Music generation & understanding
    └── Text-to-music, music-to-text, style transfer, continuation
```

### Key Design Decisions
- **Nemotron 3 0.6B streaming ASR** replaces the previous ASR components — lower latency, better quality for real-time voice interaction
- **Cosmos3-Nano** provides the world model backbone — understands video, images, audio, and physical dynamics
- **AceStep 4B** (largest variant) handles all music modalities — generation, understanding, style transfer
- **12A3B** = 12B total parameters, 3B active (MoE efficiency for edge deployment)

### Current Status
- [Released on HuggingFace](https://huggingface.co/sovthpaw/omnistep-12a3b) as public model (34 files, 4 GGUFs + 4 safetensors + example tracks)
- Example tracks: lofi, orchestra, metal (rap removed)
- 3 voice descriptions included
- Proper inference: `infer_step=50` + `oss_steps=None`

---

## 🏗️ Project 4: OmniSenter Spark 20A4B — Nous Girl Agent

### Purpose
The **Nous Girl** agent — a voice-to-voice note-taking, music, and vibe copilot that operates within Hermes Agent. This is Chris's personal assistant agent with tool-calling capabilities.

### Architecture

```
OmniSenter Spark 20A4B
├── OmniStep 12A3B ──────── Base omnimodal capabilities
├── LFM2.5 8A1B ─────────── Tool calling & agentic reasoning
│   └── 8B total, 1B active — lightweight but capable at function calling
├── Nemotron 3 ──────────── Additional training data & alignment
├── Hermes-Agent training ── Reasoning traces, tool calls from Discord
└── Darwin Family copies ──── Genome recombination for continuous improvement
```

### Capabilities
- **Voice-to-voice interaction** — real-time streaming ASR → reasoning → TTS
- **Note-taking** — persistent memory across sessions, Obsidian integration
- **Music copilot** — vibe setting, playlist management, music generation via OmniStep
- **Tool calling** — Hermes Agent function calls (terminal, file, web, calendar, etc.)
- **Agentic reasoning** — multi-step planning, delegation to other agents

### Training Data Pipeline
1. **Hermes reasoning traces** — `interstellarninja/hermes_reasoning_tool_use` (51K conversations)
2. **Lambda agent traces** — `lambda/hermes-agent-reasoning-traces` (real multi-turn trajectories)
3. **Local session data** — 318 files, 134MB across 7 agent profiles (anser, senter, chizul, nous-girl, klerik, frieza, kashik)
4. **Nemotron SFT data** — `nvidia/Nemotron-Pretraining-SFT-v1` (6.5T tokens, STEM/code/math)
5. **Nous Research Atropos** — RL-trained specialist models and SWE tasks
6. **Discord vault** — Chris's personal collection following Nous Research from the beginning

---

## 🏗️ Project 5: OmniSenter Flash 42A3B — Edge Agentic Model

### Purpose
The production-grade agentic model for edge devices. Combines everything with a larger backbone for maximum capability while maintaining MoE efficiency.

### Architecture

```
OmniSenter Flash 42A3B
├── OmniSenter Spark 20A4B ─── Base agent + omnimodal
├── Nemotron Nano Omni 30A3B ── NVIDIA's omnimodal backbone
│   └── 30B total, 3B active — proven at agentic tool calls
└── World Model training ─────── Physical reasoning, video understanding
```

### Use Cases
- Edge-deployable agentic model (runs on consumer GPUs with MoE offloading)
- All-modalities-in, all-modalities-out (voice, video, music, text, tool calls)
- Self-hosted within Hermes Agent for privacy-preserving AI
- HuggingFace release candidate

---

## 🏗️ Project 6: Evolution Radio — Self-Evolving Music Model

### Purpose
A continuously-running music generation system that uses the Darwin Family technique to evolve its own model weights. The radio literally gets better at making music the longer it runs.

### How It Works

```
┌─────────────────────────────────────────────┐
│           EVOLUTION RADIO LOOP              │
│                                             │
│  ┌─────────┐     ┌──────────────┐          │
│  │ Current  │────▶│ Darwin Merge │          │
│  │ Model    │     │ Engine       │          │
│  └─────────┘     └──────┬───────┘          │
│       ▲                  │                  │
│       │           ┌──────▼───────┐          │
│       │           │ Child Model  │          │
│       │           │ (GGUF)       │          │
│       │           └──────┬───────┘          │
│       │                  │                  │
│       │           ┌──────▼───────┐          │
│       │           │ Benchmark    │          │
│       │           │ (auto-eval)  │          │
│       │           └──────┬───────┘          │
│       │                  │                  │
│       │           ┌──────▼───────┐          │
│       └───────────│ Hot-Swap     │          │
│                   │ if better    │          │
│                   └──────────────┘          │
│                                             │
│  Runs async during normal operation         │
│  User hears music → model improves          │
│  No interruption to listening experience    │
└─────────────────────────────────────────────┘
```

### The 14-Dimensional Merge Genome

From the Darwin Family paper (arXiv:2605.14386):

```
g = (γ, α_attn, α_ffn, α_emb, ρA, ρB, r0, r1, r2, r3, r4, r5, τ, λ)
```

| Group | Parameters | Role |
|-------|-----------|------|
| **Core (6)** | γ, α_attn, α_ffn, α_emb, ρA, ρB | Global ratio, per-component ratios, parent densities |
| **Block (6)** | r0..r5 | Six independent layer-block merge ratios |
| **Hyper (2)** | τ, λ | MRI-Trust coefficient, regularization |

### MRI-Trust Fusion (Per-Tensor Mixing)

```
θM(T) = (1 - r_final(T)) · θA(T) + r_final(T) · θB(T)
r_final(T) = τ · r_MRI(T) + (1 - τ) · r_genome(T)
```

- **r_MRI(T)** — diagnostic signal (entropy + variance + cosine distance)
- **r_genome(T)** — evolutionary prior from the genome vector
- **τ** — trust parameter (converges to 0.35-0.55 empirically)

### Self-Replacement Logic
1. Background thread runs Darwin merges on the current model
2. Generates child GGUF with evolved genome
3. Benchmarks child against parent (music quality, coherence, style adherence)
4. If child scores higher → hot-swap the GGUF file
5. Next model load picks up the improved version
6. Loop continues indefinitely

---

## 🏗️ Project 7: Darwin Family Infinite Evolution Loop

### The Big Picture

```
OmniStep 12A3B (base)
    │
    ├─── Darwin Genome Copy A ───┐
    │                             ├── Merge → Child 1
    ├─── Darwin Genome Copy B ───┘
    │         │
    │         ├── Benchmark → Keep if better
    │         │
    │         ├── Darwin Genome Copy C ───┐
    │         │                             ├── Merge → Child 2
    │         ├── Darwin Genome Copy D ───┘
    │         │
    │         └── ... (infinite generations)
    │
    ├─── + LFM2.5 8A1B → OmniSenter Spark
    │         │
    │         └── Same Darwin loop on Spark
    │
    └─── + Nemotron Nano 30A3B → OmniSenter Flash
              │
              └── Same Darwin loop on Flash
```

### Scaling Strategy

When individual model merges hit quality ceilings:

1. **Merge into larger MoEs** — Combine best children into Mixture-of-Experts
2. **Fractal expert hierarchy** — Models that break down into groups → smaller experts → all the way down to 1B
3. **Expert-level fusion** — Not just weight blending, but actual expert module recombination
4. **Architecture evolution** — Let the genome parameters discover new attention patterns, routing strategies

### Continuous Training + Continuous Evolution

Two parallel loops running simultaneously:

**Loop A: Training**
- New data from Hermes Agent sessions → SFT/GRPO fine-tuning
- Nemotron datasets for STEM/code/math capability
- Nous Research Atropos artifacts for RL alignment
- Local session traces for personalization

**Loop B: Evolution**
- Darwin genome recombination of best checkpoints
- CMA-ES optimization of the 14-dimensional genome
- Cross-architecture merging via Architecture Mapper
- Automatic benchmark-based selection

The two loops feed each other: training produces better checkpoints for evolution, evolution produces better base models for training.

---

## 📊 Benchmarking & Tracking

### What We Track
- **GPQA Diamond** — Graduate-level reasoning (our Darwin-28B-REASON scores 89.39%)
- **Tool calling accuracy** — BFCL v3 scenarios (single-turn, multi-turn, multi-step, relevance)
- **Music quality** — Coherence, style adherence, generation speed
- **Voice quality** — ASR accuracy, response latency, naturalness
- **Agent performance** — Task completion rate, multi-step planning, delegation success

### Automated Loop
- **Cron job** runs every 6 hours: health checks → benchmarks → data ingestion → Discord report
- **Discord channels** for each phase: data inventory, benchmarks, merge experiments, training metrics, loop status
- **Kanban board** for tracking active experiments and blocking issues

### HuggingFace Release Pipeline
1. Model passes benchmark thresholds
2. Auto-generate model card with benchmark results
3. Package as GGUF (multiple quants) + safetensors
4. Upload to `sovthpaw/` namespace on HuggingFace
5. Post announcement to Discord

---

## 📂 Data Sources

### Tier 1 — Critical (Must Have)
| Source | Size | Content |
|--------|------|---------|
| `interstellarninja/hermes_reasoning_tool_use` | 392MB, 51K rows | Tool-calling conversations (SFT/GRPO) |
| `lambda/hermes-agent-reasoning-traces` | — | Real multi-turn agent trajectories |
| Local session data | 134MB, 318 files | 7 Hermes agent profiles |
| `sovthpaw/omnistep-12a3b` | HF model | Base omnimodal model weights |
| Darwin paper methodology | 11.7KB | Full genome spec + MRI-Trust Fusion |

### Tier 2 — High Value
| Source | Size | Content |
|--------|------|---------|
| `nvidia/Nemotron-Pretraining-SFT-v1` | 6.5T tokens | SFT data: STEM, code, math, multilingual |
| `nvidia/Nemotron-Pretraining-Code-v2` | 836M rows | GitHub code corpus |
| `nvidia/Nemotron-CC-Math-v1` | 190M rows | Mathematical reasoning |
| `nvidia/Cosmos3-Nano` | 16B params | Omnimodal world model |
| `TuringEnterprises/Open-MM-RL` | 40→3K tasks | Multimodal STEM reasoning |

### Tier 3 — Enrichment
| Source | Size | Content |
|--------|------|---------|
| `NousResearch/atropos-artifacts` | 9 items | RL-trained specialists, SWE tasks |
| `nvidia/Nemotron-CC-v2.1` | 8.79B rows | English web crawl |
| Nous Research collections | Multiple | Hermes 4, DeepHermes, YaRN, Dolma |
| Chris's personal vault | — | Curated since Nous Research founding |

---

## 🔗 Connected Repositories

| Repository | Purpose |
|------------|---------|
| [SouthpawIN/evolutionary-model-merging](https://github.com/SouthpawIN/evolutionary-model-merging) | Darwin Family merge pipeline |
| [SouthpawIN/evolutionary-radio](https://github.com/SouthpawIN/evolutionary-radio) | Self-evolving music radio |
| [SouthpawIN/Senter](https://github.com/SouthpawIN/Senter) | Senter agent framework |
| [sovthpaw/omnistep-12a3b](https://huggingface.co/sovthpaw/omnistep-12a3b) | Base omnimodal model |
| [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | Agent harness |
| [NousResearch/Atropos](https://github.com/NousResearch/Atropos) | RL environments |
| [nvidia/cosmos-framework](https://github.com/nvidia/cosmos-framework) | Cosmos3-Nano framework |
| [FINAL-Bench/Darwin-28B-REASON](https://huggingface.co/FINAL-Bench/Darwin-28B-REASON) | Darwin reasoning model |
| [mudler/Qwen3.6-35B-A3B-APEX-MTP-GGUF](https://huggingface.co/mudler/Qwen3.6-35B-A3B-APEX-MTP-GGUF) | APEX-MTP quantized model |

---

## 🎯 The Vision

Build models that **evolve themselves** — not just fine-tuned on new data, but genomically recombined through Darwin Family evolution, continuously, in the background, while the user goes about their day. The radio plays, the model learns, the genome improves, the weights get swapped, and the music gets better.

Scale this from a single 12B music model up through 20B and 42B agentic variants, each carrying forward the evolutionary lineage. Release them on HuggingFace as a family — not just models, but a **self-improving lineage** that the community can fork, evolve, and merge.

The endgame: edge-deployable, all-modalities-in/out, agentic AI that gets better every time you use it.

---

*Generated: 2026-06-05 | Darwin Family paper: arXiv:2605.14386*
