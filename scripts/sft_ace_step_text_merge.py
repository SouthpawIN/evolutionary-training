#!/usr/bin/env python3
"""
Stage 2 Sub-op A: Darwin-merge the 8B SFT text body with the ACE-Step 5Hz-LM-4B.

This produces the "OmniStep text backbone" — a single 8B-ish text LLM
that has the agentic/tool-use capabilities of the SFT body blended
with the lyric-planning/music-captioning capabilities of the ACE-Step LM.

Parent A: 8B SFT (Qwen3-8B base, agentic LoRA-merged into gen-0-clean)
          — exposes the same Qwen3 text-layer schema as Parent B
Parent B: ACE-Step 5Hz-LM-4B (Qwen3-4B base, music-lyric SFT)
          — same Qwen3 architecture, smaller hidden, fewer layers

Same-architecture: BOTH are Qwen3-derived text LMs. The hidden sizes
differ (4096 vs 2560) so we can't do a true per-tensor MRI-Trust Fusion
on all layers. Strategy:

  - Embeddings: tie to Parent A's (SFT) — agentic SFT needs full vocab
  - Per-layer: down/up-project Parent B's layers into Parent A's hidden
    dim, then Darwin-merge at the projected representation, then up-project
    back. This is the standard "cross-dim merge" trick.
  - LM head: tie to Parent A's

Usage:
  python3 sft_ace_step_text_merge.py \\
    --sft-path   evolution/gen-1-sft/omnisenter-8b-sft-merged \\
    --ace-lm-path ~/.cache/huggingface/hub/models--ACE-Step--acestep-5Hz-lm-4B/snapshots/<HASH> \\
    --output     evolution/gen-2-omnistep/omnistep-text-backbone \\
    [--rho-b 0.4] [--tau 0.4] [--dry-run]

NOTE: This is a SKELETON — the cross-dim projection merge needs the
actual Qwen3 hidden sizes verified at runtime. The pattern follows
cosmos_qwen3_darwin_merge.py (same-architecture MRI-Trust Fusion) but
adds a learned linear projection step.

Status: DRAFT (2026-06-09). Not yet run. Awaiting Stage 1 SFT completion.
"""
import argparse, json, time, gc, shutil
from pathlib import Path
import torch
import safetensors.torch as st

ALPHA_MRI = 0.5
TAU_DEFAULT = 0.4


def load_sf(p):
    """Load all safetensors from a path."""
    s = {}
    files = sorted(Path(p).rglob("*.safetensors"))
    for f in files:
        try:
            d = st.load_file(str(f), device="cpu")
            s.update(d)
        except Exception as e:
            print(f"  Warning: failed to load {f.name}: {e}")
    return s


def get_qwen3_hidden(model_path):
    """Read hidden_size, num_hidden_layers, num_attention_heads from config.json."""
    cfg = json.load(open(Path(model_path) / "config.json"))
    return {
        "hidden_size": cfg["hidden_size"],
        "num_hidden_layers": cfg["num_hidden_layers"],
        "num_attention_heads": cfg["num_attention_heads"],
        "num_key_value_heads": cfg.get("num_key_value_heads", cfg["num_attention_heads"]),
        "vocab_size": cfg["vocab_size"],
    }


def mri_trust_r(t_a, t_b, rho_b=0.5, tau=TAU_DEFAULT):
    """Paper Eq: r_final = tau*r_MRI + (1-tau)*r_genome"""
    a = t_a.float().abs() + 1e-12
    p = a / a.sum()
    H = -(p * p.log()).sum()
    V = t_a.float().var().sqrt() + 1e-12
    N = torch.clamp(t_a.float().norm(), max=t_a.float().norm().item() / 5 + 1e-12)
    static_a = H + V.sqrt() + N.log()

    a2 = t_b.float().abs() + 1e-12
    p2 = a2 / a2.sum()
    H2 = -(p2 * p2.log()).sum()
    V2 = t_b.float().var().sqrt() + 1e-12
    N2 = torch.clamp(t_b.float().norm(), max=t_b.float().norm().item() / 5 + 1e-12)
    static_b = H2 + V2.sqrt() + N2.log()

    r_mri = static_b / (static_a + static_b)
    r_genome = rho_b
    return tau * r_mri + (1 - tau) * r_genome


