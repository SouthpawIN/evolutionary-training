# Darwin Family

> **The CMA-ES + paper-exact merge methodology.** See the
> [`evolutionary-model-merging`](https://github.com/SouthpawIN/evolutionary-model-merging) repo
> and the [5-stage pipeline blog post](../../blog/the-5-stage-pipeline.md).

## Definition

**Darwin Family** is the training-free weight-space recombination
methodology (per
[arXiv:2605.14386](https://arxiv.org/abs/2605.14386), Kim et al., 2026).
It takes two pretrained LLMs and finds, **with zero gradient updates**,
a linear combination of their weights that outperforms either parent.

The mechanism is:
- A **14-dim genome** (the search vector)
- **MRI-Trust Fusion** (the linear combination formula)
- **Architecture Mapper** (handles cross-arch tensors, skips if mismatched)
- **CMA-ES** (the optimizer for the genome)

## The 14-dim genome

```python
{
  "gamma": 0.5,        # MRI-Trust attention weight
  "alpha_attn": 0.5,   # attention vs FFN balance
  "alpha_ffn": 0.5,
  "alpha_emb": 0.5,
  "rho_a": 0.5,        # rank reduction A
  "rho_b": 0.5,        # rank reduction B
  "r0": 0.5, "r1": 0.5, "r2": 0.5, "r3": 0.5,
  "r4": 0.5, "r5": 0.5, # per-tensor ratios
  "tau": 0.4,          # MRI-vs-genome blend
  "lambda_reg": 0.01   # regularization
}
```

## How it's used in the OmniSenter pipeline

| Stage | What Darwin does |
|---|---|
| **Stage 2** | `cma_es_evolution.py` searches optimal merge weights across 3 specialized Senter-8B variants |
| **Stage 3** | The merged Senter-8B becomes the base for sparse upcycling to the 32B MoE |
| **Ohm** | The Darwin merge is what makes the Ohm engine cheap (seconds per candidate, not hours) |
| **External** | `continuous_evolution.py` in `evolutionary-training` does the same loop externally |

## Why it works

The Darwin paper's intuition: high-performing models lie in a
low-dimensional manifold of weight space, and CMA-ES can navigate that
manifold. The reason it works for LLMs:
- Transformer blocks have a regular structure
- Attention and FFN layers can be averaged across compatible shapes
- The Architecture Mapper handles cross-arch mismatches

## See also

- Repo: [`SouthpawIN/evolutionary-model-merging`](https://github.com/SouthpawIN/evolutionary-model-merging)
- Blog post: [`../../blog/the-5-stage-pipeline.md`](../../blog/the-5-stage-pipeline.md) (Stage 2 specifically)
- Blog post: [`../../blog/generative-darwin-evolution.md`](../../blog/generative-darwin-evolution.md) (extending to DiT/audio)
- Related: [Ohm](./ohm.md) · [Omnimodal Fusion](./omnimodal-fusion.md) · [Senter Ohm](./senter-ohm.md)
- Paper: [arXiv:2605.14386](https://arxiv.org/abs/2605.14386)
