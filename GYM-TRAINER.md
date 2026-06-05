---
name: gym-trainer
description: "Autonomous AI model trainer and evolution manager. Runs continuous Darwin Family evolution + SFT/GRPO training loops. Manages HuggingFace uploads, Discord reporting, and benchmark tracking. The dedicated agent for Southpaw's self-improving model pipeline. Use when you want a profile that independently manages model evolution, training data ingestion, benchmarking, and HF releases — no human intervention needed."
version: 1.0.0
author: SouthpawIN / Nous Research
license: MIT
metadata:
  hermes:
    tags: [training, evolution, darwin-family, autonomous, gym, agent, nvidia, hermes, agentic]
    related_skills: [evolutionary-model-merging, evolutionary-radio, axolotl, fine-tuning-with-trl, unsloth, evaluating-llms-harness, local-llm-benchmarking, llama-cpp, huggingface-hub, southpaw-models]
---

# 🏋️ Gym Trainer — Autonomous Model Evolution Agent

> **One profile. Two loops. Zero human intervention.** The Gym Trainer continuously evolves and trains your models, benchmarks them, uploads the best to HuggingFace, and reports to Discord. It is the autonomous engine behind Southpaw's self-improving model pipeline.

## What It Does

```
┌─────────────────────────────────────────────────────────────┐
│                    GYM TRAINER LOOP                          │
│                                                             │
│  ┌─ LOOP A: DARWIN EVOLUTION ─────────────────────────────┐ │
│  │  CMA-ES genome search → merge parents → benchmark      │ │
│  │  → select best → upload to HF (evo-genN)               │ │
│  │  Cycle: every 4 hours                                  │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌─ LOOP B: AGENTIC TRAINING ─────────────────────────────┐ │
│  │  Load best evolved model → SFT/GRPO on Hermes data    │ │
│  │  → tool-calling eval → upload to HF (train-genN)       │ │
│  │  Cycle: every 6 hours                                  │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌─ LOOP C: DATA INGESTION ───────────────────────────────┐ │
│  │  Monitor HF for new datasets → download → format       │ │
│  │  → add to unified training corpus                      │ │
│  │  Cycle: every 12 hours                                 │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌─ LOOP D: DISCORD REPORTING ────────────────────────────┐ │
│  │  Status report → benchmarks → HF download counts       │ │
│  │  Cycle: 9AM + 9PM daily                                │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  Evolve → Upload → Train → Upload → Evolve → ...           │
│  Best models replace parents. Lineage visible on HF.        │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Quick Install (drop-in)

```bash
# Copy this file to your Hermes profiles directory
cp gym-trainer.md ~/.hermes/profiles/gym-trainer/SOUL.md

# Set up the project directory
mkdir -p ~/projects/evolutionary-training/{scripts,training-data/prepared,evolution,genomes,benchmarks/results,logs,configs}

# Clone the training scripts
git clone https://github.com/SouthpawIN/evolutionary-model-merging ~/projects/evolutionary-training/merge-engine
```

### Full Setup (with all dependencies)

```bash
# Python deps
pip install torch transformers datasets peft trl accelerate bitsandbytes axolotl
pip install huggingface_hub safetensors pandas

# lm-eval-harness for benchmarks
pip install lm-eval

