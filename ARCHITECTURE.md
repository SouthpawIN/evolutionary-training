# OmniSenter Architecture — Full Stack

## Model Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│                    OMNISTEP 12A3B                        │
│  Base: Cosmos3-Nano + Nemotron 3.5 ASR 0.6B + AceStep   │
│  All modalities in/out: voice, music, video, text        │
│  Streaming ASR → real-time voice-to-voice                │
├─────────────────────────────────────────────────────────┤
│  + Qwen3-8B (tool calling + agentic capabilities)    │
│                    ↓                                      │
│              OMNISENTER SPARK 20A4B                       │
│  Voice-to-voice note-taking agent in Hermes              │
│  Function calling, memory, context management            │
│  THIS IS NOUS GIRL                                       │
├─────────────────────────────────────────────────────────┤
│  Darwin Family Genome Copies × ∞                         │
│  Continuous genealogical evolution                       │
│  Self-replacing GGUF hot-swap                            │
│                    ↓                                      │
│              EVOLUTION RADIO                              │
│  Background Darwin merges while you use the model        │
│  Model literally gets better over time                   │
├─────────────────────────────────────────────────────────┤
│  + Nemotron Nano 30A3B                                   │
│                    ↓                                      │
│             OMNISENTER FLASH 42A3B                        │
│  Edge-deployable agentic model                           │
│  All modalities + world model capabilities               │
└─────────────────────────────────────────────────────────┘
```

## Component Models

### Cosmos3-Nano (16B)
- **Type:** Mixture-of-Transformers (MoT)
- **Modalities:** Text, image, video, audio, action commands
- **Architecture:** Autoregressive transformer (text) + Diffusion transformer (continuous)
- **Training:** 1.3B data points across 393 datasets
- **Repo:** nvidia/Cosmos3-Nano

### Nemotron 3.5 ASR Streaming 0.6B
- **Type:** Streaming ASR (speech-to-text)
- **Languages:** Multilingual
- **Repo:** nvidia/nemotron-3.5-asr-streaming-0.6b
- **Role in OmniStep:** Replaces streaming ASR component for real-time voice

### AceStep 4B
- **Type:** Music generation model
- **Role in OmniStep:** Music/audio generation backbone

### Qwen3-8B
- **Type:** Small language model with tool calling
- **Role in OmniSenter Spark:** Agentic capabilities, function calling
- **Active params:** 1B per token (8A = 8 total, 1B active)

### Nemotron Nano 30A3B
- **Type:** MoE model
- **Role in OmniSenter Flash:** Larger backbone for edge deployment

## Darwin Family Evolution Loop

### Phase 1: Genome Copies
1. Take OmniSenter Spark as parent model
2. Generate N genome vectors (14-dimensional merge parameter space)
3. Each genome = different child model characteristics

### Phase 2: Evaluation
1. Run each child through benchmark suite:
   - GPQA Diamond (graduate reasoning)
   - Tool calling accuracy (BFCL v3)
   - Voice-to-voice latency
   - Music generation quality
   - Agentic task completion
2. Score each child on composite metric

### Phase 3: Selection + Mutation
1. Select top-K children by composite score
2. Apply CMA-ES optimization to genome space
3. Generate next generation of children
4. Repeat Phase 2

### Phase 4: Self-Replacement
1. Best child GGUF replaces parent in llama-proxy
2. Hot-swap via proxy restart (zero downtime)
3. Log replacement in Discord #🔄-loop-status
4. Continue evolution from new baseline

### Background Operation
- Darwin merges run on GPU 1 (APEX-MTP) when idle
- 30-min idle timeout → merge job starts
- New model ready → swap on next request
- User never notices the transition

## Data Sources (for continuous training)

### Tier 1: Agent Traces
- `interstellarninja/hermes_reasoning_tool_use` (51K conversations)
- `lambda/hermes-agent-reasoning-traces` (real trajectories)
- Local session data (318 files, 134MB across 8 profiles)

### Tier 2: NVIDIA Datasets
- Nemotron-Pretraining-SFT-v1 (6.5T tokens)
- Nemotron-Pretraining-Code-v2 (836M rows)
- Nemotron-CC-Math-v1 (190M rows)

### Tier 3: Nous Research
- Atropos Artifacts (RL-trained specialists)
- SWE-smith-oracle (10.2K code tasks)

### Tier 4: Multimodal
- Open-MM-RL (multimodal STEM reasoning)
- Cosmos3-Nano training data (1.3B data points)

## Hardware Targets

| Tier | VRAM | Model Config | Context |
|------|------|-------------|---------|
| 8GB | RTX 4060 | IQ3_XS + CPU offload | 32K |
| 16GB | RTX 4080 | Q4_K_M | 128K |
| 24GB | RTX 3090 | Q4_K_M + flash attn | 262K |
| 32GB | RTX 5090 | Q5_K_M | 512K |
| 48GB | RTX 6000 | Q6_K | 1M |

## Release Pipeline

1. Darwin evolution produces candidate model
2. Benchmark suite validates quality
3. GGUF quantization at multiple tiers
4. Upload to `sovthpaw/omnisenter-*` on HuggingFace
5. Update model card with benchmark results
6. Post announcement to Discord #📊-data-inventory
