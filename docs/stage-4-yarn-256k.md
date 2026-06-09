# Stage 4: YaRN RoPE 256K Context Extension

> **TOWARDS SELF-IMPROVEMENT** — a 2026-06-09 ops doc
> *The shortest stage: extend the Senter 32A8B MoE from native context
> to 256K using YaRN. Most of the work is already done by the existing
> `yarn_256k_config.py` script + `train_long_context.py` long-context
> SFT.*

## What Stage 4 produces

A Senter MoE with **256K context window** (vs the 40K native of Qwen3
backbone). This is required for the notebook feature (per memory:
"Wiki = handoff" + "notebook is the killer feature" — the notebook
ingests long context like the entire conversation history, recent
notebook entries, all retrieved context, etc.).

| Metric | Value |
|---|---|
| Original context (Qwen3-8B native) | 40,960 tokens |
| Target context (YaRN) | 256,000 tokens |
| Scale factor | **6.25x** |
| KV cache @ 256K (no compression) | ~5.7 GB (36L × 32 heads × 128 dim × 2 × 256K × 2 bytes) |
| KV cache @ 256K with turbo4 (~8x compression) | ~700 MB |
| Long-context SFT duration | ~8-16 hours |

## The two-step process

### Step 1: Apply YaRN scaling config (instant, CPU-only)

The existing `scripts/yarn_256k_config.py` does this. It writes a
new `config.json` with `rope_scaling` set to YaRN params, and copies
all other files from the source checkpoint.

```bash
cd ~/projects/evolutionary-training
python3 scripts/yarn_256k_config.py \
    --model       evolution/gen-3-moe/senter-moe-32a8b-warm \
    --output      evolution/gen-4-256k/senter-moe-32a8b-yarn \
    --target-ctx  256000 \
    --original-ctx 40960
```

**Wall time:** ~1 second (it's a config file write + a directory copy).

The YaRN params used (per the existing script):
- `type: "yarn"`
- `factor: 6.25` (256K / 40K)
- `original_max_position_embeddings: 40960`
- `beta_fast: 32, beta_slow: 1`
- `mscale: 1.0, mscale_all_dim: 1.0`

### Step 2: Long-context SFT (continued training, ~8-16 hours)

The existing `scripts/train_long_context.py` runs continued SFT with
the long-context data. Need to verify it works with the MoE arch (the
sparse upcycle produces a custom MoE model class, may need a small
monkey-patch in the training loop).

```bash
cd ~/projects/evolutionary-training
python3 scripts/train_long_context.py \
    --model       evolution/gen-4-256k/senter-moe-32a8b-yarn \
    --data        training-data/prepared/long_context_sft.jsonl \
    --epochs      1 --lr 5e-5 \
    --batch-size  1 --gradient-accum 16 \
    --max-seq-len 32768 \
    --output-dir  evolution/gen-4-256k/senter-moe-32a8b-256k
```

**Wall time on 2× 3090:** ~8-16 hours, depending on dataset size.

**Long-context data:** a mix of:
- 50% long-agentic (multi-turn tool use over 8K+ tokens)
- 30% retrieval (notebook-style: query + long context + answer)
- 20% raw long-context (book chapters, long code, transcripts)

## What already exists vs what needs writing

| Piece | Status | Path |
|---|---|---|
| `yarn_256k_config.py` | ✅ DONE | `scripts/yarn_256k_config.py` |
| `train_long_context.py` | ✅ DONE (need to verify MoE compat) | `scripts/train_long_context.py` |
| Long-context SFT data | 🆕 NEED TO BUILD | `training-data/prepared/long_context_sft.jsonl` |
| MoE-compat patch for HF Trainer | 🟡 Likely needed (verify) | (in the script or monkey-patch) |
| Post-YaRN smoke test at 256K | 🆕 NEED TO WRITE | `scripts/test_256k_context.py` |
| KV cache turbo4 verification | 🆕 NEED TO RUN | (validate llama.cpp `turbo2/4` works at 256K) |

## The MoE compatibility question

**The big unknown:** the sparse upcycle creates a custom MoE model
class. Will HuggingFace's `SFTTrainer` + TRL handle it? Two cases:

1. **Works out of the box** — if `sparse_upcycle.py` writes a config
   that maps to a known HF architecture (e.g. it monkey-patches
   Mixtral-style MoE). Likely path.
2. **Needs a custom architecture class** — if the upcycle uses a
   novel MoE pattern, we need to register a new `AutoModel` subclass
   before `SFTTrainer` can load it. Small code, but needs writing.

**Default plan:** try it as-is first. If it fails, write a small
`custom_moe_arch.py` that registers the new model class. ~30 min
extra work in the worst case.

## Wall time

| Step | Time on 2× 3090 |
|---|---|
| YaRN config apply | ~1 sec (CPU) |
| Long-context SFT (~5000 steps @ 8-15s/step) | ~8-16 hours |
| Smoke test | ~10-15 min |
| **Total** | **~8-16 hours** |

## Open questions for Chris

1. **Turbo4 vs raw KV cache at 256K** — turbo4 quantizes KV to q4_0
   (~8x compression) and we get ~700MB KV cache. Raw is ~5.7GB. The
   scripts assume turbo4 is available. Confirm llama.cpp build has
   `--cache-type-k turbo4` working at 256K.
2. **Long-context data source** — where does the long-context SFT data
   come from? Options: (a) long-agentic subset of Stage 1 data
   upsampled, (b) bookcorpus + long-arena, (c) notebook-style synthetic
   data, (d) all three mixed. Default = mix.
3. **Post-256K context, what gets shipped** — Senter 32A8B with 256K
   context, or just the long-context expert (with the rest of the MoE
   staying at 40K)? Default = full 256K (the YaRN scales the whole
   model, not just one expert).

## See also

- Stage 2 plan: [`stage-2-omnistep-plan.md`](stage-2-omnistep-plan.md)
- Stage 3 plan: [`stage-3-senter-moe.md`](stage-3-senter-moe.md)
- Script: [`../scripts/yarn_256k_config.py`](../scripts/yarn_256k_config.py)
- Script: [`../scripts/train_long_context.py`](../scripts/train_long_context.py)
- Blog (5-stage overview): [`../blog/the-5-stage-pipeline.md`](../blog/the-5-stage-pipeline.md)
- Wiki concept: [Senter](../wiki/concepts/senter.md) (the 32A8B MoE)
