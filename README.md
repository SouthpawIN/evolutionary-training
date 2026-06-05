![Evolutionary Training Pipeline](https://v3b.fal.media/files/b/0a9d1d35/dVvLndR7FLLn8tp8XBV1K_Ic0qXeG1.png)

# 🧬 Southpaw's Evolutionary Training Pipeline

> **Self-improving AI models through Darwin Family evolution + continuous agentic training.**
> Three merge lines. 88 datasets. Zero human intervention.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![HuggingFace](https://img.shields.io/badge/🤗_HuggingFace-sovthpaw-blue)](https://huggingface.co/sovthpaw)
[![GitHub](https://img.shields.io/badge/GitHub-SouthpawIN-black?logo=github)](https://github.com/SouthpawIN)

---

## Overview

This repository contains the complete infrastructure for **autonomously evolving and training AI models** using the [Darwin Family technique](https://arxiv.org/abs/2605.14386) (Kim et al., 2026) combined with continuous SFT/GRPO training on Hermes agent and NVIDIA Nemotron data.

The system runs **two independent but interconnected loops**:

1. **Evolution Loop** — CMA-ES genome optimization → Darwin merges → benchmarks → best model replaces parents
2. **Training Loop** — SFT/GRPO on 88 datasets of agentic/tool-calling data → benchmarks → best model replaces parents

Both loops feed each other: evolution produces better base models for training, training produces better checkpoints for evolution. The best models are automatically uploaded to HuggingFace as staged generations.

---

## The Three Merge Lines

| Line | Parent A | Parent B | Child | Role | Status |
|------|----------|----------|-------|------|--------|
| **Line 1** | [Cosmos3-Nano](https://huggingface.co/nvidia/Cosmos3-Nano) (15.75B) | [LFM2.5-8B-A1B](https://huggingface.co/LiquidAI/LFM2.5-8B-A1B) (8.47B) | **OmniSenter** | Agentic / tool-calling | 🟡 Downloading |
| **Line 2** | [Cosmos3-Nano](https://huggingface.co/nvidia/Cosmos3-Nano) (15.75B) | [AceStep-5Hz-LM-4B](https://huggingface.co/ACE-Step/acestep-5Hz-lm-4B) (4B) | **OmniStep** | Music / omnimodal | 🟡 Downloading |
| **Line 3** | Best OmniSenter | Best OmniStep | **OmniSS** | Ultimate combo | ⏳ Pending |

Each line evolves independently via CMA-ES. Line 3 merges the best of Lines 1 and 2 when they mature.

### Why These Parents?

- **Cosmos3-Nano** ([nvidia/Cosmos3-Nano](https://huggingface.co/nvidia/Cosmos3-Nano)) — NVIDIA's omnimodal world model. Understands text, image, video, audio, and action commands. Mixture-of-Transformers architecture trained on 1.3B data points across 393 datasets. This provides the foundational multimodal intelligence.

- **LFM2.5-8B-A1B** ([LiquidAI/LFM2.5-8B-A1B](https://huggingface.co/LiquidAI/LFM2.5-8B-A1B)) — Liquid AI's MoE model with 8.47B total / 1B active parameters. Exceptional at tool calling, function execution, and agentic reasoning. 9 languages, 82K+ downloads. This provides the agentic backbone.

- **AceStep-5Hz-LM-4B** ([ACE-Step/acestep-5Hz-lm-4B](https://huggingface.co/ACE-Step/acestep-5Hz-lm-4B)) — ACE-Step's Qwen3-4B language model for music understanding. Chain-of-thought metadata synthesis, query rewriting, audio understanding. This provides the music intelligence.

---

## The Darwin Family Technique

From [arXiv:2605.14386](https://arxiv.org/abs/2605.14386) (Kim et al., May 2026):

> Can you recombine two pretrained LLMs — **without any training** — into a single model that's *better than either parent*?

**Answer: Yes.** Their headline result is **Darwin-27B-Opus at 86.9% on GPQA Diamond** (graduate-level reasoning), ranking #6 out of 1,252 models. No gradient updates. No RLHF. Just weight-space recombination.

### The 14-Dimensional Merge Genome

```
g = (γ, α_attn, α_ffn, α_emb, ρA, ρB, r0, r1, r2, r3, r4, r5, τ, λ)
```

| Group | Parameters | Role |
|-------|-----------|------|
| **Core (6)** | γ, α_attn, α_ffn, α_emb, ρA, ρB | Global ratio, per-component ratios, parent densities |
| **Block (6)** | r0..r5 | Six independent layer-block merge ratios |
| **Hyper (2)** | τ, λ | MRI-Trust coefficient, regularization |

### MRI-Trust Fusion

For every weight tensor T in the model:

```
θM(T) = (1 - r_final(T)) · θA(T) + r_final(T) · θB(T)
r_final(T) = τ · r_MRI(T) + (1 - τ) · r_genome(T)
```

- **r_MRI(T)** — diagnostic signal (entropy + variance + cosine distance)
- **r_genome(T)** — evolutionary prior from the genome vector
- **τ** — trust parameter (converges to 0.35-0.55 empirically)

### CMA-ES Evolution

1. Sample N candidate genomes from a multivariate Gaussian
2. Build N children — one full merge per candidate genome
3. Score each child on a real benchmark → fitness
4. Update the Gaussian — shift toward higher-fitness candidates
5. Repeat for 20-50 generations

### Architecture Mapper (Cross-Architecture)

For parents with different architectures, the Mapper finds layer correspondences:

```
Comp(i, j) = 0.5 · Type(i,j) + 0.3 · Dim(i,j) + 0.2 · Param(i,j)
```

Tensors below a compatibility threshold are **skipped** — parent A's value is kept. No random projection.

**Key finding**: The Architecture Mapper's "skip on dim mismatch" behavior is **protective**, not a fallback. Cross-arch merges that skip mismatched tensors outperform same-arch merges that force per-tensor blending.

---

## Training Data — 88 Datasets, 50K+ Conversations

### Tier 1: Critical — Hermes Agent & Tool Calling

| Dataset | Source | Size | Citation |
|---------|--------|------|----------|
| `hermes_reasoning_tool_use` | [interstellarninja](https://huggingface.co/datasets/interstellarninja/hermes_reasoning_tool_use) | 51K rows, 392MB | ShareGPT tool-calling conversations (single/multi-turn, relevance). GRPO rollouts with DeepHermes-3-Llama-3-8B-Preview. Apache-2.0. |
| `hermes-agent-reasoning-traces` | [lambda](https://huggingface.co/datasets/lambda/hermes-agent-reasoning-traces) | ~10K rows | Real multi-turn Hermes agent trajectories. |
| `hermes-agent-traces-filtered` | [DJLougen](https://huggingface.co/datasets/DJLougen/hermes-agent-traces-filtered) | ~3.6K rows | Filtered and cleaned agent traces. |
| `hermes-function-calling-v1` | [NousResearch](https://huggingface.co/datasets/NousResearch/hermes-function-calling-v1) | ~1.9K rows | Official Nous Research function calling dataset. |
| `hermes-function-calling-thinking-V1` | [Jofthomas](https://huggingface.co/datasets/Jofthomas/hermes-function-calling-thinking-V1) | ~3.5K rows | Function calling with thinking/reasoning traces. |
| `Hermes-3-Dataset` | [NousResearch](https://huggingface.co/datasets/NousResearch/Hermes-3-Dataset) | ~50K rows | Official Hermes 3 SFT dataset. |
| `carnice-dpo` | [axolotl-ai-co](https://huggingface.co/datasets/axolotl-ai-co/carnice-dpo) | ~5K rows | Carnice DPO alignment data. |
| `carnice-agent-trance-prompt-bank` | [kai-os](https://huggingface.co/datasets/kai-os/carnice-agent-trance-prompt-bank) | ~2K rows | Carnice agent trance prompt bank. |
| `carnice-glm5-hermes-traces` | [kai-os](https://huggingface.co/datasets/kai-os/carnice-glm5-hermes-traces) | ~1K rows | Carnice GLM5 Hermes traces. |
| `tool-calls-multiturn` | [interstellarninja](https://huggingface.co/datasets/interstellarninja/tool-calls-multiturn) | ~5K rows | Multi-turn tool calls. |
| `tool-use-multiturn-reasoning` | [interstellarninja](https://huggingface.co/datasets/interstellarninja/tool-use-multiturn-reasoning) | ~3K rows | Tool use with reasoning traces. |
| `tool-use-relevance-reasoning` | [interstellarninja](https://huggingface.co/datasets/interstellarninja/tool-use-relevance-reasoning) | ~2K rows | Tool relevance reasoning. |
| `toolace_hermes_sequential_tool_use` | [interstellarninja](https://huggingface.co/datasets/interstellarninja/toolace_hermes_sequential_tool_use) | ~4K rows | Sequential tool use patterns. |
| `func-calling-eval-glaive` | [NousResearch](https://huggingface.co/datasets/NousResearch/func-calling-eval-glaive) | ~2K rows | Function calling evaluation. |

### Tier 2: NVIDIA Nemotron Suite (Partnership Data)

| Dataset | Source | Citation |
|---------|--------|----------|
| **Nemotron-Agentic-v1** | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-Agentic-v1) | **THE agentic tool-use dataset.** Designed to strengthen models as interactive, tool-using agents. |
| Nemotron-SFT-Agentic-v2 | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-SFT-Agentic-v2) | Synthetic single-turn and multi-turn agentic SFT data. |
| Nemotron-RL-Agentic-Conversational-Tool-Use-Pivot-v1 | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-RL-Agentic-Conversational-Tool-Use-Pivot-v1) | RL for conversational tool use. |
| Nemotron-RL-Agentic-SWE-Pivot-v1 | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-RL-Agentic-SWE-Pivot-v1) | RL for SWE agent tasks. |
| Nemotron-RL-agent-calendar_scheduling | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-RL-agent-calendar_scheduling) | Calendar scheduling agent RL. |
| Nemotron-RL-agent-workplace_assistant | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-RL-agent-workplace_assistant) | Multi-step workplace assistant agent. |
| Nemotron-SFT-OpenCode-v1 | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-SFT-OpenCode-v1) | Agentic instruction tuning for code. |
| Nemotron-SWE-v1 | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-SWE-v1) | SWE agent instruction tuning. |
| Nemotron-Cascade-SFT-SWE | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-Cascade-SFT-SWE) | SWE code repair SFT data. |
| Nemotron-Cascade-RL-SWE | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-Cascade-RL-SWE) | SWE code repair RL. 37.2% pass@1 resolve rate. |
| Nemotron-SFT-Math-v3 | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-SFT-Math-v3) | Structured mathematical reasoning. |
| Nemotron-RL-Instruction-Following-MultiTurnChat-v1 | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-RL-Instruction-Following-MultiTurnChat-v1) | Multi-turn instruction following RL. |
| Nemotron-Post-Training-Dataset-v2 | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-Post-Training-Dataset-v2) | Post-training alignment extension. |
| Nemotron-Cascade-2-SFT-Data | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-Cascade-2-SFT-Data) | 256K-token packed SFT sequences. |
| ToolScale | [nvidia](https://huggingface.co/datasets/nvidia/ToolScale) | Tool-calling at scale. |
| Nemotron-Pretraining-SFT-v1 | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-Pretraining-SFT-v1) | 6.5T tokens: STEM, code, math, multilingual. Generated by DeepSeek-R1, Qwen3-30B-A3B, Qwen2.5-72B, Mixtral-8x22B, Nemotron 4 340B. NVIDIA Open Data License. |
| AceReason-1.1-SFT | [nvidia](https://huggingface.co/datasets/nvidia/AceReason-1.1-SFT) | Math and code reasoning SFT. |
| Llama-Nemotron-Post-Training-Dataset | [nvidia](https://huggingface.co/datasets/nvidia/Llama-Nemotron-Post-Training-Dataset) | Llama Nemotron post-training. |
| Nemotron-CC-Code-v1 | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-CC-Code-v1) | 16.9B tokens code pretraining corpus. |
| Nemotron-Math-v2 | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-Math-v2) | Math reasoning dataset. |
| Nemotron-MIND | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-MIND) | Math reasoning pretraining. |
| Nemotron-SFT-Competitive-Programming-v2 | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-SFT-Competitive-Programming-v2) | Competitive programming SFT. |
| Nemotron-Competitive-Programming-v1 | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-Competitive-Programming-v1) | Competitive programming. |
| Nemotron-RL-Safety-v1 | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-RL-Safety-v1) | RL safety alignment. |
| Nemotron-RL-knowledge-openqa | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-RL-knowledge-openqa) | RL for knowledge QA. |
| Nemotron-Research-GooseReason-0.7M | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-Research-GooseReason-0.7M) | Research reasoning 700K examples. |
| Nemotron-SFT-Multilingual-v1 | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-SFT-Multilingual-v1) | Multilingual SFT. |
| Nemotron-ClimbLab | [nvidia](https://huggingface.co/datasets/nvidia/Nemotron-ClimbLab) | Training data. |

### Tier 3: Community Tool Calling & Agent Data

| Dataset | Source | Citation |
|---------|--------|----------|
| `glaive-function-calling-v2` | [glaiveai](https://huggingface.co/datasets/glaiveai/glaive-function-calling-v2) | Glaive function calling v2. |
| `xlam-function-calling-60k` | [Salesforce](https://huggingface.co/datasets/Salesforce/xlam-function-calling-60k) | 60K function calling examples from Salesforce. |
| `function_calling_v3` | [Trelis](https://huggingface.co/datasets/Trelis/function_calling_v3) | Trelis function calling v3. |
| `ToolACE-Qwen-cleaned` | [tryumanshow](https://huggingface.co/datasets/tryumanshow/ToolACE-Qwen-cleaned) | ToolACE cleaned for Qwen training. |
| `qwen3-tool-calling-sft-dataset` | [zhendongnvidia](https://huggingface.co/datasets/zhendongnvidia/qwen3-tool-calling-sft-dataset) | Qwen3 tool calling SFT. |
| `Qwen-3.6-Plus-Agent-Tool-Calling` | [ansulev](https://huggingface.co/datasets/ansulev/Qwen-3.6-Plus-Agent-Tool-Calling) | Qwen 3.6 Plus agent trajectories. |
| `ReTool-SFT` | [JoeYing](https://huggingface.co/datasets/JoeYing/ReTool-SFT) | ReTool SFT dataset. |
| `OpenHermes-2.5-flattened` | [NurtureAI](https://huggingface.co/datasets/NurtureAI/OpenHermes-2.5-flattened) | OpenHermes 2.5 flattened for training. |
| `Agent-RL-Open-Dataset` | [DeepNLP](https://huggingface.co/datasets/DeepNLP/Agent-RL-Open-Dataset) | Agent RL open dataset. |
| `mcp-agent-trajectory-benchmark` | [obaydata](https://huggingface.co/datasets/obaydata/mcp-agent-trajectory-benchmark) | MCP agent trajectory benchmark. |
| `SWE-ZERO-12M-trajectories` | [AlienKevin](https://huggingface.co/datasets/AlienKevin/SWE-ZERO-12M-trajectories) | 12M SWE agent trajectories. Goal: instill agentic tool-use priors. |
| `Orchard` | [microsoft](https://huggingface.co/datasets/microsoft/Orchard) | Agent trajectories from Microsoft. |
| `Aureth-SFT-Curriculum` | [OusiaResearch](https://huggingface.co/datasets/OusiaResearch/Aureth-SFT-Curriculum) | SFT curriculum learning data. |
| `deepseek-v4-pro-agent-tool-calling-trajectory` | [zake7749](https://huggingface.co/datasets/zake7749/deepseek-v4-pro-agent-tool-calling-trajectory) | DeepSeek agent traces. |
| `ToolPref-Pairwise-30K` | [RioLee](https://huggingface.co/datasets/RioLee/ToolPref-Pairwise-30K) | Tool preference DPO data. 30K pairs. |

### Local Data

| Source | Size | Description |
|--------|------|-------------|
| `~/.hermes/sessions/` | 318 files, 134MB | 7 Hermes agent profiles: anser (100 files, 38MB), nous-girl (20 files, 6MB), senter (18 files, 1.6MB), klerik (6 files, 284KB), chizul (5 files, 300KB), frieza (4 files, 232KB), kashik |
| Discord agent souls | 8 channels | Agent personality and behavior traces from the Senter Dev Discord server |
| Darwin paper breakdown | 11.7KB | Full paper breakdown of arXiv:2605.14386 with methodology reference |

---

## Scripts

| Script | Purpose | Key Features |
|--------|---------|-------------|
| `lfm_cosmos_darwin_merge.py` | Paper-exact 2-parent Darwin merge | MRI-Trust Fusion, Architecture Mapper, cross-arch handling |
| `continuous_evolution.py` | CMA-ES genome optimization daemon | 14-dim genome, adaptive sigma, hot-swap, HF upload |
| `agentic_training_loop.py` | QLoRA/SFT training on Hermes data | 4-bit QLoRA, tool-calling eval, checkpointing |
| `mega_training_data.py` | Download + format 50+ datasets | Multi-format converter (ShareGPT, Alpaca, Messages, DPO) |
| `hf_auto_upload.py` | Staged HF uploads | Per-generation repos (evo-genN, train-genN), auto model cards |
| `discord_evolution_report.py` | Status reporting | Generation, fitness, sigma, HF downloads |
| `darwin_benchmark.py` | GPQA-style evaluation | Physics, chemistry, math, biology, CS domains |
| `evolution_radio.py` | Self-evolving music model loop | Background Darwin merges, hot-swap GGUF |
| `data_ingestion.py` | Data pipeline management | HF datasets, local sessions, Discord data |
| `training_loop.py` | Cron-friendly training runner | Benchmark → ingest → report → Discord |
| `download_all_data.sh` | Bulk dataset downloader | All tiers, parquet→JSONL conversion |

---

## Gym Trainer — The Autonomous Agent

The [Gym Trainer](GYM-TRAINER.md) is a standalone Hermes Agent profile that manages the entire pipeline autonomously:

- **4 concurrent loops**: evolution, training, data ingestion, Discord reporting
- **Cron-scheduled**: every 4h (evolution), 6h (training), 12h (data), 12h (reports)
- **No human intervention**: benchmarks, selects, uploads, reports
- **Staged HF uploads**: lineage visible as `sovthpaw/omnisenter-evo-gen0`, `gen1`, etc.

Drop `GYM-TRAINER.md` into `~/.hermes/profiles/gym-trainer/SOUL.md` to activate.

---

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| GPU | 1× RTX 3090 (24GB) | 2× RTX 3090 (48GB total) |
| RAM | 32GB | 64GB |
| Storage | 500GB SSD | 2TB NVMe |
| Training method | QLoRA 4-bit | QLoRA 4-bit + gradient checkpointing |

### RTX 3090 Training Config

```yaml
# QLoRA config for 24GB VRAM
method: qlora
bits: 4
lora_r: 64
lora_alpha: 128
batch_size: 2
gradient_accumulation: 8
learning_rate: 2e-4
max_seq_len: 4096
epochs: 3
optimizer: paged_adamw_8bit
```

---

## Scaling Strategy

```
Small (8B):  LFM2.5 × Cosmos → constant evo + train
             ↓ plateaus?
Medium:      Merge multiples → bigger MoE (fractal expert hierarchy)
             ↓ doesn't work?
Large:       Step up to Nemotron Nano 30A3B backbone
```

The fractal expert hierarchy: models that break down into groups → smaller experts → all the way down to 1B. Not just weight blending, but actual expert module recombination.

---

## HuggingFace Releases

Models are uploaded as **staged generations** so the evolutionary lineage is visible:

```
sovthpaw/omnisenter-evo-gen0    ← first evolved (Darwin merge)
sovthpaw/omnisenter-train-gen0  ← first trained (SFT on Hermes data)
sovthpaw/omnisenter-evo-gen1    ← second evolved (from trained-gen0)
sovthpaw/omnisenter-train-gen1  ← second trained
...
```

Each model card includes:
- Genome parameters (14-dim Darwin vector)
- Benchmark scores (GPQA, tool-calling accuracy, BFCL v3)
- Training data sources used
- Parent model lineage

### Current Releases

| Repo | Status | Downloads |
|------|--------|-----------|
| [sovthpaw/omnistep-12a3b](https://huggingface.co/sovthpaw/omnistep-12a3b) | ✅ Released | 594 |
| [sovthpaw/Omni-Senter-3B](https://huggingface.co/sovthpaw/Omni-Senter-3B) | ✅ Released | 44 |
| sovthpaw/omnisenter-evo-gen0 | ⏳ Pending | — |
| sovthpaw/omnistep-evo-gen0 | ⏳ Pending | — |

---

## Project Structure

```
evolutionary-training/
├── README.md                          # This file
├── GYM-TRAINER.md                     # Autonomous agent profile
├── ARCHITECTURE.md                    # Architecture spec
├── SOUTHPAW-ARCHITECTURE.md           # Full 7-project ecosystem
├── discord-announcement.md            # Discord share text
├── configs/
│   └── merge_lines.py                 # 3 merge line definitions
├── scripts/
│   ├── lfm_cosmos_darwin_merge.py     # Darwin merge engine
│   ├── continuous_evolution.py        # CMA-ES daemon
│   ├── agentic_training_loop.py       # SFT/GRPO training
│   ├── mega_training_data.py          # Data pipeline (50+ datasets)
│   ├── hf_auto_upload.py              # Staged HF uploads
│   ├── discord_evolution_report.py    # Status reporting
│   ├── darwin_benchmark.py            # GPQA-style eval
│   ├── evolution_radio.py             # Self-evolving music loop
│   ├── data_ingestion.py              # Data management
│   ├── training_loop.py               # Cron training runner
│   └── download_all_data.sh           # Bulk downloader
├── training-data/
│   ├── raw/                           # Downloaded datasets
│   └── prepared/
│       ├── unified_sft.jsonl          # 419MB, 24K+ conversations
│       └── manifest.json              # Dataset manifest
├── evolution/
│   ├── lfm-cosmos/                    # Line 1 evolution state
│   └── omnistep/                      # Line 2 evolution state
├── genomes/                           # CMA-ES genome storage
├── benchmarks/
│   └── results/                       # Benchmark results
├── logs/                              # Pipeline logs
└── data-sources/
    └── discord/                       # Agent souls + Darwin docs
```

---

## References

### Papers
- Kim, T. et al. (2026). *Darwin Family: MRI-Trust-Weighted Evolutionary Merging for Training-Free Scaling of Language-Model Reasoning.* [arXiv:2605.14386](https://arxiv.org/abs/2605.14386).
- Agrawal, P. et al. (2025). *Reflective Prompt Evolution Can Outperform Reinforcement Learning.* [arXiv:2507.19457](https://arxiv.org/abs/2507.19457).

### Models
- NVIDIA Cosmos3-Nano: [nvidia/Cosmos3-Nano](https://huggingface.co/nvidia/Cosmos3-Nano) — 15.75B omnimodal world model. OpenMDW 1.1 License.
- Liquid AI LFM2.5-8B-A1B: [LiquidAI/LFM2.5-8B-A1B](https://huggingface.co/LiquidAI/LFM2.5-8B-A1B) — 8.47B MoE (1B active). LFM1.0 License.
- ACE-Step 5Hz LM 4B: [ACE-Step/acestep-5Hz-lm-4B](https://huggingface.co/ACE-Step/acestep-5Hz-lm-4B) — Qwen3-4B music LM. MIT License.
- Darwin-28B-REASON: [FINAL-Bench/Darwin-28B-REASON](https://huggingface.co/FINAL-Bench/Darwin-28B-REASON) — 27.6B dense, GPQA Diamond 89.39%.

### Tools & Frameworks
- [Axolotl](https://github.com/axolotl-ai-cloud/axolotl) — YAML-based LLM fine-tuning
- [TRL](https://github.com/huggingface/trl) — Transformers Reinforcement Learning
- [Unsloth](https://github.com/unslothai/unsloth) — 2-5x faster LoRA/QLoRA
- [lm-eval-harness](https://github.com/EleutherAI/lm-evaluation-harness) — LLM benchmarking
- [llama.cpp](https://github.com/ggml-org/llama.cpp) — Local GGUF inference
- [Hermes Agent](https://github.com/NousResearch/hermes-agent) — Self-improving AI agent framework
- [TurboHaul Manager](https://github.com/MrTrenchTrucker/turbohaul-manager) — Ollama-shape inference manager

### Related Repositories
- [SouthpawIN/evolutionary-model-merging](https://github.com/SouthpawIN/evolutionary-model-merging) — Darwin Family merge pipeline
- [SouthpawIN/evolutionary-radio](https://github.com/SouthpawIN/evolutionary-radio) — Self-evolving music radio
- [NousResearch/Atropos](https://github.com/NousResearch/Atropos) — RL environments framework

---

## License

MIT. Training data follows individual dataset licenses:
- Nous Research / Hermes data: Apache-2.0
- NVIDIA Nemotron data: [NVIDIA Open Data License](https://developer.nvidia.com/nvidia-open-data-license)
- Community datasets: see individual dataset pages

---

## Acknowledgments

- **Nous Research** — Hermes Agent framework, Hermes training data, community support
- **NVIDIA** — Nemotron training suite, Cosmos3-Nano, partnership data access
- **Liquid AI** — LFM2.5 MoE model
- **ACE-Step** — Music generation foundation model
- **MrTrenchTrucker** — TurboHaul Manager inference server
- **Kim et al.** — Darwin Family paper (arXiv:2605.14386)

---

*Built by [SouthpawIN](https://github.com/SouthpawIN) for the [Nous Research](https://nousresearch.com) community.*
*Part of the Southpaw Evolutionary AI Architecture.*
