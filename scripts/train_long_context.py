#!/usr/bin/env python3
"""
Long-Context SFT Training — Phase 2 after YaRN 256K config.

Continues training with gradually increasing sequence lengths to teach
the model to use its newly extended 256K context window.

Usage:
  python3 train_long_context.py --model training-output/omnisenter-256k \\
      --adapter training-output/omnisenter-sft-XXX/ \\
      --output training-output/omnisenter-256k-sft \\
      --max-seq-len 8192 --steps 500
"""

import json, os, sys, time, argparse
from pathlib import Path
from datetime import datetime
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from trl import SFTTrainer, SFTConfig
from peft import PeftModel, LoraConfig, TaskType
from datasets import Dataset

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "training-data" / "prepared"
OUTPUT_DIR = BASE_DIR / "training-output"
LOGS_DIR = BASE_DIR / "logs"

# Same QLoRA + LoRA config as main training
BnB_CONFIG = BitsAndBytesConfig(
    load_in_4bit=True, bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True,
)

LORA_CONFIG = LoraConfig(
    r=64, lora_alpha=128, lora_dropout=0.05,
    target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
    task_type=TaskType.CAUSAL_LM,
)

def load_training_data(path: Path, max_examples: int = 10000):
    """Load a subset of training data for long-context pass."""
    data = []
    with open(path) as f:
        for i, line in enumerate(f):
            if i >= max_examples:
                break
            try:
                data.append(json.loads(line))
            except:
                pass
    return Dataset.from_list(data)

def format_conversation(conv):
    """Convert ShareGPT-style conversation to string."""
    messages = conv.get("conversations", conv.get("messages", []))
    text = ""
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        text += f"{role}: {content}\n\n"
    return text

def main():
    parser = argparse.ArgumentParser(description="Long-context SFT training (YaRN Phase 2)")
    parser.add_argument("--model", required=True, help="Path to YaRN-configured model")
    parser.add_argument("--adapter", default=None, help="Path to existing LoRA adapter to continue from")
    parser.add_argument("--output", default=None, help="Output directory")
    parser.add_argument("--max-seq-len", type=int, default=8192, help="Training sequence length")
    parser.add_argument("--steps", type=int, default=500, help="Number of training steps")
    parser.add_argument("--batch-size", type=int, default=1, help="Per-device batch size")
    parser.add_argument("--gradient-accum", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--lr", type=float, default=5e-5, help="Learning rate")
    parser.add_argument("--max-examples", type=int, default=10000, help="Max training examples")
    parser.add_argument("--verbose", action="store_true")
    
    args = parser.parse_args()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"omnisenter-256k-sft-{timestamp}"
    
    print(f"\n{'='*60}")
    print(f"LONG-CONTEXT SFT TRAINING (YaRN Phase 2)")
    print(f"{'='*60}")
    print(f"  Model: {args.model}")
    print(f"  Adapter: {args.adapter or 'new LoRA'}")
    print(f"  Max seq len: {args.max_seq_len}")
    print(f"  Steps: {args.steps}")
    print(f"  Batch: {args.batch_size} × {args.gradient_accum}")
    print(f"  LR: {args.lr}")
    print(f"  Run: {run_name}")
    print()
    
    # Load tokenizer
    print("[1/5] Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load base model in 4-bit
    print("[2/5] Loading base model (4-bit QLoRA)...")
    base_model = AutoModelForCausalLM.from_pretrained(
        args.model, device_map="auto", quantization_config=BnB_CONFIG,
        dtype=torch.bfloat16,
    )
    
    # Load adapter if continuing
    if args.adapter:
        print(f"  Loading adapter from {args.adapter}...")
        model = PeftModel.from_pretrained(base_model, args.adapter, is_trainable=True)
    else:
        from peft import get_peft_model
        model = get_peft_model(base_model, LORA_CONFIG)
    
    # Load data
    print("[3/5] Loading training data...")
    raw_data = load_training_data(DATA_DIR / "unified_sft.jsonl", args.max_examples)
    print(f"  Loaded {len(raw_data)} conversations")
    
    # Format data
    print("[4/5] Formatting data...")
    formatted = raw_data.map(lambda x: {"text": format_conversation(x)})
    formatted = formatted.select_columns(["text"])
    print(f"  Formatted {len(formatted)} examples")
    
    # Training args — fewer steps, longer seqs
    output_dir = args.output or str(OUTPUT_DIR / run_name)
    logging_dir = str(OUTPUT_DIR / "logs")
    
    training_args = SFTConfig(
        output_dir=output_dir,
        max_steps=args.steps,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accum,
        learning_rate=args.lr,
        weight_decay=0.01,
        warmup_ratio=0.03,
        max_length=args.max_seq_len,
        packing=False,
        logging_steps=10,
        save_steps=100,
        save_total_limit=3,
        bf16=True,
        logging_dir=logging_dir,
        report_to="none",
        optim="paged_adamw_8bit",
        lr_scheduler_type="cosine",
        ddp_find_unused_parameters=False,
        remove_unused_columns=False,
        seed=42,
        run_name=run_name,
    )
    
    # Setup trainer
    print("[5/5] Setting up trainer...")
    trainer = SFTTrainer(
        model=model, processing_class=tokenizer,
        train_dataset=formatted, peft_config=LORA_CONFIG if not args.adapter else None,
        args=training_args,
    )
    
    # Train
    print(f"\n{'='*60}")
    print(f"STARTING LONG-CONTEXT TRAINING")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    trainer.train()
    train_time = time.time() - start_time
    
    # Save
    print(f"\n{'='*60}")
    print(f"TRAINING COMPLETE")
    print(f"{'='*60}")
    print(f"  Time: {train_time:.0f}s ({train_time/3600:.1f}h)")
    print(f"  Output: {output_dir}")
    
    trainer.save_model(output_dir)
    
    # Log
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOGS_DIR / "long_context_log.jsonl", "a") as f:
        f.write(json.dumps({
            "run": run_name, "model": args.model, "adapter": args.adapter,
            "steps": args.steps, "max_seq_len": args.max_seq_len,
            "train_time": train_time, "timestamp": timestamp,
        }) + "\n")
    
    print(f"\nNext: python3 scripts/merge_lora.py --base {args.model} --adapter {output_dir} --output training-output/omnisenter-256k-merged")

if __name__ == "__main__":
    main()
