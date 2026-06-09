# Stage 3: OmniStep → Senter 32A8B MoE (Sparse Upcycle)

> **TOWARDS SELF-IMPROVEMENT** — a 2026-06-09 ops doc
> *The Stage 3 build: turn the 8B-active OmniStep composite into a
> 32A8B MoE with 5-6 routed experts. Reference:*
> [`../blog/sparse-upcycling-deep-dive.md`](../blog/sparse-upcycling-deep-dive.md)
> *for the full math + design rationale (this doc is just the operational
> plan for the new architecture).*

## What Stage 3 produces

A ~32B-total / 8B-active MoE called **Senter** (Standard) or
**Senter Ohm** (with the self-evolution engine), built on top of the
OmniStep composite from Stage 2. Each FFN in OmniStep's text LLM body
gets copied N times to create N parallel "experts," with a small
router on top to dispatch per token.

| Metric | Value |
|---|---|
| Total params | ~32B (was ~24B in OmniStep) |
| Active per token (top-1) | ~8B (same as OmniStep) |
| Total disk @ 4-bit | ~18GB |
| Inference VRAM (1× 3090) | ~22GB |
| Training VRAM (2× 3090, QLoRA) | ~50GB peak (tight) |

## The expert lineup (5 routed + 1 generalist fallback)

We have the source models for 5 of the 6 experts in HF cache. The
6th (generalist fallback) is just a copy of the base — it diversifies
itself via continued training.

