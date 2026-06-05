#!/usr/bin/env python3
"""
Darwin Family Merge: Cosmos3-Nano × Qwen3-8B

Same-architecture Darwin merge — both parents are Qwen3-based:
  - Cosmos3-Nano text backbone: hidden=4096, 36L, 32 heads, 8 KV, vocab=151936
  - Qwen3-8B: hidden=4096, 36L, 32 heads, 8 KV, vocab=151936

100% tensor shape match guaranteed. Every layer gets MRI-Trust fused.

Usage:
  python3 cosmos_qwen3_darwin_merge.py \
    --cosmos-path ~/Models/storage/Cosmos3-Nano \
    --qwen-path ~/Models/storage/Qwen3-8B \
    --output ~/projects/evolutionary-training/evolution/gen-0 \
    [--rho-b 0.5] [--tau 0.4] [--genome-json genome.json] \
    [--dry-run]
"""

import os, json, time, gc, argparse, shutil
from pathlib import Path
import torch
import safetensors.torch as st

ALPHA_MRI = 0.5
TAU_DEFAULT = 0.4


def load_sf(p, recursive=True):
    """Load all safetensors from a path."""
    s = {}
    files = sorted(Path(p).rglob("*.safetensors")) if recursive else sorted(Path(p).glob("*.safetensors"))
    for f in files:
        try:
            d = st.load_file(str(f), device="cpu")
            s.update(d)
        except Exception as e:
            print(f"  Warning: failed to load {f.name}: {e}")
    return s


# Cosmos3-Nano uses different attention key names than Qwen3-8B.
# Both are Qwen3-based but Cosmos has a renamed attention layout.
# This map translates Cosmos keys → Qwen3 keys for matching.
COSMOS_TO_QWEN_ATTN = {
    ".self_attn.to_q.weight":      ".self_attn.q_proj.weight",
    ".self_attn.to_k.weight":      ".self_attn.k_proj.weight",
    ".self_attn.to_v.weight":      ".self_attn.v_proj.weight",
    ".self_attn.to_out.weight":    ".self_attn.o_proj.weight",
    ".self_attn.norm_q.weight":    ".self_attn.q_norm.weight",
    ".self_attn.norm_k.weight":    ".self_attn.k_norm.weight",
}

# Cosmos extra keys (cross-modal attention, MoE twins) — kept separately, not merged
COSMOS_EXTRA_PATTERNS = [
    "_moe_gen",      # MoE generation expert twins
    "add_k_proj",    # Cross-modal attention
    "add_q_proj",
    "add_v_proj",
    "to_add_out",
    "norm_added_k",
    "norm_added_q",
    "_modality_embed",
]


def _rename_cosmos_key(k):
    """Translate a Cosmos attention key to Qwen3 naming."""
    for cosmos_suffix, qwen_suffix in COSMOS_TO_QWEN_ATTN.items():
        if k.endswith(cosmos_suffix):
            return k.replace(cosmos_suffix, qwen_suffix)
    return k


def _is_cosmos_extra(k):
    """Check if a key is a Cosmos-specific extra (cross-attn, MoE twin, modality)."""
    return any(pat in k for pat in COSMOS_EXTRA_PATTERNS)


def extract_cosmos_text(tensors):
    """Extract text LLM body from Cosmos3-Nano with key renaming.
    
    Extracts layers.*, embed_tokens.weight, lm_head.weight.
    Renames attention keys to match Qwen3 naming.
    Separately collects Cosmos-exclusive tensors (cross-attn, MoE twins).
    """
    text = {}
    extras = {}
    for k, v in tensors.items():
        if _is_cosmos_extra(k):
            extras[k] = v
            continue
        if k.startswith("layers.") or k in ("embed_tokens.weight", "lm_head.weight"):
            renamed = _rename_cosmos_key(k)
            text[renamed] = v
    print(f"  [Cosmos3-Nano] extracted {len(text)} text tensors (renamed attn keys)")
    print(f"  [Cosmos3-Nano] {len(extras)} exclusive tensors (cross-attn, MoE twins, modality)")
    return text, extras


