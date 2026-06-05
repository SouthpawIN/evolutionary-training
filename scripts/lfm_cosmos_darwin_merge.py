#!/usr/bin/env python3
"""
Darwin Family Merge: LFM2.5 8B-A1B × Cosmos3-Nano

Cross-architecture Darwin merge of:
- Parent A: Cosmos3-Nano (15.75B, Cosmos3ForConditionalGeneration, omnimodal)
- Parent B: LFM2.5 8B-A1B (8.47B total/1B active, Lfm2MoeForCausalLM, tool-calling)

Architecture Mapper handles dimension mismatches by SKIPPING (keeps parent A).
Per-tensor MRI-Trust Fusion on shape-matched tensors.
Modality heads from Cosmos3-Nano attached separately (NOT merged).

Usage:
  python3 lfm_cosmos_darwin_merge.py \
    --cosmos-path /path/to/Cosmos3-Nano \
    --lfm-path /path/to/LFM2.5-8B-A1B \
    --output /path/to/output \
    [--rho-b 0.5] [--tau 0.4] [--genome-json genome.json]
"""

import os, json, time, gc, argparse, shutil
from pathlib import Path
import torch
import safetensors.torch as st

# Paper-fixed constants
ALPHA_MRI = 0.5
TAU_DEFAULT = 0.4


def load_sf(p, prefix=None, max_files=None, recursive=True):
    """Load safetensors, optionally filtering by key prefix.
    
    Searches recursively by default to handle models with subdirectories
    (e.g., Cosmos3-Nano has transformer/, vision_encoder/, sound_tokenizer/).
    """
    s = {}
    if recursive:
        files = sorted(Path(p).rglob("*.safetensors"))
    else:
        files = sorted(Path(p).glob("*.safetensors"))
    if max_files:
        files = files[:max_files]
    for f in files:
        try:
            d = st.load_file(str(f), device="cpu")
            if prefix:
                d = {k: v for k, v in d.items() if k.startswith(prefix)}
            s.update(d)
        except Exception as e:
            print(f"  Warning: failed to load {f.name}: {e}")
    return s


def extract_cosmos_text(tensors):
    """Extract text LLM body from Cosmos3-Nano.
    
    Cosmos3-Nano structure (Cosmos3ForConditionalGeneration):
    - Direct: layers.*, embed_tokens.weight, lm_head.weight
    - Modality: *_modality_embed (action, audio)
    - MoE twins: layers.*.*_moe_gen.* (generation expert twins)
    - Cross-attn: layers.*.self_attn.add_*/to_add_*/norm_added_*
    - Separate dirs: transformer/, vision_encoder/, sound_tokenizer/, vae/
    """
    out = {}
    for k, v in tensors.items():
        # Text backbone (direct layers.*)
        if k.startswith("layers."):
            out[k] = v
        elif k == "embed_tokens.weight":
            out["embed_tokens.weight"] = v
        elif k == "lm_head.weight":
            out["lm_head.weight"] = v
        # Skip: modality embeds, separate component dirs
    print(f"  [Cosmos3-Nano] extracted {len(out)} text tensors "
          f"(lm_head={'lm_head.weight' in out})")
    return out


def extract_lfm_text(tensors):
    """Extract text body from LFM2.5 8B-A1B.
    
    LFM2.5 uses Lfm2MoeForCausalLM:
    - model.* for the MoE backbone
    - lm_head.weight for the language head
    - MoE expert weights are in model.layers.*.experts.*
    """
    out = {}
    for k, v in tensors.items():
        if k.startswith("model."):
            out[k.replace("model.", "", 1)] = v
        elif k in ("lm_head.weight",):
            out["lm_head.weight"] = v
    print(f"  [LFM2.5] extracted {len(out)} text tensors "
          f"(lm_head={'lm_head.weight' in out})")
    return out


def static_term(t):
    """Paper's Static: normalized entropy + variance + capped l2-norm."""
    a = t.float().abs() + 1e-12
    p = a / a.sum()
    H = -(p * p.log()).sum()
    V = t.float().var().sqrt() + 1e-12
    N = torch.clamp(t.float().norm(), max=t.float().norm().item() / 5 + 1e-12)
    return H + V.sqrt() + N.log()


def mri_trust_r(t_a, t_b, rho_b=0.5, tau=TAU_DEFAULT):
    """Paper Eq: r_final = tau*r_MRI + (1-tau)*r_genome"""
    static_a = static_term(t_a)
    static_b = static_term(t_b)
    r_mri = static_b / (static_a + static_b)
    r_genome = rho_b
    return tau * r_mri + (1 - tau) * r_genome


def darwin_merge(theta_a, theta_b, rho_b=0.5, tau=TAU_DEFAULT):
    """Paper-exact 2-parent Darwin merge with Architecture Mapper.
    
    For cross-architecture (different shapes), the Architecture Mapper
    SKIPS dim-mismatched tensors (keeps parent A). NO random projection.
    """
    out = {}
    shared = sorted(set(theta_a.keys()) & set(theta_b.keys()))
    a_only = sorted(set(theta_a.keys()) - set(theta_b.keys()))
    b_only = sorted(set(theta_b.keys()) - set(theta_a.keys()))

    merged_count = 0
    skipped_count = 0

    # Parent A exclusive -> keep A
    for k in a_only:
        out[k] = theta_a[k]

    # Shared tensors -> shape check then merge
    for k in shared:
        ta, tb = theta_a[k], theta_b[k]
        if ta.shape != tb.shape:
            # Architecture Mapper: SKIP on dim mismatch (keep parent A)
            out[k] = ta
            skipped_count += 1
        else:
            # Paper-exact MRI-Trust Fusion
            r = mri_trust_r(ta, tb, rho_b=rho_b, tau=tau)
            out[k] = ((1 - r) * ta.float() + r * tb.float()).to(ta.dtype)
            merged_count += 1

    # Parent B exclusive -> skip (Architecture Mapper drops these)
    print(f"  Merge stats: {merged_count} merged, {skipped_count} skipped (dim mismatch), "
          f"{len(a_only)} A-only kept, {len(b_only)} B-only dropped")
    return out


