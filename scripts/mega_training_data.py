#!/usr/bin/env python3
"""
Mega Agentic Training Data Pipeline

Downloads, processes, and formats ALL available Hermes agent / tool-calling /
agentic training data from HuggingFace and local sources.

Produces a unified ShareGPT-format JSONL for SFT training.

Usage:
  python3 mega_training_data.py --download --prepare [--sample] [--tier 1]
"""

import json, os, sys, subprocess, argparse, time
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "training-data"
DOWNLOAD_DIR = DATA_DIR / "raw"
PREPARED_DIR = DATA_DIR / "prepared"
LOG_FILE = BASE_DIR / "logs" / "data_pipeline.jsonl"

# === TIER 1: CRITICAL — Hermes Agent & Tool Calling ===
TIER1 = {
    "hermes-reasoning-tool-use": {
        "repo": "interstellarninja/hermes_reasoning_tool_use",
        "priority": 1, "tags": ["agent", "tool-use", "reasoning", "hermes"],
        "desc": "51K tool-calling conversations",
    },
    "hermes-agent-traces": {
        "repo": "lambda/hermes-agent-reasoning-traces",
        "priority": 1, "tags": ["agent", "traces", "hermes"],
        "desc": "Real Hermes agent multi-turn trajectories",
    },
    "hermes-agent-traces-filtered": {
        "repo": "DJLougen/hermes-agent-traces-filtered",
        "priority": 1, "tags": ["agent", "traces", "hermes", "filtered"],
        "desc": "Filtered hermes agent traces",
    },
    "hermes-function-calling-v1": {
        "repo": "NousResearch/hermes-function-calling-v1",
        "priority": 1, "tags": ["function-calling", "hermes", "nous"],
        "desc": "Nous Research official function calling",
    },
    "hermes-function-calling-thinking": {
        "repo": "Jofthomas/hermes-function-calling-thinking-V1",
        "priority": 1, "tags": ["function-calling", "thinking", "hermes"],
        "desc": "Function calling with thinking traces",
    },
    "hermes-3-dataset": {
        "repo": "NousResearch/Hermes-3-Dataset",
        "priority": 1, "tags": ["hermes", "sft", "nous", "general"],
        "desc": "Official Hermes 3 SFT dataset",
    },
    "carnice-dpo": {
        "repo": "axolotl-ai-co/carnice-dpo",
        "priority": 1, "tags": ["dpo", "carnice", "alignment"],
        "desc": "Carnice DPO alignment data",
    },
    "carnice-agent-traces": {
        "repo": "kai-os/carnice-agent-trance-prompt-bank",
        "priority": 1, "tags": ["carnice", "agent", "traces"],
        "desc": "Carnice agent trance prompt bank",
    },
    "carnice-glm5-hermes": {
        "repo": "kai-os/carnice-glm5-hermes-traces",
        "priority": 1, "tags": ["carnice", "hermes", "traces"],
        "desc": "Carnice GLM5 Hermes traces",
    },
}

