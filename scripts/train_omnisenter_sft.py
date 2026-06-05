#!/usr/bin/env python3
"""
SFT Training Pipeline for OmniSenter Base 16B

Fine-tunes the base model on 34,142 conversations using QLoRA (4-bit) to fit on 24GB VRAM.
Training config: 2 GPUs × 24GB, batch_size=2, gradient_accum=8, max_seq_len=4096

Usage:
  python3 train_omnisenter_sft.py [--epochs 2] [--batch-size 2] [--lr 1e-4]
"""

import json, os, sys, time
from pathlib import Path
from datetime import datetime
import torch
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    DataCollatorForSeq2Seq,
)
from trl import SFTTrainer
from peft import LoraConfig, TaskType
from datasets import Dataset

# Config
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "training-data" / "prepared"
OUTPUT_DIR = BASE_DIR / "training-output"
LOGS_DIR = BASE_DIR / "logs"

# Model path (use local gen-0 or HF)
MODEL_PATH = os.environ.get(
    "MODEL_PATH", 
    "sovthpaw/OmniSenter-Base-16B"
)

# QLoRA config
BnB_CONFIG = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

# LoRA config
LORA_CONFIG = LoraConfig(
    r=64,
    lora_alpha=128,
    lora_dropout=0.05,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    task_type=TaskType.CAUSAL_LM,
)

def load_training_data(path):
    """Load unified SFT data as ShareGPT conversations."""
    data = []
    with open(path) as f:
        for line in f:
            try:
                conv = json.loads(line)
                data.append(conv)
            except Exception as e:
                print(f"Warning: Failed to parse line: {e}")
    return Dataset.from_list(data)

def format_conversation(conv):
    """Convert ShareGPT-style conversation to string."""
    if "conversations" in conv:
        messages = conv["conversations"]
    elif "messages" in conv:
        messages = conv["messages"]
    else:
        return ""
    
    # Simple formatting - can be customized
    text = ""
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        text += f"{role}: {content}\n\n"
    return text

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Train OmniSenter on SFT data")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--max-seq-len", type=int, default=4096)
    parser.add_argument("--gradient-accum", type=int, default=8)
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--warmup-ratio", type=float, default=0.03)
    parser.add_argument("--logging-dir", type=str, default=None)
    args = parser.parse_args()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"omnisenter-sft-{timestamp}"
    
    print(f"\n{'='*60}")
    print(f"OMNISENTER SFT TRAINING")
    print(f"{'='*60}")
    print(f"  Model: {MODEL_PATH}")
    print(f"  Data: {DATA_DIR}/unified_sft.jsonl")
    print(f"  Epochs: {args.epochs}")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Gradient accum: {args.gradient_accum}")
    print(f"  Max seq len: {args.max_seq_len}")
    print(f"  Run: {run_name}")
    print()
    
    # Load model
    print("[1/5] Loading model (4-bit QLoRA)...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        device_map="auto",
        quantization_config=BnB_CONFIG,
        torch_dtype=torch.bfloat16,
    )
    
    # Load tokenizer
    print("[2/5] Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Load training data
    print("[3/5] Loading training data...")
    raw_data = load_training_data(DATA_DIR / "unified_sft.jsonl")
    print(f"  Loaded {len(raw_data)} conversations")
    
    # Format data
    print("[4/5] Formatting data...")
    formatted_data = raw_data.map(lambda x: {"text": format_conversation(x)})
    formatted_data = formatted_data.select_columns(["text"])
    print(f"  Formatted {len(formatted_data)} examples")
    
    # Training arguments
    output_dir = args.output_dir or str(OUTPUT_DIR / run_name)
    logging_dir = args.logging_dir or str(OUTPUT_DIR / "logs")
    
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accum,
        learning_rate=args.lr,
        weight_decay=0.01,
        warmup_ratio=args.warmup_ratio,
        max_steps=-1,  # Use epochs instead
        logging_steps=50,
        save_steps=500,
        save_total_limit=3,
        fp16=False,
        bf16=True,
        logging_dir=logging_dir,
        report_to="none",  # No wandb by default
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
        model=model,
        tokenizer=tokenizer,
        train_dataset=formatted_data,
        peft_config=LORA_CONFIG,
        dataset_text_field="text",
        max_seq_length=args.max_seq_len,
        args=training_args,
        packing=False,
        data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, padding=True),
    )
    
    # Log config
    config = {
        "model": MODEL_PATH,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "gradient_accum": args.gradient_accum,
        "lr": args.lr,
        "max_seq_len": args.max_seq_len,
        "lora_r": 64,
        "lora_alpha": 128,
        "timestamp": timestamp,
    }
    
    with open(f"{output_dir}/training_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    # Train!
    print(f"\n{'='*60}")
    print(f"STARTING TRAINING")
    print(f"{'='*60}")
    
    start_time = time.time()
    trainer.train()
    train_time = time.time() - start_time
    
    # Save adapter
    print(f"\n{'='*60}")
    print(f"TRAINING COMPLETE")
    print(f"{'='*60}")
    print(f"  Time: {train_time:.0f}s ({train_time/3600:.1f}h)")
    print(f"  Output: {output_dir}")
    
    trainer.save_model(output_dir)
    
    # Log completion
    log_entry = {
        "run": run_name,
        "model": MODEL_PATH,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "learning_rate": args.lr,
        "train_time": train_time,
        "timestamp": timestamp,
    }
    
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOGS_DIR / "training_log.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    print(f"\nNext steps:")
    print(f"  1. Evaluate: python3 darwin_benchmark.py --model {output_dir}")
    print(f"  2. Upload to HF: huggingface-cli upload sovthpaw/omnisenter-train-gen0 {output_dir}")

if __name__ == "__main__":
    main()
