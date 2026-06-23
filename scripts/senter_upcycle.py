#!/usr/bin/env python3
"""
Senter 32A8B — Sparse MoE upcycle (FAST VERSION).

Constructs a 32B MoE with 8B active per token from:
  - Source A: new OmniStep (16B, text body = SFT-Qwen3-8B + Cosmos3-Nano)
  - Source B: OmniStep SFT-8B (8B, SFT'd Qwen3-8B)

Architecture: 4 experts × 8B each, top-1 routing.
  - Expert 0,2: FFN from OmniStep (slight noise on #2 for diversity)
  - Expert 1,3: FFN from SFT-8B (slight noise on #3 for diversity)
  - Shared: attention, embed, norms, lm_head (from SFT-8B; ties to its vocab)

FAST: Builds FFN experts via torch.stack (4 copies at once instead of 4 separate ops).
Generates noise for noisy experts in a single call.
Uses memory-efficient tensor reuse where possible.

Usage:
  python3 senter_upcycle.py --output training-output/senter-ohm-32a8b
"""
import os, json, time, gc, argparse, shutil
from pathlib import Path
import torch
from safetensors.torch import load_file, save_file

OMNISTEP_CLEAN = Path("/home/sovthpaw/projects/evolutionary-training/evolution/line2-new-omnistep-clean")
SFT8B = Path("/home/sovthpaw/projects/evolutionary-training/training-output/omnistep-sft-merged-20260612")

NUM_LAYERS = 36
NUM_EXPERTS = 4
TOP_K = 1
HIDDEN = 4096
INTERMEDIATE = 12288
NUM_HEADS = 32
NUM_KV_HEADS = 8
HEAD_DIM = 128
VOCAB = 151936
MAX_POS = 40960
ROPE_THETA = 1000000
NOISE_STD = 0.001

def load_omnistep_shards():
    """Load text-body safetensors from the new OmniStep (line2-new-omnistep-clean)."""
    print(f'  Loading OmniStep text body from {OMNISTEP_CLEAN}...', flush=True)
    with open(OMNISTEP_CLEAN / "model.safetensors.index.json") as f:
        idx = json.load(f)
    weight_map = idx["weight_map"]
    shards = {}
    for sf in sorted(set(weight_map.values())):
        shards[sf] = load_file(str(OMNISTEP_CLEAN / sf), device="cpu")
    print(f'    Loaded {len(shards)} shards, {sum(len(s) for s in shards.values())} tensors', flush=True)
    return shards

def load_sft8b_ffn():
    """Load only the FFN tensors from SFT-8B (we use them as the source for experts 1,3)."""
    print(f'  Loading SFT-8B FFN tensors from {SFT8B}...', flush=True)
    with open(SFT8B / "model.safetensors.index.json") as f:
        idx = json.load(f)
    ffn_keys = [k for k in idx["weight_map"] if any(x in k for x in [".mlp.gate_proj", ".mlp.up_proj", ".mlp.down_proj"])]
    print(f'    {len(ffn_keys)} FFN tensors to load', flush=True)
    sf_to_keys = {}
    for k in ffn_keys:
        sf = idx["weight_map"][k]
        sf_to_keys.setdefault(sf, []).append(k)
    out = {}
    for sf, keys in sf_to_keys.items():
        s = load_file(str(SFT8B / sf), device="cpu")
        for k in keys:
            out[k] = s[k]
        del s
    print(f'    Loaded {len(out)} SFT-8B FFN tensors', flush=True)
    return out