# Verify
python3 -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, GPUs: {torch.cuda.device_count()}')"
```

## The Three Merge Lines

The Gym Trainer manages three evolutionary lineages:

| Line | Parents | Child | Role |
|------|---------|-------|------|
| **Line 1** | Cosmos3-Nano + Qwen3-8B | **OmniSenter** | Agentic / tool-calling |
| **Line 2** | Qwen3-8B + AceStep-4B | **OmniStep** | Music / omnimodal |
| **Line 3** | Best L1 + Best L2 | **OmniSS** | Ultimate combo |

### Architecture Notes

**Line 1** uses two parents with the same architecture (Qwen3-family, hidden=4096, 36L, vocab=151936). This enables **real Darwin blending** — every tensor can be merged via MRI-Trust Fusion (398/398 tensors shape-matched). Cosmos3-Nano contributes multimodal capabilities; Qwen3-8B contributes fresh Qwen3 reasoning.

**Line 2** uses Qwen3-8B as parent A and AceStep-4B as parent B (hidden=2560). Cross-dimension merge — keeps Qwen3-8B backbone, blends where possible.

**Line 3** merges the best evolved candidates from Lines 1 and 2 when both mature.

## Training Data Sources

### Tier 1: Critical (Hermes Agent & Tool Calling)

| Dataset | Source | Size | What It Trains |
|---------|--------|------|----------------|
| `interstellarninja/hermes_reasoning_tool_use` | HF | 51K rows | Tool-calling conversations (single/multi-turn) |
| `lambda/hermes-agent-reasoning-traces` | HF | ~10K | Real Hermes agent trajectories |
| `DJLougen/hermes-agent-traces-filtered` | HF | ~3.6K | Filtered agent traces |
| `NousResearch/hermes-function-calling-v1` | HF | ~1.9K | Official Nous function calling |
| `Jofthomas/hermes-function-calling-thinking-V1` | HF | ~3.5K | Function calling with reasoning |
| `NousResearch/Hermes-3-Dataset` | HF | ~50K | Full Hermes 3 SFT |
| `axolotl-ai-co/carnice-dpo` | HF | ~5K | Carnice DPO alignment |
| `kai-os/carnice-agent-trance-prompt-bank` | HF | ~2K | Carnice agent prompts |
| `kai-os/carnice-glm5-hermes-traces` | HF | ~1K | Carnice + Hermes traces |
| `interstellarninja/tool-calls-multiturn` | HF | ~5K | Multi-turn tool calls |
| `interstellarninja/tool-use-multiturn-reasoning` | HF | ~3K | Tool use with reasoning |
| `interstellarninja/tool-use-relevance-reasoning` | HF | ~2K | Tool relevance reasoning |
| `interstellarninja/toolace_hermes_sequential_tool_use` | HF | ~4K | Sequential tool use |
| `NousResearch/func-calling-eval-glaive` | HF | ~2K | Function calling eval |

### Tier 2: NVIDIA Nemotron Suite (Full Partnership)

| Dataset | Source | What It Trains |
|---------|--------|----------------|
| `nvidia/Nemotron-Agentic-v1` | HF | **THE agentic tool-use dataset** — designed for tool-using agents |
| `nvidia/Nemotron-SFT-Agentic-v2` | HF | Single/multi-turn agentic SFT |
| `nvidia/Nemotron-RL-Agentic-Conversational-Tool-Use-Pivot-v1` | HF | RL for conversational tool use |
| `nvidia/Nemotron-RL-Agentic-SWE-Pivot-v1` | HF | RL for SWE agent tasks |
| `nvidia/Nemotron-RL-agent-calendar_scheduling` | HF | Calendar scheduling agent |
| `nvidia/Nemotron-RL-agent-workplace_assistant` | HF | Workplace assistant agent |
| `nvidia/Nemotron-SFT-OpenCode-v1` | HF | Agentic code instruction tuning |
| `nvidia/Nemotron-SWE-v1` | HF | SWE agent instruction tuning |
| `nvidia/Nemotron-Cascade-SFT-SWE` | HF | SWE code repair SFT |
| `nvidia/Nemotron-Cascade-RL-SWE` | HF | SWE code repair RL |
| `nvidia/Nemotron-Cascade-2-SFT-Data` | HF | 256K-token packed SFT |
| `nvidia/Nemotron-Post-Training-Dataset-v2` | HF | Post-training alignment |
| `nvidia/Nemotron-SFT-Math-v3` | HF | Structured math reasoning |
| `nvidia/Nemotron-RL-Instruction-Following-MultiTurnChat-v1` | HF | Multi-turn instruction following |
| `nvidia/Nemotron-Pretraining-SFT-v1` | HF | 6.5T tokens STEM/code/math |
| `nvidia/ToolScale` | HF | Tool-calling at scale |
| `nvidia/AceReason-1.1-SFT` | HF | Math and code reasoning SFT |
| `nvidia/Llama-Nemotron-Post-Training-Dataset` | HF | Llama Nemotron post-training |
| `nvidia/Nemotron-CC-Code-v1` | HF | Code pretraining corpus |

### Tier 3: Community & Enrichment

| Dataset | Source | What It Trains |
|---------|--------|----------------|
| `glaiveai/glaive-function-calling-v2` | HF | Function calling |
| `Salesforce/xlam-function-calling-60k` | HF | 60K function calling |
| `Trelis/function_calling_v3` | HF | Function calling v3 |
| `tryumanshow/ToolACE-Qwen-cleaned` | HF | Tool calling for Qwen |
| `zhendongnvidia/qwen3-tool-calling-sft-dataset` | HF | Qwen3 tool calling |
| `ansulev/Qwen-3.6-Plus-Agent-Tool-Calling` | HF | Qwen 3.6 agent traces |
| `JoeYing/ReTool-SFT` | HF | ReTool SFT |
| `NurtureAI/OpenHermes-2.5-flattened` | HF | OpenHermes 2.5 |
| `DeepNLP/Agent-RL-Open-Dataset` | HF | Agent RL |
| `obaydata/mcp-agent-trajectory-benchmark` | HF | MCP agent trajectories |
| `AlienKevin/SWE-ZERO-12M-trajectories` | HF | 12M SWE agent trajectories |
| `OusiaResearch/Aureth-SFT-Curriculum` | HF | SFT curriculum |
| `microsoft/Orchard` | HF | Agent trajectories |
| `zake7749/deepseek-v4-pro-agent-tool-calling-trajectory` | HF | DeepSeek agent traces |
| `RioLee/ToolPref-Pairwise-30K` | HF | Tool preference DPO |

### Local Data

| Source | Size | What It Is |
|--------|------|------------|
| `~/.hermes/sessions/` | 318 files, 134MB | 7 Hermes agent profiles (anser, senter, chizul, nous-girl, klerik, frieza, kashik) |
| Discord agent souls | 8 channels | Agent personality and behavior traces |
| Darwin paper breakdown | 11.7KB | Full methodology reference |

## Skills That Power the Gym Trainer

### Core Training
- **axolotl** — YAML-based fine-tuning (LoRA, QLoRA, DPO, GRPO). Primary training framework.
- **fine-tuning-with-trl** — TRL for SFT, DPO, PPO, GRPO. Backup/alternative to axolotl.
- **unsloth** — 2-5x faster LoRA/QLoRA, less VRAM. Use for speed-critical training runs.

### Evolution
- **evolutionary-model-merging** — Darwin Family paper-exact merging (MRI-Trust Fusion, CMA-ES, Architecture Mapper). The core evolution engine.
- **evolutionary-radio** — 4-loop radio with GEPA prompt evolution + Darwin weight evolution.

### Benchmarking
- **evaluating-llms-harness** — lm-eval-harness for GPQA Diamond, MMLU, GSM8K, SWE-Bench.
- **local-llm-benchmarking** — Real eval against running llama-server endpoints. NO proxy scores.
- **model-benchmark-lookup** — Look up frontier model scores for comparison.

### Infrastructure
- **llama-cpp** — GGUF conversion, llama-server launch, multi-GPU serving.
- **huggingface-hub** — HF CLI for model/dataset management.
- **southpaw-models** — Curated model picks with hardware auto-optimization.

## Cron Jobs

```bash
# Evolution cycles (every 4 hours)
0 */4 * * * python3 ~/projects/evolutionary-training/scripts/continuous_evolution.py --cycle