# === TIER 2: HIGH VALUE — NVIDIA Nemotron & Tool Calling ===
TIER2 = {
    "nemotron-sft-agentic-v2": {
        "repo": "nvidia/Nemotron-SFT-Agentic-v2",
        "priority": 2, "tags": ["nvidia", "agentic", "sft", "tool-calling"],
        "desc": "NVIDIA Nemotron agentic SFT v2",
    },
    "nemotron-sft-v1": {
        "repo": "nvidia/Nemotron-Pretraining-SFT-v1",
        "priority": 2, "tags": ["nvidia", "sft", "massive", "multilingual"],
        "desc": "6.5T tokens SFT data (STEM, code, math)",
        "requires_agreement": True,
    },
    "nemotron-cascade-2-sft": {
        "repo": "nvidia/Nemotron-Cascade-2-SFT-Data",
        "priority": 2, "tags": ["nvidia", "cascade", "sft"],
        "desc": "Nemotron Cascade 2 SFT data",
    },
    "nemotron-toolscale": {
        "repo": "nvidia/ToolScale",
        "priority": 2, "tags": ["nvidia", "tool-calling", "scale"],
        "desc": "NVIDIA ToolScale tool-calling",
    },
    "nemotron-agentic-v1": {
        "repo": "nvidia/Nemotron-Agentic-v1",
        "priority": 1, "tags": ["nvidia", "agentic", "tool-use", "agent"],
        "desc": "Nemotron Agentic Tool Use v1 — DESIGNED for tool-using agents",
    },
    "nemotron-post-training-v2": {
        "repo": "nvidia/Nemotron-Post-Training-Dataset-v2",
        "priority": 2, "tags": ["nvidia", "post-training", "alignment"],
        "desc": "Nemotron Post-Training Dataset v2",
    },
    "nemotron-cascade-rl-swe": {
        "repo": "nvidia/Nemotron-Cascade-RL-SWE",
        "priority": 2, "tags": ["nvidia", "rl", "swe", "agent"],
        "desc": "Nemotron Cascade RL for SWE tasks",
    },
    "nemotron-instruction-following-chat": {
        "repo": "nvidia/Nemotron-Instruction-Following-Chat-v1",
        "priority": 2, "tags": ["nvidia", "instruction-following", "chat"],
        "desc": "Nemotron instruction following chat",
    },
    "nemotron-sft-swe-v2": {
        "repo": "nvidia/Nemotron-SFT-SWE-v2",
        "priority": 2, "tags": ["nvidia", "sft", "swe", "code"],
        "desc": "Nemotron SFT for SWE tasks v2",
    },
    "nemotron-rl-safety-v1": {
        "repo": "nvidia/Nemotron-RL-Safety-v1",
        "priority": 2, "tags": ["nvidia", "rl", "safety"],
        "desc": "Nemotron RL Safety v1",
    },
    "nemotron-rl-knowledge-openqa": {
        "repo": "nvidia/Nemotron-RL-knowledge-openqa",
        "priority": 2, "tags": ["nvidia", "rl", "knowledge", "qa"],
        "desc": "Nemotron RL Knowledge OpenQA",
    },
    "nemotron-research-goosereason": {
        "repo": "nvidia/Nemotron-Research-GooseReason-0.7M",
        "priority": 2, "tags": ["nvidia", "research", "reasoning"],
        "desc": "Nemotron Research GooseReason 0.7M",
    },
    "nemotron-sft-competitive-programming-v2": {
        "repo": "nvidia/Nemotron-SFT-Competitive-Programming-v2",
        "priority": 2, "tags": ["nvidia", "sft", "code", "competitive"],
        "desc": "Nemotron SFT Competitive Programming v2",
    },
    "nemotron-competitive-programming-v1": {
        "repo": "nvidia/Nemotron-Competitive-Programming-v1",
        "priority": 2, "tags": ["nvidia", "code", "competitive"],
        "desc": "Nemotron Competitive Programming v1",
    },
    "nemotron-math-v2": {
        "repo": "nvidia/Nemotron-Math-v2",
        "priority": 2, "tags": ["nvidia", "math"],
        "desc": "Nemotron Math v2",
    },
    "nemotron-mind": {
        "repo": "nvidia/Nemotron-MIND",
        "priority": 2, "tags": ["nvidia", "math", "reasoning", "pretraining"],
        "desc": "Nemotron MIND math reasoning pretraining",
    },
    "nemotron-rl-structured-outputs": {
        "repo": "nvidia/Nemotron-RL-instruction_following-structured_outputs",
        "priority": 2, "tags": ["nvidia", "rl", "structured-output"],
        "desc": "Nemotron RL instruction following + structured outputs",
    },
    "nemotron-climblab": {
        "repo": "nvidia/Nemotron-ClimbLab",
        "priority": 3, "tags": ["nvidia", "training"],
        "desc": "Nemotron ClimbLab",
    },
    "xlam-function-calling-60k": {
        "repo": "Salesforce/xlam-function-calling-60k",
        "priority": 2, "tags": ["function-calling", "salesforce"],
        "desc": "60K function calling examples from Salesforce",
    },
    "nemotron-sft-math-v3": {
        "repo": "nvidia/Nemotron-SFT-Math-v3",
        "priority": 2, "tags": ["nvidia", "math", "sft"],
        "desc": "NVIDIA Nemotron math SFT v3",
    },
    "nemotron-sft-multilingual-v1": {
        "repo": "nvidia/Nemotron-SFT-Multilingual-v1",
        "priority": 2, "tags": ["nvidia", "multilingual", "sft"],
        "desc": "NVIDIA Nemotron multilingual SFT",
    },
}