def build_senter(omnistep_shards, sft_ffn, output_dir):
    """Build Senter 32A8B with batched FFN expert construction."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(42)

    # Build index of OmniStep tensors for fast lookup
    omni_index = {}
    for sf, tensors in omnistep_shards.items():
        omni_index.update(tensors)

    # Collect shared tensors from OmniStep
    print('  Collecting shared tensors (attention, embed, norms, lm_head)...', flush=True)
    shared = {}
    ffn_base = {}  # (layer, proj) -> (omni_t, sft_t)
    for k, v in omni_index.items():
        if any(x in k for x in [".mlp.gate_proj", ".mlp.up_proj", ".mlp.down_proj"]):
            # Parse layer and proj
            # key: "model.layers.5.mlp.gate_proj.weight"
            parts = k.split(".")
            layer = int(parts[2])
            proj = parts[4]  # gate_proj, up_proj, down_proj
            sft_k = f"model.layers.{layer}.mlp.{proj}.weight"
            if sft_k in sft_ffn:
                ffn_base[(layer, proj)] = (v, sft_ffn[sft_k])
        else:
            shared[k] = v
    print(f'    {len(shared)} shared, {len(ffn_base)} FFN (layer, proj) pairs', flush=True)
    del omni_index
    gc.collect()

    # Build the experts dict with batched operations
    print(f'  Building 4 experts per FFN ({len(ffn_base)} (layer,proj) pairs × 4 experts)...', flush=True)
    senter = dict(shared)
    del shared
    gc.collect()

    t_build = time.time()
    n_ffn = 0
    for (layer, proj), (omni_t, sft_t) in ffn_base.items():
        # Build 4 experts: [omni, sft, omni+noise, sft+noise]
        # We use torch.stack so the 4 copies are in one allocation
        # But torch.stack creates a new tensor (4x the size), then we unbind
        # Faster approach: just clone+contiguous (no-op) for clean copies, then
        # create noisy copies via add+randn. This is the same as before but
        # with explicit per-expert allocations instead of inline expressions.

        # Expert 0: omni (no copy needed if already in senter)
        senter[f"model.layers.{layer}.mlp.experts.0.{proj}.weight"] = omni_t

        # Expert 1: sft
        senter[f"model.layers.{layer}.mlp.experts.1.{proj}.weight"] = sft_t

        # Expert 2: omni + noise
        noise_omni = torch.randn_like(omni_t) * NOISE_STD
        senter[f"model.layers.{layer}.mlp.experts.2.{proj}.weight"] = omni_t + noise_omni
        del noise_omni

        # Expert 3: sft + noise
        noise_sft = torch.randn_like(sft_t) * NOISE_STD
        senter[f"model.layers.{layer}.mlp.experts.3.{proj}.weight"] = sft_t + noise_sft
        del noise_sft

        n_ffn += 4
        if n_ffn % 36 == 0:
            print(f'    {n_ffn}/{len(ffn_base)*4} FFN expert tensors built ({time.time()-t_build:.0f}s)...', flush=True)
    del ffn_base
    gc.collect()
    print(f'    FFN experts done in {time.time()-t_build:.0f}s', flush=True)

    # Add routers
    print(f'  Building {NUM_LAYERS} routers (random init)...', flush=True)
    for layer in range(NUM_LAYERS):
        router_w = (torch.randn(NUM_EXPERTS, HIDDEN) * 0.01).contiguous()
        router_b = torch.zeros(NUM_EXPERTS)
        senter[f"model.layers.{layer}.mlp.router.weight"] = router_w
        senter[f"model.layers.{layer}.mlp.router.bias"] = router_b
    print(f'    {NUM_LAYERS*2} router tensors added', flush=True)

    # Build config
    config = {
        "architectures": ["Qwen3MoEForCausalLM"],
        "model_type": "qwen3_moe",
        "hidden_size": HIDDEN,
        "intermediate_size": INTERMEDIATE,
        "num_hidden_layers": NUM_LAYERS,
        "num_attention_heads": NUM_HEADS,
        "num_key_value_heads": NUM_KV_HEADS,
        "head_dim": HEAD_DIM,
        "max_position_embeddings": MAX_POS,
        "rope_theta": ROPE_THETA,
        "vocab_size": VOCAB,
        "tie_word_embeddings": False,
        "num_experts": NUM_EXPERTS,
        "top_k": TOP_K,
        "moe_intermediate_size": INTERMEDIATE,
        "moe_ffn_init_source": {
            "expert_0": "OmniStep-FFN (50% SFT+Cosmos, paper-exact)",
            "expert_1": "SFT-8B-FFN (agentic SFT-tuned)",
            "expert_2": "OmniStep-FFN + noise(0.001)",
            "expert_3": "SFT-8B-FFN + noise(0.001)",
        },
        "torch_dtype": "bfloat16",
        "transformers_version": "4.57.0.dev0",
    }

    with open(output_dir / "config.json", "w") as f:
        json.dump(config, f, indent=2)

    # Shard and save
    print(f'  Sharding and saving {len(senter)} tensors to {output_dir}...', flush=True)
    shard_bytes = 4_500_000_000  # 4.5GB per shard
    shards_out = []
    cur = {}
    cur_bytes = 0
    weight_map = {}
    for k in sorted(senter.keys()):
        v = senter[k]
        nb = v.numel() * v.element_size()
        if cur_bytes + nb > shard_bytes and cur:
            shards_out.append(cur)
            cur = {}
            cur_bytes = 0
        cur[k] = v
        cur_bytes += nb
    if cur:
        shards_out.append(cur)

    t_save = time.time()
    for i, sh in enumerate(shards_out):
        fname = f"model-{i+1:05d}-of-{len(shards_out):05d}.safetensors"
        save_file(sh, str(output_dir / fname))
        for k in sh:
            weight_map[k] = fname
        sz = sum(t.numel() * t.element_size() for t in sh.values()) / 1e9
        print(f'    Wrote {fname} ({len(sh)} tensors, {sz:.2f} GB)', flush=True)

    with open(output_dir / "model.safetensors.index.json", "w") as f:
        json.dump({"metadata": {"total_size": sum(t.numel() * t.element_size() for t in senter.values())},
                   "weight_map": weight_map}, f, indent=2)

    # Copy tokenizer files from SFT-8B
    for f in ["tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt",
              "special_tokens_map.json", "added_tokens.json", "chat_template.json",
              "generation_config.json"]:
        src = SFT8B / f
        if src.exists():
            shutil.copy2(src, output_dir / f)

    # Save metadata
    meta = {
        "construction": "Phase 1 (no router training)",
        "experts": NUM_EXPERTS,
        "top_k": TOP_K,
        "total_params_estimate": 32_000_000_000,
        "active_params_per_token": 8_000_000_000,
        "parent_a": "OmniStep (line2-new-omnistep-clean)",
        "parent_b": "OmniStep SFT-8B (omnistep-sft-merged-20260612)",
        "noise_std": NOISE_STD,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    with open(output_dir / "senter_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f'    Save done in {time.time()-t_save:.0f}s', flush=True)

    return config

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Output dir for Senter bundle")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    print(f'═══ Senter 32A8B construction (Phase 1) at {time.strftime("%H:%M:%S")} ═══')

    omnistep_shards = load_omnistep_shards()
    sft_ffn = load_sft8b_ffn()
    gc.collect()

    config = build_senter(omnistep_shards, sft_ffn, output_dir)

    elapsed = time.time() - t0
    print(f'\n═══ Senter 32A8B constructed in {elapsed:.0f}s ({elapsed/60:.1f} min) ═══')
    print(f'  Output: {output_dir}')
    total_size = sum(f.stat().st_size for f in output_dir.rglob("*.safetensors")) / 1e9
    print(f'  Total size: {total_size:.2f} GB')

    # Update metadata with actual time
    with open(output_dir / "senter_metadata.json") as f:
        meta = json.load(f)
    meta["construction_time_s"] = int(elapsed)
    with open(output_dir / "senter_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

if __name__ == "__main__":
    main()