def save_sharded(tensors, output_dir, max_shard_bytes=5_000_000_000):
    """Save tensors as sharded safetensors."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    shards = []
    current_shard = {}
    current_bytes = 0
    shard_idx = 0

    for k in sorted(tensors.keys()):
        v = tensors[k]
        nbytes = v.numel() * v.element_size()
        if current_bytes + nbytes > max_shard_bytes and current_shard:
            shards.append(current_shard)
            current_shard = {}
            current_bytes = 0
        current_shard[k] = v
        current_bytes += nbytes

    if current_shard:
        shards.append(current_shard)

    weight_map = {}
    for i, shard in enumerate(shards):
        fname = f"model-{i+1:05d}-of-{len(shards):05d}.safetensors"
        st.save_file(shard, str(output_dir / fname))
        for k in shard:
            weight_map[k] = fname
        print(f"  Saved shard {fname} ({len(shard)} tensors)")

    # Write index
    index = {
        "metadata": {"total_size": sum(v.numel() * v.element_size() for v in tensors.values())},
        "weight_map": weight_map,
    }
    with open(output_dir / "model.safetensors.index.json", "w") as f:
        json.dump(index, f, indent=2)


def copy_config_and_tokenizers(cosmos_path, lfm_path, output_dir):
    """Copy config and tokenizer files from parent A (Cosmos3-Nano)."""
    output_dir = Path(output_dir)
    config_files = [
        "config.json", "tokenizer.json", "tokenizer_config.json",
        "vocab.json", "merges.txt", "special_tokens_map.json",
        "added_tokens.json", "preprocessor.json", "preprocessor_config.json",
        "generation_config.json",
    ]
    for fname in config_files:
        for src in [Path(cosmos_path) / fname, Path(lfm_path) / fname]:
            if src.exists():
                shutil.copy2(src, output_dir / fname)
                print(f"  Copied {fname} from {src.parent.name}")
                break


def main():
    parser = argparse.ArgumentParser(description="Darwin Merge: LFM2.5 × Cosmos3-Nano")
    parser.add_argument("--cosmos-path", required=True, help="Path to Cosmos3-Nano model")
    parser.add_argument("--lfm-path", required=True, help="Path to LFM2.5-8B-A1B model")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--rho-b", type=float, default=0.5, help="Parent B density (genome)")
    parser.add_argument("--tau", type=float, default=TAU_DEFAULT, help="MRI-Trust coefficient")
    parser.add_argument("--genome-json", help="Full 14-dim genome JSON (overrides rho-b/tau)")
    parser.add_argument("--dry-run", action="store_true", help="Load and report only")
    args = parser.parse_args()

    # Load genome if provided
    rho_b = args.rho_b
    tau = args.tau
    if args.genome_json:
        with open(args.genome_json) as f:
            genome = json.load(f)
        rho_b = genome.get("rho_b", rho_b)
        tau = genome.get("tau", tau)
        print(f"  Loaded genome: rho_b={rho_b:.4f}, tau={tau:.4f}")

    print(f"\n{'='*60}")
    print(f"Darwin Family Merge: LFM2.5 × Cosmos3-Nano")
    print(f"{'='*60}")
    print(f"  Parent A: Cosmos3-Nano ({args.cosmos_path})")
    print(f"  Parent B: LFM2.5 8B-A1B ({args.lfm_path})")
    print(f"  rho_b={rho_b:.4f}, tau={tau:.4f}")
    print(f"  Output: {args.output}")
    print()

    # Load parent tensors
    print("[1/5] Loading Cosmos3-Nano tensors...")
    cosmos_raw = load_sf(args.cosmos_path)
    cosmos_text = extract_cosmos_text(cosmos_raw)

    print("\n[2/5] Loading LFM2.5 tensors...")
    lfm_raw = load_sf(args.lfm_path)
    lfm_text = extract_lfm_text(lfm_raw)

    if args.dry_run:
        shared = set(cosmos_text.keys()) & set(lfm_text.keys())
        shape_match = sum(1 for k in shared if cosmos_text[k].shape == lfm_text[k].shape)
        print(f"\n  DRY RUN: {len(shared)} shared keys, {shape_match} shape-matched")
        print(f"  A-only: {len(set(cosmos_text.keys()) - set(lfm_text.keys()))}")
        print(f"  B-only: {len(set(lfm_text.keys()) - set(cosmos_text.keys()))}")
        return

    # Darwin merge
    print("\n[3/5] Running Darwin merge (MRI-Trust Fusion)...")
    t0 = time.time()
    merged = darwin_merge(cosmos_text, lfm_text, rho_b=rho_b, tau=tau)
    print(f"  Merge took {time.time()-t0:.1f}s")

    # Save
    print("\n[4/5] Saving merged model...")
    save_sharded(merged, args.output)

    print("\n[5/5] Copying config and tokenizer files...")
    copy_config_and_tokenizers(args.cosmos_path, args.lfm_path, args.output)

    print(f"\n{'='*60}")
    print(f"Done! Merged model at: {args.output}")
    print(f"  Total tensors: {len(merged)}")
    print(f"  Genome: rho_b={rho_b:.4f}, tau={tau:.4f}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