def extract_qwen_text(tensors):
    """Extract text body from Qwen3-8B.
    
    Strip 'model.' prefix to match Cosmos key naming convention.
    """
    out = {}
    for k, v in tensors.items():
        if k.startswith("model."):
            out[k.replace("model.", "", 1)] = v
        elif k == "lm_head.weight":
            out[k] = v
    print(f"  [Qwen3-8B] extracted {len(out)} text tensors")
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
    """Same-architecture Darwin merge — ALL tensors merged via MRI-Trust Fusion."""
    out = {}
    shared = sorted(set(theta_a.keys()) & set(theta_b.keys()))
    a_only = sorted(set(theta_a.keys()) - set(theta_b.keys()))
    b_only = sorted(set(theta_b.keys()) - set(theta_a.keys()))

    merged = 0
    skipped = 0

    # Parent A exclusive -> keep A
    for k in a_only:
        out[k] = theta_a[k]

    # Shared tensors -> merge (same arch so shapes always match)
    for k in shared:
        ta, tb = theta_a[k], theta_b[k]
        if ta.shape != tb.shape:
            print(f"  WARNING: shape mismatch on {k}: {ta.shape} vs {tb.shape} — keeping A")
            out[k] = ta
            skipped += 1
        else:
            r = mri_trust_r(ta, tb, rho_b=rho_b, tau=tau)
            out[k] = ((1 - r) * ta.float() + r * tb.float()).to(ta.dtype)
            merged += 1

    # Parent B exclusive -> keep B (shouldn't happen in same-arch, but safety)
    for k in b_only:
        out[k] = theta_b[k]

    print(f"  Merge stats: {merged} merged, {skipped} skipped, "
          f"{len(a_only)} A-only, {len(b_only)} B-only")
    return out


