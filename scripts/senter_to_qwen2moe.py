#!/usr/bin/env python3
"""Convert Senter's custom Qwen3MoE to llama.cpp-compatible Qwen2MoE format.

Removes router.bias tensors (llama.cpp doesn't support them).
Rewrites config.json to claim qwen2_moe arch.
"""
import json, shutil, sys
from pathlib import Path
from safetensors.torch import load_file, save_file

SRC = Path("/home/sovthpaw/projects/evolutionary-training/training-output/senter-ohm-32a8b")
DST = Path("/home/sovthpaw/projects/evolutionary-training/training-output/senter-ohm-32a8b-qwen2moe")

if DST.exists():
    for f in DST.iterdir():
        if f.is_symlink() or f.is_file():
            f.unlink()
        elif f.is_dir():
            shutil.rmtree(f)
DST.mkdir(parents=True, exist_ok=True)

print(f"Converting {SRC} -> {DST}")

# Load index
with open(SRC / "model.safetensors.index.json") as f:
    idx = json.load(f)

weight_map = idx["weight_map"]
print(f"  Source has {len(weight_map)} tensors across {len(set(weight_map.values()))} shards")

# Filter out router biases + rewrite weight_map
new_map = {}
router_biases = [k for k in weight_map if "router.bias" in k]
print(f"  Stripping {len(router_biases)} router.bias tensors")
for k, fname in weight_map.items():
    if "router.bias" not in k:
        new_map[k] = fname

# Process each shard
shards_seen = set()
for new_k, fname in new_map.items():
    if fname in shards_seen:
        continue
    shards_seen.add(fname)
    src_path = SRC / fname
    print(f"  Processing {fname}...", flush=True)
    shard = load_file(str(src_path))
    # Filter out router biases + copy
    clean_shard = {k: v for k, v in shard.items() if "router.bias" not in k}
    save_file(clean_shard, str(DST / fname))
    print(f"    {len(shard)} -> {len(clean_shard)} tensors")
    del shard

# Write new index
with open(DST / "model.safetensors.index.json", "w") as f:
    json.dump({"metadata": {"total_size": 0}, "weight_map": new_map}, f, indent=2)
print(f"  Total tensors kept: {len(new_map)}")

# Write Qwen2MoE-compatible config
config = {
    "architectures": ["Qwen2MoeForCausalLM"],
    "model_type": "qwen2_moe",
    "hidden_size": 4096,
    "intermediate_size": 12288,  # per expert FFN
    "num_hidden_layers": 36,
    "num_attention_heads": 32,
    "num_key_value_heads": 8,
    "max_position_embeddings": 40960,
    "rope_theta": 1000000,
    "head_dim": 128,
    "vocab_size": 151936,
    "tie_word_embeddings": False,
    "num_experts": 4,
    "num_experts_per_tok": 1,
    "decoder_sparse_step": 1,
    "moe_intermediate_size": 12288,
    "use_cache": True,
    "bos_token_id": 1,
    "eos_token_id": 151643,
    "pad_token_id": 151643,
    "torch_dtype": "bfloat16",
    "sliding_window": None,
}
with open(DST / "config.json", "w") as f:
    json.dump(config, f, indent=2)

# Copy tokenizer files
for fname in ["tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt",
              "special_tokens_map.json", "added_tokens.json", "chat_template.json",
              "generation_config.json"]:
    src = SRC / fname
    if src.exists():
        shutil.copy2(src, DST / fname)

# Also copy safetensors shards by symlink for HF loading (convert_hf_to_gguf reads from index)
# Actually convert_hf_to_gguf.py just reads the safetensors referenced by index

print(f"\n✓ Conversion done: {DST}")
print(f"  {len(new_map)} tensors in {len(shards_seen)} shards")
print(f"  Config: Qwen2MoeForCausalLM, 4 experts, top-1")