| # | Expert | Source (on disk?) | Distillation target | Status |
|---|---|---|---|---|
| 0 | **Agentic** | OmniStep itself (text LLM body) | Native — Expert 0 = base FFN | ✅ Always |
| 1 | **Image/video** | `Qwen/Qwen3-Omni-30B-A3B-Instruct` | FFN distillation | ✅ Have in cache |
| 2 | **Audio** | `Atotti/Qwen3-Omni-AudioTransformer` (Qwen3-Omni's audio tower) | FFN distillation | ✅ Have in cache |
| 3 | **Music** | ACE-Step (any of the 3 we just downloaded) | FFN distillation from `acestep-5Hz-lm-4B` (the Qwen3-based LM, not the DiT) | ✅ Just downloaded |
| 4 | **Long-context** | Stage 4 YaRN-extended model (chicken/egg — bootstrap from base until Stage 4 done) | FFN distillation | 🟡 Bootstrap from base |
| 5 | **Generalist fallback** | Copy of base | Diversifies via continued training | ✅ Always |

**Total: 6 experts, top-1 routing, ~35B params, 8B active.** The blog
post's "sweet spot" table.

## The continued training (router warm-up)

The upcycled model needs a **short** continued training to teach the
router which expert fires for which input. 1-5% of Stage 1's budget:

- Stage 1: 3954 steps at ~70s/step = ~77 hours
- Stage 3 continued: 100-200 steps at ~70s/step = ~2-4 hours

**Training data mix (per `sparse-upcycling-deep-dive.md`):**
- 50% agentic SFT (re-use `unified_sft_filtered.jsonl` from Stage 1)
- 20% multimodal examples (text descriptions of images/audio, Q&A)
- 20% specialist data (whatever the experts were distilled from)
- 10% retrieval examples (long-context, notebook-style)

The router is **trained from scratch** (uniform + small noise init).
The expert FFN weights are **frozen** at their source values — only
the router updates. This is the magic: converges in 100-200 steps
because the experts are already good.

## The exact command sequence

```bash
# Pre-flight: confirm all expert sources are on disk
ls ~/.cache/huggingface/hub/models--Qwen--Qwen3-Omni-30B-A3B-Instruct/  # ✅ have
ls ~/.cache/huggingface/hub/models--Atotti--Qwen3-Omni-AudioTransformer/  # ✅ have
ls ~/.cache/huggingface/hub/models--ACE-Step--acestep-5Hz-lm-4B/snapshots/_dl/  # ✅ have (just downloaded)
ls ~/projects/evolutionary-training/evolution/gen-2-omnistep/omnistep-v1/  # Stage 2 output, will be ready

# 1. Sparse upcycle the OmniStep text LLM body into a 6-expert MoE
cd ~/projects/multimodal-expansion-local
python3 scripts/sparse_upcycle.py \
    --base-model  ~/projects/evolutionary-training/evolution/gen-2-omnistep/omnistep-v1 \
    --expert-sources \
        ~/.cache/huggingface/hub/models--Qwen--Qwen3-Omni-30B-A3B-Instruct/snapshots/<HASH> \
        ~/.cache/huggingface/hub/models--Atotti--Qwen3-Omni-AudioTransformer/snapshots/<HASH> \
        ~/.cache/huggingface/hub/models--ACE-Step--acestep-5Hz-lm-4B/snapshots/_dl \
    --output      ~/projects/evolutionary-training/evolution/gen-3-moe/senter-moe-32a8b \
    --num-experts 6 --top-k 1 \
    --router-hidden 256 \
    --router-aux-loss-coef 0.01 \
    --jitter-noise 0.01

# 2. Router warm-up training (continued SFT, frozen FFNs, trainable router)
cd ~/projects/evolutionary-training
python3 scripts/train_long_context.py \  # REUSE the long-context trainer
    --base-model evolution/gen-3-moe/senter-moe-32a8b \
    --data training-data/prepared/router_warmup_mix.jsonl \
    --epochs 0.05 --lr 1e-4 \            # 0.05 epochs ≈ 100-200 steps
    --batch-size 2 --gradient-accum 8 \
    --max-seq-len 4096 \
    --output-dir evolution/gen-3-moe/senter-moe-32a8b-warm

# 3. (Optional) GGUF conversion for llama.cpp inference
python3 scripts/sparse_upcycle.py --convert-gguf \
    --input evolution/gen-3-moe/senter-moe-32a8b-warm \
    --output evolution/gen-3-moe/senter-moe-32a8b-warm-q4_k_m.gguf \
    --quantization Q4_K_M
```

**Note on GGUF conversion:** llama.cpp doesn't natively support MoE
architectures with custom routers. The script needs a custom
conversion that flattens the MoE to a multi-expert format. This is on
the roadmap, not done yet — skip the GGUF step on first try, use
HF safetensors for the MoE inference.

## Wall time

| Step | Time on 2× 3090 |
|---|---|
| Sparse upcycle (FFN copy + router init) | ~5-10 min |
| Router warm-up (200 steps) | ~2-4 hours |
| Smoke test (load + 4 expert routes) | ~10-15 min |
| **Total** | **~3-5 hours** |

## What already exists vs what needs writing

| Piece | Status | Path |
|---|---|---|
| `sparse_upcycle.py` | ✅ DONE | `multimodal-expansion-local/scripts/sparse_upcycle.py` |
| Router warm-up training loop | 🟡 REUSE `train_long_context.py` | `evolutionary-training/scripts/train_long_context.py` |
| Router warm-up data mix | 🆕 NEED TO BUILD | `training-data/prepared/router_warmup_mix.jsonl` |
| Expert distillation scripts (extract FFN from each source) | 🆕 NEED TO WRITE | `multimodal-expansion-local/scripts/distill_*.py` (one per source) |
| Custom MoE architecture class (HF compatible) | 🟡 Likely already in sparse_upcycle.py | (verify) |
| GGUF conversion for MoE | 🔴 NOT YET | (llama.cpp extension needed) |
| Expert routing visualization / monitoring | 🔮 FUTURE | (operational tool, not blocker) |

## Wild cards (per the blog post, still relevant)

1. **Expert collapse** — router always picks Expert 0. Fix: load-balancing
   aux loss. Script has it.
2. **Catastrophic forgetting** — continued training drifts experts. Fix:
   freeze FFN, only train router. Script has it.
3. **Router instability** — early router oscillates. Fix: jitter noise.
   Script has it.
4. **Expert quality variance** — some experts might be dead weight. Fix:
   per-expert usage monitoring, drop experts < 5% of tokens.

## Open questions for Chris

1. **Expert count** — 6 (per blog sweet spot) or 4 (stricter 8B-active
   via no-shared-expert design)? Default = 6.
2. **Long-context expert bootstrap** — do we initialize Expert 4 from
   the base (then specialize via continued training) or do we wait for
   Stage 4 YaRN extension to provide the source? Default = bootstrap
   from base, retrain after Stage 4.
3. **Distillation vs raw FFN copy** — for the image/video/audio experts
   (Qwen3-Omni sources), do we do proper knowledge distillation
   (logits matching) or just copy the FFN weights directly? Default =
   raw FFN copy for v1 (faster, simpler), add distillation for v2.
4. **Senter vs Senter Ohm** — Stage 3 produces the base MoE. Stage 5
   wires the Ohm engine. Should we ship Senter (no Ohm) first and add
   Ohm later, or do both in one push? Default = Senter first, Ohm in
   a follow-up.

## See also

- Blog (full design): [`../blog/sparse-upcycling-deep-dive.md`](../blog/sparse-upcycling-deep-dive.md)
- Blog (math): [`../blog/senter-ohm-32a8b-math.md`](../blog/senter-ohm-32a8b-math.md)
- Script: [`../../multimodal-expansion-local/scripts/sparse_upcycle.py`](../../multimodal-expansion-local/scripts/sparse_upcycle.py)
- Concept: [`../wiki/concepts/senter.md`](../wiki/concepts/senter.md) (the 32A8B MoE)
- Concept: [`../wiki/concepts/senter-ohm.md`](../wiki/concepts/senter-ohm.md) (with self-evolution)
- Stage 2 plan: [`stage-2-omnistep-plan.md`](stage-2-omnistep-plan.md) (the input to Stage 3)
- Stage 4 plan: [`stage-4-yarn-256k.md`](stage-4-yarn-256k.md) (the next step)
