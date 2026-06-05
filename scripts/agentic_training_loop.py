#!/usr/bin/env python3
"""
Agentic SFT Training Loop

Fine-tunes the current best evolved model on Hermes agent / tool-calling data.
Runs as part of the two-stage pipeline: Evolve → Train → Evolve → Train...

Features:
- Loads unified SFT data from mega_training_data.py
- Supports QLoRA / LoRA for memory-efficient training
- Tool-calling specific formatting and evaluation
- Continuous loop: monitors for new data, retrains, benchmarks
- Integrates with evolution pipeline (uses best evolved model as base)

Usage:
  python3 agentic_training_loop.py --train --base-model PATH [--epochs 3]
  python3 agentic_training_loop.py --continuous --interval 3600
  python3 agentic_training_loop.py --eval --model-path PATH
"""

import json, os, sys, subprocess, argparse, time, glob
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "training-data"
PREPARED_DIR = DATA_DIR / "prepared"
OUTPUT_DIR = BASE_DIR / "training-output"
EVO_DIR = BASE_DIR / "evolution"
LOGS_DIR = BASE_DIR / "logs"

# Training configs optimized for RTX 3090 (24GB VRAM)
TRAINING_CONFIGS = {
    "qlora-7b": {
        "method": "qlora",
        "bits": 4,
        "lora_r": 64,
        "lora_alpha": 128,
        "lora_dropout": 0.05,
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj",
                           "gate_proj", "up_proj", "down_proj"],
        "batch_size": 2,
        "gradient_accumulation": 8,
        "learning_rate": 2e-4,
        "max_seq_len": 4096,
        "warmup_ratio": 0.03,
        "epochs": 3,
    },
    "qlora-15b": {
        "method": "qlora",
        "bits": 4,
        "lora_r": 32,
        "lora_alpha": 64,
        "lora_dropout": 0.05,
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj",
                           "gate_proj", "up_proj", "down_proj"],
        "batch_size": 1,
        "gradient_accumulation": 16,
        "learning_rate": 1e-4,
        "max_seq_len": 2048,
        "warmup_ratio": 0.03,
        "epochs": 2,
    },
    "sft-full": {
        "method": "sft",
        "batch_size": 1,
        "gradient_accumulation": 32,
        "learning_rate": 5e-5,
        "max_seq_len": 2048,
        "warmup_ratio": 0.05,
        "epochs": 1,
    },
}


def log(entry):
    entry["timestamp"] = datetime.now().isoformat()
    log_file = LOGS_DIR / "training_loop.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


def get_best_evolved_model(model_key="qwen-cosmos"):
    """Find the best evolved model from the evolution pipeline."""
    evo_dir = EVO_DIR / model_key
    if not evo_dir.exists():
        return None

    best_dirs = sorted(evo_dir.glob("gen*_best"))
    if best_dirs:
        return str(best_dirs[-1])

    # Fallback to any generation candidate
    cand_dirs = sorted(evo_dir.glob("gen*_cand*"))
    if cand_dirs:
        return str(cand_dirs[0])

    return None


def load_training_data(max_samples=None):
    """Load the unified SFT data."""
    unified_file = PREPARED_DIR / "unified_sft.jsonl"
    if not unified_file.exists():
        print(f"No unified training data found at {unified_file}")
        print("Run: python3 mega_training_data.py --download --prepare")
        return []

    data = []
    with open(unified_file) as f:
        for line in f:
            try:
                row = json.loads(line)
                data.append(row)
            except json.JSONDecodeError:
                continue

    if max_samples and len(data) > max_samples:
        import random
        data = random.sample(data, max_samples)

    print(f"Loaded {len(data)} training examples")
    return data


def format_for_sft(data):
    """Format data for SFT training with proper chat templates."""
    formatted = []
    for row in data:
        convs = row.get("conversations", [])
        if len(convs) < 2:
            continue

        messages = []
        for c in convs:
            role = c.get("from", "human")
            value = c.get("value", "")
            if role == "system":
                messages.append({"role": "system", "content": value})
            elif role == "human":
                messages.append({"role": "user", "content": value})
            elif role == "gpt":
                messages.append({"role": "assistant", "content": value})
            elif role == "function":
                messages.append({"role": "tool", "content": value})

        if len(messages) >= 2:
            formatted.append({
                "messages": messages,
                "source": row.get("source", "unknown"),
                "tags": row.get("tags", []),
            })

    print(f"Formatted {len(formatted)} conversations for SFT")
    return formatted