# === TIER 3: ENRICHMENT — Community Tool Calling & Agent Data ===
TIER3 = {
    "glaive-function-calling-v2": {
        "repo": "glaiveai/glaive-function-calling-v2",
        "priority": 3, "tags": ["function-calling", "glaive"],
        "desc": "Glaive function calling v2",
    },
    "toolace-qwen-cleaned": {
        "repo": "tryumanshow/ToolACE-Qwen-cleaned",
        "priority": 3, "tags": ["tool-calling", "qwen", "cleaned"],
        "desc": "ToolACE cleaned for Qwen",
    },
    "sharegpt-tool-calls": {
        "repo": "Guilherme34/sharegpt-tool-calls",
        "priority": 3, "tags": ["sharegpt", "tool-calls"],
        "desc": "ShareGPT format tool calls",
    },
    "function-calling-sharegpt": {
        "repo": "hypervariance/function-calling-sharegpt",
        "priority": 3, "tags": ["function-calling", "sharegpt"],
        "desc": "Function calling in ShareGPT format",
    },
    "function-calling-v3": {
        "repo": "Trelis/function_calling_v3",
        "priority": 3, "tags": ["function-calling", "trelis"],
        "desc": "Trelis function calling v3",
    },
    "function-calling-extended": {
        "repo": "Trelis/function_calling_extended",
        "priority": 3, "tags": ["function-calling", "extended"],
        "desc": "Trelis function calling extended",
    },
    "qwen3-tool-calling-sft": {
        "repo": "zhendongnvidia/qwen3-tool-calling-sft-dataset",
        "priority": 3, "tags": ["qwen3", "tool-calling", "sft"],
        "desc": "Qwen3 tool calling SFT",
    },
    "qwen3.6-agent-tool-calling": {
        "repo": "ansulev/Qwen-3.6-Plus-Agent-Tool-Calling",
        "priority": 3, "tags": ["qwen3.6", "agent", "tool-calling"],
        "desc": "Qwen 3.6 Plus agent tool calling trajectories",
    },
    "retool-sft": {
        "repo": "JoeYing/ReTool-SFT",
        "priority": 3, "tags": ["tool-calling", "sft", "retool"],
        "desc": "ReTool SFT dataset",
    },
    "openhermes-2.5": {
        "repo": "NurtureAI/OpenHermes-2.5-flattened",
        "priority": 3, "tags": ["openhermes", "general", "sft"],
        "desc": "OpenHermes 2.5 flattened",
    },
    "agent-rl-open": {
        "repo": "DeepNLP/Agent-RL-Open-Dataset",
        "priority": 3, "tags": ["agent", "rl", "reinforcement"],
        "desc": "Agent RL open dataset",
    },
    "mcp-agent-trajectory": {
        "repo": "obaydata/mcp-agent-trajectory-benchmark",
        "priority": 3, "tags": ["mcp", "agent", "trajectory"],
        "desc": "MCP agent trajectory benchmark",
    },
    "swe-zero-trajectories": {
        "repo": "AlienKevin/SWE-ZERO-1k-trajectories",
        "priority": 3, "tags": ["swe", "agent", "trajectories"],
        "desc": "SWE-ZERO 1K agent trajectories",
    },
    "swe-rebench-trajectories": {
        "repo": "nebius/SWE-rebench-openhands-trajectories",
        "priority": 3, "tags": ["swe", "openhands", "agent"],
        "desc": "SWE rebench OpenHands trajectories",
    },
    "aureth-sft-curriculum": {
        "repo": "OusiaResearch/Aureth-SFT-Curriculum",
        "priority": 3, "tags": ["sft", "curriculum"],
        "desc": "Aureth SFT curriculum",
    },
    "aureth-corpus-hermes4": {
        "repo": "OusiaResearch/Aureth-Corpus-Hermes4.3-Generated",
        "priority": 3, "tags": ["hermes4", "generated", "corpus"],
        "desc": "Aureth corpus Hermes4.3 generated",
    },
    "qwen3.5-toolcalling-v2": {
        "repo": "Mustafaege/qwen3.5-toolcalling-v2",
        "priority": 3, "tags": ["qwen3.5", "tool-calling"],
        "desc": "Qwen 3.5 tool calling v2",
    },
    "openhermes-uncensored": {
        "repo": "rombodawg/OpenHermes-2.5-Uncensored",
        "priority": 3, "tags": ["openhermes", "uncensored"],
        "desc": "OpenHermes 2.5 uncensored",
    },
    "agent-world-model-1k": {
        "repo": "Snowflake/AgentWorldModel-1K",
        "priority": 3, "tags": ["agent", "world-model", "rl"],
        "desc": "Snowflake Agent World Model 1K",
    },
    "hermes-agent-reasoning-ansulev": {
        "repo": "ansulev/hermes-agent-reasoning-traces",
        "priority": 3, "tags": ["hermes", "agent", "reasoning"],
        "desc": "Hermes agent reasoning traces (ansulev fork)",
    },
}

