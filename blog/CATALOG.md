# OmniSenter Blog Catalog

The complete design catalog for the OmniSenter project. Every post covers one
facet of the vision, with the architecture wiki as the source of truth and
the code in the [evolutionary-training](https://github.com/SouthpawIN/evolutionary-training)
repo as the executable reference.

> **The headline:** OmniSenter is a **32B-A8B multimodal MoE** that serves
> as a notebook-keeping **auxiliary to Hermes Agent**. It has **Synthesia**
> (cross-modal memory), **Ohm** (self-evolution), and the **5-stage build
> pipeline** (agentic SFT → merge → sparse upcycle → 256K YaRN → wiring).
>
> — Chris, 2026-06-07

---

## The flagship post

**[OmniSenter: The Self-Evolving Multimodal Auxiliary for Hermes](./omnisenter-self-evolving.md)** (2026-06-07)
The overview. The vision, the architecture, the 5-stage pipeline, Synthesia,
Ohm, the math, the wild cards. Read this first.

## The deep dives

### [The 5-Stage Pipeline: Building OmniSenter from Scratch](./the-5-stage-pipeline.md)
Detailed walkthrough of each stage with inputs, outputs, scripts, expected
wall-time, and the gotchas. The "how do we actually build this" post.

### [The Notebook Schema: How OmniSenter Remembers What Hermes Doesn't](./the-notebook-schema.md)
The structured state object that flows between turns, between agents, and
across process boundaries. YAML spec, the write/read API, the compaction
policy, the privacy model.

### [Sparse Upcycling: Building a 32B MoE from an 8B Base](./sparse-upcycling-deep-dive.md)
The Stage 3 deep dive. The math (24A8B / 32A8B / 50A8B), the shared-expert
design, the script, the evaluation, the wild cards. The headline technical
post.

### [The 32A8B Math: How Big is OmniSenter Anyway?](./the-32a8b-math.md)
The full sizing breakdown. Per-layer params, active vs total, 4-bit vs bf16
disk, VRAM at inference, VRAM at training. With tables.

### [OmniSenter as the Hermes Auxiliary: The Integration Pattern](./omnisenter-as-hermes-auxiliary.md)
The use case. How OmniSenter fits in front of Hermes Agent via the existing
`auxiliary_client.py`. The notebook-as-API pattern. The escalation contract.

### [Generative Darwin Evolution: Darwin-merging DiT Weights](./generative-darwin-evolution.md)
The research direction. How Darwin methodology (MRI-Trust + Architecture
Mapper + CMA-ES) extends from text LLMs to DiT audio decoders, VAE, talkers.
Music/video/image/speech.

## The concepts (linked wiki pages)

- **[omnisenter-architecture](file:///home/sovthpaw/wiki/concepts/omnisenter-architecture.md)** — the master architecture doc (5 stages, plugin pattern, Synthesia, Ohm)
- **[synthesia](file:///home/sovthpaw/wiki/concepts/synthesia.md)** — cross-modal memory indexer (text + audio + image joint embedding)
- **[omnisenter-ohm](file:///home/sovthpaw/wiki/concepts/omnisenter-ohm.md)** — self-evolving model file (`.ohm` format + background CMA-ES loop)
- **[omnimodal-fusion-architecture](file:///home/sovthpaw/wiki/concepts/omnimodal-fusion-architecture.md)** — the 2026-06-06 master plan (Cosmos × ACE-Step × Nemotron ASR)
- **[omnistep-multimodal](file:///home/sovthpaw/wiki/concepts/omnistep-multimodal.md)** — the destination unified model
- **[darwin-family-paper](file:///home/sovthpaw/wiki/concepts/darwin-family-paper.md)** — the 14-dim genome, MRI-Trust Fusion, Architecture Mapper, CMA-ES
- **[evolutionary-radio](file:///home/sovthpaw/wiki/concepts/evolutionary-radio.md)** — the OmniStep-brained infinite generative music radio
- **[multi-agent-pipeline](file:///home/sovthpaw/wiki/concepts/multi-agent-pipeline.md)** — Nous Girl / Senter / Chizul music studio

## The code (linked scripts in the evolutionary-training repo)

### Build pipeline
- `scripts/train_omnisenter_sft_fixed.py` — Stage 1 agentic SFT (running now)
- `scripts/train_long_context.py` — Stage 4 long-context SFT
- `scripts/yarn_256k_config.py` — Stage 4 YaRN RoPE scaling
- `scripts/merge_lora.py` — LoRA merge for deploy
- `scripts/omnisenter_ohm.py` — 🔥 Ohm runtime (self-evolving model)
- `scripts/data_ingestion.py` — data prep
- `scripts/mega_training_data.py` — ShareGPT formatter
- `scripts/download_all_data.sh` — raw data downloader
- `scripts/agentic_training_loop.py` — agentic SFT loop with monitoring
- `scripts/continuous_evolution.py` — external Ohm-like loop (the inspiration for Ohm)

### Evaluation
- `scripts/benchmark_omnisenter.py` — main eval
- `scripts/darwin_benchmark.py` — Darwin eval
- `scripts/gpqa_benchmark.py` — GPQA reasoning
- `scripts/bfcl_benchmark.py` — BFCL function calling
- `scripts/hf_auto_upload.py` — HF upload

### Tooling
- `scripts/extract_clean_qwen3.py` — model surgery (strip multimodal tensors)
- `scripts/cosmos_qwen3_darwin_merge.py` — Darwin merge
- `scripts/discord_evolution_report.py` — Discord reporting
- `scripts/evolution_radio.py` — the radio loop

### External (in other repos)
- `multimodal-expansion/scripts/sparse_upcycle.py` — Stage 3 sparse upcycle
- `evolutionary-model-merging/cma_es_evolution.py` — CMA-ES engine
- `evolutionary-model-merging/paper_exact_2parent_merge.py` — Darwin paper-exact merge
- `evolutionary-model-merging/real_benchmark.py` — Darwin benchmark
- `evolutionary-model-merging/filter_for_gguf.py` — GGUF filter
- `hermes-agent/agent/auxiliary_client.py` — the integration point for OmniSenter

## The HuggingFace artifacts

- [sovthpaw/omnistep-12a3b](https://huggingface.co/sovthpaw/omnistep-12a3b) — the multimodal baseline (35GB, 4 GGUFs + 4 safetensors + cover)
- Legacy: [sovthpaw/omnistep-multimodal](https://huggingface.co/sovthpaw/omnistep-multimodal) (v0.1, 21GB safetensors, superseded)
- Upcoming: `sovthpaw/omnisenter-moe-32a8b` — the Stage 3 destination

## The repos

| Repo | What | Status |
|---|---|---|
| [SouthpawIN/evolutionary-training](https://github.com/SouthpawIN/evolutionary-training) | The main project (Stage 1 running, blog, scripts) | 🔄 active |
| [SouthpawIN/omnistep-fusion](https://github.com/SouthpawIN/omnistep-fusion) | Cosmos × ACE-Step fusion logic | ✅ initial |
| [SouthpawIN/evolutionary-radio](https://github.com/SouthpawIN/evolutionary-radio) | The infinite generative music radio | ✅ running |
| [SouthpawIN/evolutionary-model-merging](https://github.com/SouthpawIN/evolutionary-model-merging) | Darwin Family paper-exact implementation | ✅ published |
| [SouthpawIN/multimodal-expansion](https://github.com/SouthpawIN/multimodal-expansion) | REAP + EvoMoE + sparse upcycle | ✅ skill |
| [SouthpawIN/hermes-agent](https://github.com/SouthpawIN/hermes-agent) | The smart agent OmniSenter is auxiliary to | ✅ active |
| [SouthpawIN/senter](https://github.com/SouthpawIN/senter) | Hermes Agent profile (senter) | ✅ distribution |
| [SouthpawIN/nous-girl](https://github.com/SouthpawIN/nous-girl) | Hermes Agent profile (nous-girl) | ✅ distribution |
| [SouthpawIN/chizul](https://github.com/SouthpawIN/chizul) | Hermes Agent profile (chizul) | ✅ distribution |

## Brand & style

All images in this catalog are generated with FAL (managed by Nous subscription)
using the **Nous Research brand guide**:
- Strictly monochrome B&W with halftone grain (default)
- "Cosmic variant" exception: teal + gold nebula for hero/promotional art
- Retro manga / 70s shoujo line art
- Industrial typewriter / Swiss grid composition
- Tagline: "TOWARDS SELF-IMPROVEMENT"

See `references/brand-booklet-pages.md` in the nous-brand-guide skill for the
full spec.

---

## How to read this catalog

- **If you're new**: read the flagship post (omnisenter-self-evolving.md) first
- **If you're implementing**: read the 5-stage pipeline + the notebook schema
- **If you're researching**: read the 32A8B math + generative Darwin evolution
- **If you're integrating with Hermes**: read the auxiliary post
- **If you want to understand the why**: read the architecture wiki + the concept pages

## How to contribute

- Wiki pages live in `~/wiki/concepts/` — frontmatter format is YAML, lowercase
  hyphens, wikilinks for cross-references. See `SCHEMA.md`.
- Blog posts live in this `blog/` directory. Each post is one `.md` file plus
  images in `blog/assets/`. Cross-link to wiki pages with `[name](file:///home/sovthpaw/wiki/concepts/name.md)`.
- Scripts live in `scripts/` in evolutionary-training (or other repos for
  specific tools). Follow the pattern of existing scripts: argparse, docstring
  with usage, dataclass config, log to `logs/`.
- The training is running on `gen-0-clean` — **don't touch it** while it's
  grinding. The new scripts and the new architecture are for Stage 2 onwards.