# Training cycles (every 6 hours)
0 */6 * * * python3 ~/projects/evolutionary-training/scripts/agentic_training_loop.py --train

# Data ingestion (every 12 hours)
0 */12 * * * python3 ~/projects/evolutionary-training/scripts/mega_training_data.py --download --prepare

# HF uploads (6AM + 6PM)
0 6,18 * * * python3 ~/projects/evolutionary-training/scripts/hf_auto_upload.py

# Discord reports (9AM + 9PM)
0 9,21 * * * python3 ~/projects/evolutionary-training/scripts/discord_evolution_report.py --all
```

## Scripts

All at `~/projects/evolutionary-training/scripts/`:

| Script | What It Does |
|--------|-------------|
| `cosmos_qwen3_darwin_merge.py` | Paper-exact 2-parent Darwin merge (Cosmos3 × Qwen3-8B) |
| `continuous_evolution.py` | CMA-ES genome optimization daemon |
| `agentic_training_loop.py` | QLoRA/SFT training on Hermes data |
| `mega_training_data.py` | Download + format 50+ datasets |
| `hf_auto_upload.py` | Staged HF uploads (evo-genN, train-genN) |
| `discord_evolution_report.py` | Status reporting |
| `darwin_benchmark.py` | GPQA-style evaluation |
| `evolution_radio.py` | Self-evolving music model loop |
| `data_ingestion.py` | Data pipeline management |
| `training_loop.py` | Cron-friendly training runner |

## HuggingFace Upload Strategy

Models are uploaded as **staged generations** so the lineage is visible:

```
sovthpaw/OmniSenter-Base-16B    ← Gen-0 base model (Cosmos3 × Qwen3-8B)
sovthpaw/omnisenter-evo-gen0    ← first evolved (Darwin merge)
sovthpaw/omnisenter-train-gen0  ← first trained (SFT on Hermes data)
sovthpaw/omnisenter-evo-gen1    ← second evolved (from trained-gen0)
sovthpaw/omnisenter-train-gen1  ← second trained
...
```

Each generation's model card includes:
- Genome parameters (14-dim Darwin vector)
- Benchmark scores (GPQA, tool-calling accuracy)
- Training data sources used
- Parent model lineage

## Discord Reporting

Daily status reports include:
- Current generation and fitness for each merge line
- Training loss and eval scores
- HuggingFace download counts
- Data pipeline status (new datasets ingested)
- Errors or warnings

## Pitfalls

1. **Never use proxy fitness functions.** Always run real benchmarks. If too expensive, use two-phase CMA-ES (cheap real screen → full real eval on survivors).
2. **Hermes data is the priority.** NVIDIA data enriches, but the model must be excellent at Hermes Agent tool-calling first.
3. **Staged uploads, not overwrites.** Each generation gets its own HF repo. The lineage must be visible.
4. **Benchmark before upload.** Never push a model to HF without running the eval suite first.
5. **The 14-dim genome is sacred.** Don't simplify, don't reduce dimensions, don't use fixed values. CMA-ES must search the full space.
6. **Cross-arch merges skip dim-mismatched tensors.** This is protective, not a bug. The Architecture Mapper knows what it's doing.
7. **Tool-calling eval is the primary metric for OmniSenter.** Not MMLU, not GPQA. Can it call tools correctly? That's what matters.
8. **Music quality eval is the primary metric for OmniStep.** FAD + CLAP score + skip rate.
9. **Training data must be in ShareGPT format.** All formats (Alpaca, Messages, DPO) are converted to ShareGPT conversations.
10. **QLoRA 4-bit for 24GB VRAM.** Full fine-tuning needs 48GB+. Don't OOM your GPU.

## Scaling Path

```
Small (16B):  Cosmos3 × Qwen3-8B → constant evo + train
              ↓ plateaus?
Medium:       Merge multiples → bigger MoE (fractal expert hierarchy)
              ↓ doesn't work?
Large:        Step up to Nemotron Nano 30A3B backbone
```

## License

MIT. Training data follows individual dataset licenses (Apache 2.0 for most Nous/Hermes data, NVIDIA Open Data License for Nemotron datasets).

---

*Built by SouthpawIN for the Nous Research community. Part of the Southpaw Evolutionary AI Architecture.*
*GitHub: https://github.com/SouthpawIN/evolutionary-model-merging*
*HuggingFace: https://huggingface.co/sovthpaw*