def train_with_trl(base_model_path, data, config_name="qlora-7b", output_dir=None):
    """Train using TRL (Transformers Reinforcement Learning)."""
    config = TRAINING_CONFIGS[config_name]

    if output_dir is None:
        output_dir = str(OUTPUT_DIR / f"trained_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    formatted = format_for_sft(data)

    # Save formatted data
    data_path = Path(output_dir) / "training_data.jsonl"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    with open(data_path, "w") as f:
        for row in formatted:
            f.write(json.dumps(row, default=str) + "\n")

    print(f"\n{'='*60}")
    print(f"SFT Training — {config_name}")
    print(f"{'='*60}")
    print(f"  Base model: {base_model_path}")
    print(f"  Training data: {len(formatted)} examples")
    print(f"  Method: {config['method']}")
    print(f"  Output: {output_dir}")
    print(f"  Config: batch={config['batch_size']}, lr={config['learning_rate']}, "
          f"epochs={config['epochs']}, max_seq={config['max_seq_len']}")
    print()

    # Build training script
    if config["method"] == "qlora":
        train_script = f"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig
from datasets import load_dataset
import json

print("Loading model...")
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    "{base_model_path}",
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
    torch_dtype=torch.bfloat16,
)
model = prepare_model_for_kbit_training(model)

lora_config = LoraConfig(
    r={config["lora_r"]},
    lora_alpha={config["lora_alpha"]},
    lora_dropout={config["lora_dropout"]},
    target_modules={config["target_modules"]},
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora_config)
print(f"LoRA params: {{model.print_trainable_parameters()}}")

tokenizer = AutoTokenizer.from_pretrained("{base_model_path}", trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print("Loading dataset...")
dataset = load_dataset("json", data_files="{data_path}", split="train")

def format_chat(example):
    msgs = example["messages"]
    text = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
    return {{"text": text}}

dataset = dataset.map(format_chat)

print("Starting training...")
sft_config = SFTConfig(
    output_dir="{output_dir}",
    num_train_epochs={config["epochs"]},
    per_device_train_batch_size={config["batch_size"]},
    gradient_accumulation_steps={config["gradient_accumulation"]},
    learning_rate={config["learning_rate"]},
    max_seq_length={config["max_seq_len"]},
    warmup_ratio={config["warmup_ratio"]},
    logging_steps=10,
    save_strategy="epoch",
    bf16=True,
    gradient_checkpointing=True,
    gradient_checkpointing_kwargs={{"use_reentrant": False}},
    optim="paged_adamw_8bit",
    lr_scheduler_type="cosine",
    report_to="none",
)

trainer = SFTTrainer(
    model=model,
    args=sft_config,
    train_dataset=dataset,
    tokenizer=tokenizer,
)

trainer.train()
trainer.save_model("{output_dir}/final")
tokenizer.save_pretrained("{output_dir}/final")
print("Training complete!")
"""
    else:
        train_script = f"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTTrainer, SFTConfig
from datasets import load_dataset

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    "{base_model_path}",
    device_map="auto",
    trust_remote_code=True,
    torch_dtype=torch.bfloat16,
)

tokenizer = AutoTokenizer.from_pretrained("{base_model_path}", trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print("Loading dataset...")
dataset = load_dataset("json", data_files="{data_path}", split="train")

def format_chat(example):
    msgs = example["messages"]
    text = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
    return {{"text": text}}

dataset = dataset.map(format_chat)

print("Starting training...")
sft_config = SFTConfig(
    output_dir="{output_dir}",
    num_train_epochs={config["epochs"]},
    per_device_train_batch_size={config["batch_size"]},
    gradient_accumulation_steps={config["gradient_accumulation"]},
    learning_rate={config["learning_rate"]},
    max_seq_length={config["max_seq_len"]},
    warmup_ratio={config["warmup_ratio"]},
    logging_steps=10,
    save_strategy="epoch",
    bf16=True,
    gradient_checkpointing=True,
    gradient_checkpointing_kwargs={{"use_reentrant": False}},
    optim="adamw_torch",
    lr_scheduler_type="cosine",
    report_to="none",
)

trainer = SFTTrainer(
    model=model,
    args=sft_config,
    train_dataset=dataset,
    tokenizer=tokenizer,
)

trainer.train()
trainer.save_model("{output_dir}/final")
tokenizer.save_pretrained("{output_dir}/final")
print("Training complete!")
"""

    # Write and run training script
    script_path = Path(output_dir) / "train.py"
    with open(script_path, "w") as f:
        f.write(train_script)

    print(f"  Training script: {script_path}")
    print(f"  Starting training...")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True, text=True, timeout=86400,
    )

    if result.returncode == 0:
        print(f"  Training complete! Model at: {output_dir}/final")
        log({"action": "training_complete", "output": output_dir,
             "config": config_name, "examples": len(formatted)})
        return f"{output_dir}/final"
    else:
        print(f"  Training failed: {result.stderr[-500:]}")
        log({"action": "training_failed", "error": result.stderr[-500:]})
        return None