def save_sharded(tensors, output_dir, max_shard_bytes=5_000_000_000):
    """Save tensors as sharded safetensors."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    shards = []
    current_shard = {}
    current_bytes = 0

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

    index = {
        "metadata": {"total_size": sum(v.numel() * v.element_size() for v in tensors.values())},
        "weight_map": weight_map,
    }
    with open(output_dir / "model.safetensors.index.json", "w") as f:
        json.dump(index, f, indent=2)


def copy_configs(cosmos_path, qwen_path, output_dir):
    """Copy config and tokenizer files (prefer Qwen3-8B for clean CausalLM config)."""
    output_dir = Path(output_dir)
    
    # Copy from Qwen3-8B first (it has the clean CausalLM config)
    qwen_files = [
        "config.json", "tokenizer.json", "tokenizer_config.json",
        "vocab.json", "merges.txt", "special_tokens_map.json",
        "added_tokens.json", "generation_config.json",
    ]
    for fname in qwen_files:
        src = Path(qwen_path) / fname
        if src.exists():
            shutil.copy2(src, output_dir / fname)
            print(f"  Copied {fname} from Qwen3-8B")
    
    # Copy chat template from Cosmos if it has one (it uses Qwen template)
    for tpl in ["chat_template.json", "chat_template.jinja"]:
        src = Path(cosmos_path) / tpl
        if src.exists():
            shutil.copy2(src, output_dir / tpl)
            print(f"  Copied {tpl} from Cosmos3-Nano")


def main():
    parser = argparse.ArgumentParser(description="Darwin Merge: Cosmos3-Nano × Qwen3-8B")
    parser.add_argument("--cosmos-path", required=True)
    parser.add_argument("--qwen-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--rho-b", type=float, default=0.5)
    parser.add_argument("--tau", type=float, default=TAU_DEFAULT)
    parser.add_argument("--genome-json", help="Full genome JSON (overrides rho-b/tau)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--generation", type=int, default=0, help="Generation number for metadata")
    args = parser.parse_args()

    rho_b = args.rho_b
    tau = args.tau
    if args.genome_json:
        with open(args.genome_json) as f:
            genome = json.load(f)
        rho_b = genome.get("rho_b", rho_b)
        tau = genome.get("tau", tau)
        print(f"  Loaded genome: rho_b={rho_b:.4f}, tau={tau:.4f}")

    print(f"\n{'='*60}")
    print(f"Darwin Family Merge: Cosmos3-Nano × Qwen3-8B")
    print(f"{'='*60}")
    print(f"  Parent A: Cosmos3-Nano ({args.cosmos_path})")
    print(f"  Parent B: Qwen3-8B ({args.qwen_path})")
    print(f"  rho_b={rho_b:.4f}, tau={tau:.4f}")
    print(f"  Generation: {args.generation}")
    print(f"  Output: {args.output}")
    print()

    t0 = time.time()

    # Load parents
    print("[1/5] Loading Cosmos3-Nano tensors...")
    cosmos_raw = load_sf(args.cosmos_path)
    cosmos_text, cosmos_extras = extract_cosmos_text(cosmos_raw)
    del cosmos_raw; gc.collect()

    print("\n[2/5] Loading Qwen3-8B tensors...")
    qwen_raw = load_sf(args.qwen_path)
    qwen_text = extract_qwen_text(qwen_raw)
    del qwen_raw; gc.collect()

    # Compatibility report
    shared = set(cosmos_text.keys()) & set(qwen_text.keys())
    shape_match = sum(1 for k in shared if cosmos_text[k].shape == qwen_text[k].shape)
    a_only = set(cosmos_text.keys()) - set(qwen_text.keys())
    b_only = set(qwen_text.keys()) - set(cosmos_text.keys())

    print(f"\n  Compatibility Report:")
    print(f"    Cosmos text tensors: {len(cosmos_text)}")
    print(f"    Qwen3 text tensors:  {len(qwen_text)}")
    print(f"    Shared keys:         {len(shared)}")
    print(f"    Shape-matched:       {shape_match}/{len(shared)}")
    print(f"    Cosmos-only:         {len(a_only)} ({', '.join(sorted(a_only)[:5])}{'...' if len(a_only)>5 else ''})")
    print(f"    Qwen-only:           {len(b_only)} ({', '.join(sorted(b_only)[:5])}{'...' if len(b_only)>5 else ''})")

    if args.dry_run:
        print(f"\n  DRY RUN — not merging. ({time.time()-t0:.1f}s)")
        return

    # Merge!
    print(f"\n[3/5] Running Darwin merge (MRI-Trust Fusion)...")
    merged = darwin_merge(cosmos_text, qwen_text, rho_b=rho_b, tau=tau)
    del cosmos_text, qwen_text; gc.collect()

    # Re-attach Cosmos-exclusive tensors (cross-attn, MoE twins, modality)
    merged.update(cosmos_extras)
    print(f"  Re-attached {len(cosmos_extras)} Cosmos-exclusive tensors")
    del cosmos_extras; gc.collect()

    # Save
    print(f"\n[4/5] Saving merged model to {args.output}...")
    save_sharded(merged, args.output)

    print(f"\n[5/5] Copying configs and tokenizers...")
    copy_configs(args.cosmos_path, args.qwen_path, args.output)

    # Write merge metadata
    meta = {
        "merge_type": "darwin_family",
        "parent_a": "nvidia/Cosmos3-Nano",
        "parent_b": "Qwen/Qwen3-8B",
        "rho_b": rho_b,
        "tau": tau,
        "generation": args.generation,
        "total_tensors": len(merged),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "merge_time_s": round(time.time() - t0, 1),
    }
    with open(Path(args.output) / "merge_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\n{'='*60}")
    print(f"✅ Gen-{args.generation} merge complete!")
    print(f"   Tensors: {len(merged)}, Time: {time.time()-t0:.1f}s")
    print(f"   Output: {args.output}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
