#!/bin/bash
set -euo pipefail
BASE="/home/sovthpaw/projects/evolutionary-training/training-data/raw"
mkdir -p "$BASE"

download_hf() {
    local key="$1"
    local repo="$2"
    local out="$BASE/$key"
    mkdir -p "$out"
    
    if [ -f "$out/.done" ]; then
        echo "  SKIP $key (already done)"
        return
    fi
    
    echo "  Downloading $repo..."
    # Download with huggingface-cli — grabs parquet/jsonl files
    huggingface-cli download "$repo"         --local-dir "$out"         --include "*.jsonl*"         --include "*.parquet"         2>&1 | tail -3
    
    # Convert parquet to jsonl if needed
    for pq in "$out"/**/*.parquet "$out"/*.parquet; do
        [ -f "$pq" ] || continue
        echo "  Converting $(basename $pq) to JSONL..."
        python3 -c "
import pandas as pd, json, sys
df = pd.read_parquet('$pq')
out_path = '${pq%.parquet}.jsonl'
df.to_json(out_path, orient='records', lines=True)
print(f'  -> {out_path} ({len(df)} rows)')
" 2>&1
    done
    
    # Count rows
    local rows=$(cat "$out"/*.jsonl "$out"/**/*.jsonl 2>/dev/null | wc -l)
    echo "  Done $key: $rows rows"
    touch "$out/.done"
}

# === TIER 1: CRITICAL (run these first) ===
echo "=== TIER 1: Critical Hermes/Agent Data ==="
download_hf "hermes-reasoning-tool-use" "interstellarninja/hermes_reasoning_tool_use"
download_hf "hermes-function-calling-v1" "NousResearch/hermes-function-calling-v1"
download_hf "hermes-3-dataset" "NousResearch/Hermes-3-Dataset"
download_hf "hermes-function-calling-thinking" "Jofthomas/hermes-function-calling-thinking-V1"
download_hf "nemotron-agentic-v1" "nvidia/Nemotron-Agentic-v1"
download_hf "carnice-dpo" "axolotl-ai-co/carnice-dpo"
download_hf "carnice-agent-traces" "kai-os/carnice-agent-trance-prompt-bank"
download_hf "hermes-agent-traces-filtered" "DJLougen/hermes-agent-traces-filtered"

# === TIER 2: HIGH VALUE NVIDIA ===
echo "=== TIER 2: NVIDIA Nemotron ==="
download_hf "nemotron-post-training-v2" "nvidia/Nemotron-Post-Training-Dataset-v2"
download_hf "nemotron-cascade-2-sft" "nvidia/Nemotron-Cascade-2-SFT-Data"
download_hf "nemotron-toolscale" "nvidia/ToolScale"
download_hf "nemotron-sft-swe-v2" "nvidia/Nemotron-SFT-SWE-v2"
download_hf "nemotron-cascade-rl-swe" "nvidia/Nemotron-Cascade-RL-SWE"
download_hf "nemotron-instruction-following-chat" "nvidia/Nemotron-Instruction-Following-Chat-v1"
download_hf "nemotron-rl-safety-v1" "nvidia/Nemotron-RL-Safety-v1"
download_hf "nemotron-rl-knowledge-openqa" "nvidia/Nemotron-RL-knowledge-openqa"
download_hf "nemotron-research-goosereason" "nvidia/Nemotron-Research-GooseReason-0.7M"
download_hf "nemotron-sft-competitive-programming-v2" "nvidia/Nemotron-SFT-Competitive-Programming-v2"
download_hf "nemotron-competitive-programming-v1" "nvidia/Nemotron-Competitive-Programming-v1"
download_hf "nemotron-math-v2" "nvidia/Nemotron-Math-v2"
download_hf "nemotron-mind" "nvidia/Nemotron-MIND"
download_hf "nemotron-rl-structured-outputs" "nvidia/Nemotron-RL-instruction_following-structured_outputs"
download_hf "nemotron-sft-math-v3" "nvidia/Nemotron-SFT-Math-v3"
download_hf "nemotron-sft-multilingual-v1" "nvidia/Nemotron-SFT-Multilingual-v1"

# === TIER 3: Community tool calling ===
echo "=== TIER 3: Community Data ==="
download_hf "glaive-function-calling-v2" "glaiveai/glaive-function-calling-v2"
download_hf "xlam-function-calling-60k" "Salesforce/xlam-function-calling-60k"
download_hf "toolace-qwen-cleaned" "tryumanshow/ToolACE-Qwen-cleaned"
download_hf "function-calling-v3" "Trelis/function_calling_v3"
download_hf "openhermes-2.5" "NurtureAI/OpenHermes-2.5-flattened"
download_hf "qwen3-tool-calling-sft" "zhendongnvidia/qwen3-tool-calling-sft-dataset"
download_hf "agent-rl-open" "DeepNLP/Agent-RL-Open-Dataset"
download_hf "aureth-sft-curriculum" "OusiaResearch/Aureth-SFT-Curriculum"

echo ""
echo "=== ALL DOWNLOADS COMPLETE ==="
echo "Preparing unified training data..."
python3 /home/sovthpaw/projects/evolutionary-training/scripts/mega_training_data.py --prepare 2>&1
echo "DONE"
