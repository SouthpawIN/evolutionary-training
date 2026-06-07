#!/usr/bin/env python3
"""
Merge LoRA adapter back into base model for a single deployable artifact.

After SFT + YaRN + long-context training, the LoRA adapter contains all the
fine-tuned weights. This script merges them into the base model and saves
a standalone model ready for inference.

Usage:
  python3 merge_lora.py --base training-output/omnisenter-256k \\
      --adapter training-output/omnisenter-256k-sft-XXX/ \\
      --output training-output/omnisenter-256k-merged
"""

import argparse, json, shutil
from pathlib import Path
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

def merge_lora(base_path: Path, adapter_path: Path, output_path: Path, push_to_hf: str = None):
    """Merge LoRA adapter into base model and save."""
    
    print(f"LoRA Merge Tool")
    print(f"  Base: {base_path}")
    print(f"  Adapter: {adapter_path}")
    print(f"  Output: {output_path}")
    print()
    
    # Load base model
    print("[1/3] Loading base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        base_path, torch_dtype=torch.bfloat16, device_map="auto",
    )
    tokenizer = AutoTokenizer.from_pretrained(base_path)
    print(f"  Base params: {sum(p.numel() for p in base_model.parameters()):,}")
    
    # Load and merge adapter
    print("[2/3] Loading and merging adapter...")
    model = PeftModel.from_pretrained(base_model, adapter_path)
    model = model.merge_and_unload()
    print(f"  Merged params: {sum(p.numel() for p in model.parameters()):,}")
    
    # Save merged model
    print("[3/3] Saving merged model...")
    output_path.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_path, safe_serialization=True)
    tokenizer.save_pretrained(output_path)
    
    # Copy config files
    for fname in ["generation_config.json", "chat_template.json", "merge_metadata.json"]:
        src = base_path / fname
        if src.exists():
            shutil.copy2(src, output_path / fname)
    
    size_gb = sum(f.stat().st_size for f in output_path.iterdir() if f.is_file()) / 1e9
    print(f"\n  ✅ Merged model saved: {output_path}")
    print(f"  ✅ Size: {size_gb:.1f} GB")
    print(f"  ✅ Ready for inference at 256K context with turbo4 KV cache")
    
    # Push to HF if requested
    if push_to_hf:
        print(f"\n  Uploading to {push_to_hf}...")
        import subprocess
        subprocess.run([
            "huggingface-cli", "upload", push_to_hf, str(output_path),
            "--repo-type", "model",
            "--commit-message", "OmniSenter 256K — YaRN-extended, LoRA-merged, turbo4 KV cache"
        ], check=True)
        print(f"  ✅ Pushed to {push_to_hf}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge LoRA adapter into base model")
    parser.add_argument("--base", required=True, help="Path to base model")
    parser.add_argument("--adapter", required=True, help="Path to LoRA adapter")
    parser.add_argument("--output", required=True, help="Output path for merged model")
    parser.add_argument("--push-to-hf", default=None, help="HF repo to push to (e.g. sovthpaw/omnisenter-256k)")
    
    args = parser.parse_args()
    merge_lora(Path(args.base), Path(args.adapter), Path(args.output), args.push_to_hf)