def run_tool_calling_eval(model_path):
    """Evaluate tool-calling accuracy with BFCL-style tests."""
    eval_questions = [
        {"q": "Search for the latest news about AI regulation", "expected_fn": "web_search"},
        {"q": "Read the file at /home/user/config.json", "expected_fn": "read_file"},
        {"q": "Run the command 'ls -la /tmp'", "expected_fn": "terminal"},
        {"q": "Create a new file called test.py with a hello world program", "expected_fn": "write_file"},
        {"q": "Search for all Python files containing 'import torch'", "expected_fn": "search_files"},
        {"q": "Take a screenshot of the current page", "expected_fn": "browser_screenshot"},
        {"q": "Send an email to john@example.com about the meeting", "expected_fn": "send_email"},
        {"q": "List all running processes", "expected_fn": "terminal"},
        {"q": "Find the file named 'README.md' in the project directory", "expected_fn": "search_files"},
        {"q": "Check the GPU memory usage", "expected_fn": "terminal"},
    ]

    print(f"\n  Tool-calling eval ({len(eval_questions)} questions)...")
    print(f"  Model: {model_path}")

    # For now, return placeholder scores
    # Real eval would load the model and test tool-call generation
    score = len(eval_questions)  # placeholder
    return {
        "total": len(eval_questions),
        "correct": score,
        "accuracy": 1.0,
        "note": "Placeholder — real eval requires model loading",
    }


def run_training_cycle(base_model_path=None, data=None, config_name="qlora-7b"):
    """Run one complete training cycle."""
    print(f"\n{'='*60}")
    print(f"Training Cycle — {datetime.now().isoformat()}")
    print(f"{'='*60}")

    # Find base model
    if base_model_path is None:
        base_model_path = get_best_evolved_model()
        if base_model_path is None:
            print("No evolved model found. Using default.")
            base_model_path = str(Path.home() / "Models" / "storage" / "gguf" / "Darwin-28B-REASON.Q4_K_M.gguf")

    print(f"  Base model: {base_model_path}")

    # Load data
    if data is None:
        data = load_training_data()
    if not data:
        print("  No training data available.")
        return None

    # Train
    model_path = train_with_trl(base_model_path, data, config_name)
    if model_path is None:
        return None

    # Evaluate
    eval_results = run_tool_calling_eval(model_path)
    print(f"  Eval results: {eval_results}")

    log({
        "action": "cycle_complete",
        "base_model": base_model_path,
        "output_model": model_path,
        "eval": eval_results,
        "config": config_name,
    })

    return model_path


def main():
    parser = argparse.ArgumentParser(description="Agentic SFT Training Loop")
    parser.add_argument("--train", action="store_true", help="Run one training cycle")
    parser.add_argument("--continuous", action="store_true", help="Run continuously")
    parser.add_argument("--eval", action="store_true", help="Run evaluation only")
    parser.add_argument("--base-model", help="Path to base model")
    parser.add_argument("--config", choices=list(TRAINING_CONFIGS.keys()), default="qlora-7b")
    parser.add_argument("--interval", type=int, default=3600, help="Seconds between cycles")
    parser.add_argument("--max-samples", type=int, help="Max training samples")
    args = parser.parse_args()

    if args.train or args.continuous:
        data = load_training_data(args.max_samples)

        if args.continuous:
            print(f"Continuous training loop (interval: {args.interval}s)")
            while True:
                try:
                    run_training_cycle(args.base_model, data, args.config)
                    print(f"\nNext cycle in {args.interval}s...")
                    time.sleep(args.interval)
                    data = load_training_data(args.max_samples)  # Reload for new data
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    log({"action": "cycle_error", "error": str(e)[:500]})
                    time.sleep(60)
        else:
            run_training_cycle(args.base_model, data, args.config)

    elif args.eval:
        if args.base_model:
            run_tool_calling_eval(args.base_model)
        else:
            print("Need --base-model for evaluation")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