ALL_DATASETS = {}
ALL_DATASETS.update(TIER1)
ALL_DATASETS.update(TIER2)
ALL_DATASETS.update(TIER3)


def log(entry):
    entry["timestamp"] = datetime.now().isoformat()
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def download_dataset(key, config, sample=False):
    """Download a dataset from HuggingFace."""
    repo = config["repo"]
    out_dir = DOWNLOAD_DIR / key
    out_dir.mkdir(parents=True, exist_ok=True)

    if config.get("requires_agreement"):
        print(f"  SKIP (requires agreement): {repo}")
        log({"action": "skip", "dataset": key, "reason": "requires_agreement"})
        return False

    existing = list(out_dir.glob("*.jsonl")) + list(out_dir.glob("*.parquet"))
    if existing and not sample:
        print(f"  Already downloaded: {key} ({len(existing)} files)")
        return True

    print(f"  Downloading: {repo}...")

    try:
        download_script = (
            "import json\n"
            "from datasets import load_dataset\n"
            f"ds = load_dataset('{repo}', streaming={sample}, trust_remote_code=True)\n"
            "if hasattr(ds, 'items'):\n"
            "    for split_name, split_data in ds.items():\n"
            f"        out_path = '{out_dir}/' + split_name + '.jsonl'\n"
            "        if hasattr(split_data, 'to_json'):\n"
            "            split_data.to_json(out_path)\n"
            "            print(f'Saved {split_name}')\n"
            "elif hasattr(ds, 'to_json'):\n"
            f"    ds.to_json('{out_dir}/train.jsonl')\n"
            "    print('Saved train.jsonl')\n"
            "print('Done')\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", download_script],
            capture_output=True, text=True, timeout=600
        )

        if result.returncode == 0:
            files = list(out_dir.glob("*.jsonl"))
            print(f"  OK: {key} ({len(files)} files)")
            log({"action": "download", "dataset": key, "files": len(files)})
            return True
        else:
            print(f"  FAIL: {key}: {result.stderr[:200]}")
            log({"action": "download_fail", "dataset": key, "error": result.stderr[:300]})
            return False
    except Exception as e:
        print(f"  ERROR: {key}: {e}")
        log({"action": "download_error", "dataset": key, "error": str(e)[:300]})
        return False


def format_to_sharegpt(row, dataset_key):
    """Convert any format to ShareGPT conversations."""
    # Already ShareGPT
    if "conversations" in row:
        return row["conversations"]

    # Messages format
    if "messages" in row:
        msgs = row["messages"]
        convs = []
        for m in msgs:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                convs.append({"from": "system", "value": content})
            elif role == "user":
                convs.append({"from": "human", "value": content})
            elif role == "assistant":
                if "tool_calls" in m and m["tool_calls"]:
                    tc = m["tool_calls"][0]
                    fn = tc.get("function", {})
                    fn_name = fn.get("name", "")
                    fn_args = fn.get("arguments", "{}")
                    tool_text = f"<tool_call>\n<name>{fn_name}</name>\n<arguments>{fn_args}</arguments>\n</tool_call>"
                    content = (content + "\n" + tool_text).strip() if content else tool_text
                convs.append({"from": "gpt", "value": content})
            elif role == "tool":
                convs.append({"from": "function", "value": content})
        return convs

    # Alpaca format
    if "instruction" in row:
        convs = [{"from": "human", "value": row["instruction"]}]
        if row.get("input"):
            convs[0]["value"] += "\n" + str(row["input"])
        convs.append({"from": "gpt", "value": str(row.get("output", ""))})
        return convs

    # Prompt/completion
    if "prompt" in row and "completion" in row:
        return [
            {"from": "human", "value": str(row["prompt"])},
            {"from": "gpt", "value": str(row["completion"])},
        ]

    # Chosen/rejected (DPO)
    if "chosen" in row and "rejected" in row:
        ch = row["chosen"]
        if isinstance(ch, list) and len(ch) >= 2:
            return [
                {"from": "human", "value": ch[0].get("content", "")},
                {"from": "gpt", "value": ch[1].get("content", "")},
            ]

    return None


