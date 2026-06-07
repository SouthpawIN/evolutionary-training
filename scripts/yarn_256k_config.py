#!/usr/bin/env python3
"""
Apply YaRN RoPE scaling to extend model context from 40K → 256K.

YaRN (Yet another RoPE extensioN) mathematically stretches position embeddings.
Factor = target_context / original_context = 256000 / 40960 = 6.25x.

Usage:
  python3 yarn_256k_config.py --model training-output/<run>/checkpoint-XXX --output training-output/omnisenter-256k
"""

import json, shutil, argparse
from pathlib import Path

def apply_yarn(model_path: Path, output_path: Path, target_ctx: int = 256000, 
               original_ctx: int = 40960, dry_run: bool = False):
    """Apply YaRN scaling config to a trained model checkpoint."""
    
    factor = target_ctx / original_ctx
    
    print(f"YaRN 256K Configurator")
    print(f"  Source: {model_path}")
    print(f"  Target context: {target_ctx:,} tokens")
    print(f"  Original context: {original_ctx:,} tokens")
    print(f"  Scale factor: {factor:.3f}x")
    print()
    
    # Load config
    config_path = model_path / "config.json"
    with open(config_path) as f:
        config = json.load(f)
    
    print(f"  Architecture: {config.get('architectures', ['unknown'])[0]}")
    print(f"  Current max_position_embeddings: {config.get('max_position_embeddings', 'unknown')}")
    
    # Apply YaRN scaling
    config["rope_scaling"] = {
        "type": "yarn",
        "factor": factor,
        "original_max_position_embeddings": original_ctx,
        "attention_factor": 1.0,
        "beta_fast": 32,
        "beta_slow": 1,
        "mscale": 1.0,
        "mscale_all_dim": 1.0,
    }
    
    # Update max position embeddings to target
    config["max_position_embeddings"] = target_ctx
    
    if dry_run:
        print(f"\n  [DRY RUN] Would write config with:")
        print(f"  rope_scaling: {json.dumps(config['rope_scaling'], indent=4)}")
        return
    
    # Create output
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save new config
    with open(output_path / "config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    # Copy all other files
    for item in model_path.iterdir():
        if item.name == "config.json":
            continue  # Already written
        dest = output_path / item.name
        if item.is_dir():
            if not dry_run:
                shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)
    
    print(f"\n  ✅ YaRN config applied: {factor:.3f}x scale")
    print(f"  ✅ Model saved to: {output_path}")
    print(f"  ✅ Context extended: {original_ctx:,} → {target_ctx:,} tokens")
    print()
    print(f"  KV cache estimate at {target_ctx//1000}K with turbo4:")
    vram_kv = 36 * 32 * 128 * 2 * target_ctx * 2 / 8  # raw bf16 size / 8x turbo4 compression
    print(f"    ~{vram_kv / 1e9:.1f} GB (turbo4 @ ~8x compression)")
    print()
    print(f"  Next: Run long-context SFT phase with --max-seq-len 8192")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply YaRN scaling to extend context")
    parser.add_argument("--model", required=True, help="Path to trained model checkpoint")
    parser.add_argument("--output", required=True, help="Output path for YaRN-configured model")
    parser.add_argument("--target-ctx", type=int, default=256000, help="Target context length")
    parser.add_argument("--original-ctx", type=int, default=40960, help="Original max_position_embeddings")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without writing")
    
    args = parser.parse_args()
    apply_yarn(Path(args.model), Path(args.output), args.target_ctx, args.original_ctx, args.dry_run)