def cross_dim_merge(t_a, t_b, proj_a_to_b, proj_b_to_a, rho_b=0.5, tau=TAU_DEFAULT):
    """
    Cross-dim Darwin merge:
      1. Project both to a shared dim (use the smaller one as target)
      2. MRI-Trust-Fuse in shared space
      3. Project back to A's space (preserves A's shape)

    t_a: A's tensor (target shape)
    t_b: B's tensor (different shape, e.g. smaller hidden)
    proj_a_to_b: Linear(t_a.shape[-1] -> t_b.shape[-1])
    proj_b_to_a: Linear(t_b.shape[-1] -> t_a.shape[-1])
    """
    with torch.no_grad():
        a_proj = proj_a_to_b(t_a.float())  # -> B's dim
        b_proj = t_b.float()                # already in B's dim
        r = mri_trust_r(a_proj, b_proj, rho_b=rho_b, tau=tau)
        fused = ((1 - r) * a_proj + r * b_proj)
        return proj_b_to_a(fused).to(t_a.dtype)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sft-path", required=True, help="Path to 8B SFT (LoRA-merged)")
    parser.add_argument("--ace-lm-path", required=True, help="Path to ACE-Step 5Hz-LM-4B")
    parser.add_argument("--output", required=True, help="Output dir for merged text backbone")
    parser.add_argument("--rho-b", type=float, default=0.4,
                        help="Genome weight on Parent B (ACE-Step). 0.4 = 40%% ACE, 60%% SFT.")
    parser.add_argument("--tau", type=float, default=TAU_DEFAULT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"Stage 2 Sub-op A: SFT × ACE-Step LM text merge")
    print(f"{'='*60}")

    sft_cfg = get_qwen3_hidden(args.sft_path)
    ace_cfg = get_qwen3_hidden(args.ace_lm_path)
    print(f"  SFT (Parent A):  {sft_cfg}")
    print(f"  ACE  (Parent B): {ace_cfg}")
    print(f"  rho_b={args.rho_b}, tau={args.tau}")
    print(f"  Output: {args.output}")

    if sft_cfg["vocab_size"] != ace_cfg["vocab_size"]:
        print(f"  WARNING: vocab mismatch (SFT={sft_cfg['vocab_size']}, "
              f"ACE={ace_cfg['vocab_size']}). Will tie embeddings to SFT's vocab.")

    if sft_cfg["hidden_size"] == ace_cfg["hidden_size"]:
        print(f"  Same hidden size — pure per-tensor MRI-Trust Fusion")
    else:
        print(f"  Cross-dim: SFT hidden={sft_cfg['hidden_size']}, "
              f"ACE hidden={ace_cfg['hidden_size']}. Using linear projections.")

    if args.dry_run:
        print("\n  DRY RUN — not merging.")
        return

    t0 = time.time()
    print(f"\n[1/4] Loading SFT tensors...")
    sft_t = load_sf(args.sft_path)
    print(f"  {len(sft_t)} SFT tensors")

    print(f"\n[2/4] Loading ACE-Step LM tensors...")
    ace_t = load_sf(args.ace_lm_path)
    print(f"  {len(ace_t)} ACE-Step LM tensors")

    # Build cross-dim projections (if needed)
    if sft_cfg["hidden_size"] != ace_cfg["hidden_size"]:
        torch.manual_seed(42)
        proj_a_to_b = torch.nn.Linear(sft_cfg["hidden_size"], ace_cfg["hidden_size"], bias=False)
        proj_b_to_a = torch.nn.Linear(ace_cfg["hidden_size"], sft_cfg["hidden_size"], bias=False)
        # Xavier init
        torch.nn.init.xavier_uniform_(proj_a_to_b.weight)
        torch.nn.init.xavier_uniform_(proj_b_to_a.weight)
        proj_a_to_b = proj_a_to_b.weight.T  # [hidden_sft, hidden_ace]
        proj_b_to_a = proj_b_to_a.weight.T  # [hidden_ace, hidden_sft]
    else:
        proj_a_to_b = proj_b_to_a = None

    # Find shared text-layer keys
    sft_text_keys = {k for k in sft_t if "layers." in k or k in (
        "embed_tokens.weight", "lm_head.weight", "model.embed_tokens.weight", "model.norm.weight"
    )}
    ace_text_keys = {k for k in ace_t if "layers." in k or k in (
        "embed_tokens.weight", "lm_head.weight", "model.embed_tokens.weight", "model.norm.weight"
    )}

    # Strip "model." prefix for matching
    def strip_prefix(k):
        return k.replace("model.", "", 1) if k.startswith("model.") else k
    sft_norm = {strip_prefix(k): k for k in sft_text_keys}
    ace_norm = {strip_prefix(k): k for k in ace_text_keys}
    shared = sorted(set(sft_norm.keys()) & set(ace_norm.keys()))
    print(f"\n  Shared text keys: {len(shared)}")

    # Merge
    print(f"\n[3/4] Running cross-dim Darwin merge...")
    out = {}
    for k in shared:
        ta = sft_t[sft_norm[k]]
        tb = ace_t[ace_norm[k]]
        if ta.shape == tb.shape:
            # Same shape, pure MRI-Trust
            r = mri_trust_r(ta, tb, rho_b=args.rho_b, tau=args.tau)
            out[k] = ((1 - r) * ta.float() + r * tb.float()).to(ta.dtype)
        elif ta.dim() == 2 and tb.dim() == 2 and ta.shape[-1] == tb.shape[-1]:
            # Same feature dim, different rows (e.g. embeddings with different vocab)
            # Use the smaller vocab's slice, then concatenate SFT-only rows
            min_vocab = min(ta.shape[0], tb.shape[0])
            ta_slice = ta[:min_vocab].float()
            tb_slice = tb[:min_vocab].float()
            r = mri_trust_r(ta_slice, tb_slice, rho_b=args.rho_b, tau=args.tau)
            fused = ((1 - r) * ta_slice + r * tb_slice).to(ta.dtype)
            if ta.shape[0] > min_vocab:
                # Keep SFT's extra rows (e.g. added agentic tokens)
                fused = torch.cat([fused, ta[min_vocab:]], dim=0)
            out[k] = fused
        elif proj_a_to_b is not None:
            # Cross-dim: project both to shared, merge, project back
            out[k] = cross_dim_merge(ta, tb, proj_a_to_b, proj_b_to_a,
                                     rho_b=args.rho_b, tau=args.tau)
        else:
            # Can't merge, keep SFT
            print(f"  WARNING: {k} shape mismatch ({ta.shape} vs {tb.shape}), keeping SFT")
            out[k] = ta

    # Add SFT-only keys (e.g. agentic-specific tensors, LoRA residuals if any)
    sft_only = set(sft_norm.keys()) - set(ace_norm.keys())
    for k in sft_only:
        out[k] = sft_t[sft_norm[k]]
    print(f"  Kept {len(sft_only)} SFT-only tensors (agentic additions)")

    del sft_t, ace_t; gc.collect()

    # Save
    print(f"\n[4/4] Saving to {args.output}...")
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sharded save
    shards = [{}]
    shard_bytes = [0]
    MAX_SHARD = 5_000_000_000
    weight_map = {}
    for k in sorted(out.keys()):
        v = out[k]
        nbytes = v.numel() * v.element_size()
        if shard_bytes[0] + nbytes > MAX_SHARD and shards[-1]:
            shards.append({})
            shard_bytes.append(0)
        shards[-1][k] = v
        shard_bytes[-1] += nbytes
        weight_map[k] = f"model-{len(shards):05d}-of-XXXXX.safetensors"

    # Finalize names
    n_shards = len(shards)
    for i, shard in enumerate(shards):
        fname = f"model-{i+1:05d}-of-{n_shards:05d}.safetensors"
        for k in shard:
            weight_map[k] = fname
        st.save_file(shard, str(output_dir / fname))
        print(f"  Saved {fname} ({len(shard)} tensors)")

    json.dump(
        {"metadata": {"total_size": sum(v.numel() * v.element_size() for v in out.values())},
         "weight_map": weight_map},
        open(output_dir / "model.safetensors.index.json", "w"), indent=2
    )

    # Copy configs/tokenizer from SFT (the canonical text-LLM side)
    for fname in ["config.json", "tokenizer.json", "tokenizer_config.json",
                  "vocab.json", "merges.txt", "special_tokens_map.json",
                  "added_tokens.json", "generation_config.json"]:
        src = Path(args.sft_path) / fname
        if src.exists():
            shutil.copy2(src, output_dir / fname)

    # Merge metadata
    json.dump({
        "merge_type": "darwin_cross_dim_text",
        "parent_a": str(args.sft_path),
        "parent_b": str(args.ace_lm_path),
        "rho_b": args.rho_b,
        "tau": args.tau,
        "total_tensors": len(out),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "merge_time_s": round(time.time() - t0, 1),
    }, open(output_dir / "merge_metadata.json", "w"), indent=2)

    print(f"\n{'='*60}")
    print(f"✅ Text backbone merge complete!")
    print(f"   Tensors: {len(out)}, Time: {time.time()-t0:.1f}s")
    print(f"   Output: {output_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
