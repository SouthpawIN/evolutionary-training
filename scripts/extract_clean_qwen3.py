#!/usr/bin/env python3
"""Extract clean Qwen3-compatible weights from gen-0 multimodal model."""
import json, shutil
from pathlib import Path
from safetensors.torch import load_file, save_file

GEN0 = Path("/home/sovthpaw/projects/evolutionary-training/evolution/gen-0")
CLEAN = Path("/home/sovthpaw/projects/evolutionary-training/evolution/gen-0-clean")
for f in CLEAN.iterdir() if CLEAN.exists() else []:
    f.unlink()
CLEAN.mkdir(parents=True, exist_ok=True)

with open(GEN0 / "model.safetensors.index.json") as f:
    index = json.load(f)

EXCLUDE = ["moe_gen", "add_k_proj", "add_q_proj", "add_v_proj", "to_add_out",
           "norm_added_k", "norm_added_q", "action_modality_embed", "audio_modality_embed"]

# Group by shard file, tracking (old_name, new_name)
by_file = {}
for old_name, filename in index["weight_map"].items():
    if any(m in old_name for m in EXCLUDE):
        continue
    # lm_head is NOT under model. prefix (tied embeddings)
    if old_name in ("lm_head.weight",):
        new_name = old_name
    else:
        new_name = "model." + old_name
    by_file.setdefault(filename, []).append((old_name, new_name))

print(f"Keeping {sum(len(v) for v in by_file.values())} / {len(index['weight_map'])} weights")

new_index = {"metadata": {"total_size": 0}, "weight_map": {}}
total_params = 0

for filename in sorted(by_file):
    pairs = by_file[filename]
    shard = load_file(str(GEN0 / filename))
    clean_shard = {}
    for old_name, new_name in pairs:
        clean_shard[new_name] = shard[old_name]
        total_params += shard[old_name].numel()
    
    save_file(clean_shard, str(CLEAN / filename))
    for _, new_name in pairs:
        new_index["weight_map"][new_name] = filename
    print(f"  {filename}: {len(pairs)} weights")

with open(CLEAN / "model.safetensors.index.json", "w") as f:
    json.dump(new_index, f, indent=2)

for fname in ["config.json", "tokenizer.json", "tokenizer_config.json",
              "generation_config.json", "merges.txt", "chat_template.json"]:
    src = GEN0 / fname
    if src.exists():
        shutil.copy2(src, CLEAN / fname)

print(f"\nDone! {total_params:,} params (~{total_params*2/1e9:.1f}B bf16)")
print(f"Size: {sum(f.stat().st_size for f in CLEAN.iterdir() if f.is_file())/1e9:.1f} GB")