def prepare_training_data(sample=False):
    """Process all downloaded data into unified ShareGPT JSONL."""
    PREPARED_DIR.mkdir(parents=True, exist_ok=True)
    output_file = PREPARED_DIR / "senter-hermes-dataset.jsonl"

    total_rows = 0
    dataset_counts = {}

    with open(output_file, "w") as out:
        for key in sorted(ALL_DATASETS.keys()):
            config = ALL_DATASETS[key]
            data_dir = DOWNLOAD_DIR / key
            if not data_dir.exists():
                continue

            jsonl_files = list(data_dir.glob("*.jsonl"))
            if not jsonl_files:
                continue

            count = 0
            for jf in jsonl_files:
                try:
                    with open(jf) as f:
                        for line in f:
                            try:
                                row = json.loads(line)
                                convs = format_to_sharegpt(row, key)
                                if convs and len(convs) >= 2:
                                    out.write(json.dumps({
                                        "conversations": convs,
                                        "source": key,
                                        "tags": config.get("tags", []),
                                    }, default=str) + "\n")
                                    count += 1
                                    total_rows += 1
                            except json.JSONDecodeError:
                                continue
                except Exception as e:
                    print(f"  Error processing {jf}: {e}")

            if count > 0:
                dataset_counts[key] = count
                print(f"  {key}: {count} conversations")

    print(f"\n{'='*60}")
    print(f"Total: {total_rows} conversations from {len(dataset_counts)} datasets")
    print(f"Output: {output_file}")
    print(f"{'='*60}")

    manifest = {
        "name": "Senter-Hermes-Dataset",
        "total_conversations": total_rows,
        "datasets": dataset_counts,
        "created": datetime.now().isoformat(),
        "output_file": str(output_file),
        "description": "Unified Hermes agent / tool-calling / agentic training data. 50 sources from HuggingFace including NousResearch, NVIDIA Nemotron, Carnice, and community tool-calling datasets.",
    }
    with open(PREPARED_DIR / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    return output_file, total_rows


def main():
    parser = argparse.ArgumentParser(description="Mega Agentic Training Data Pipeline")
    parser.add_argument("--download", action="store_true", help="Download all datasets")
    parser.add_argument("--prepare", action="store_true", help="Prepare unified training data")
    parser.add_argument("--sample", action="store_true", help="Samples only (faster)")
    parser.add_argument("--list", action="store_true", help="List all datasets")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3], help="Only this tier")
    parser.add_argument("--output", default=str(PREPARED_DIR))
    args = parser.parse_args()

    if args.list:
        print(f"\nAll datasets ({len(ALL_DATASETS)} total):\n")
        for key in sorted(ALL_DATASETS.keys(), key=lambda k: ALL_DATASETS[k]["priority"]):
            cfg = ALL_DATASETS[key]
            tags = ", ".join(cfg.get("tags", []))
            print(f"  P{cfg['priority']} {key}: {cfg['desc']}")
            print(f"         {cfg['repo']}  [{tags}]")
        return

    if args.download:
        print(f"\nDownloading {'SAMPLES' if args.sample else 'FULL'} datasets...\n")
        for key in sorted(ALL_DATASETS.keys(), key=lambda k: ALL_DATASETS[k]["priority"]):
            cfg = ALL_DATASETS[key]
            if args.tier and cfg["priority"] != args.tier:
                continue
            download_dataset(key, cfg, args.sample)

    if args.prepare:
        print(f"\nPreparing unified training data...\n")
        prepare_training_data(args.sample)


if __name__ == "__main__":
    main()
