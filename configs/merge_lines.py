#!/usr/bin/env python3
"""
Multi-Line Evolution Pipeline Configuration

Three Darwin merge lines:
  Line 1: Cosmos + LFM2.5 → OmniSenter (agentic/tool-calling)
  Line 2: Cosmos + AceStep → OmniStep (music/omnimodal)
  Line 3: Best of L1 + Best of L2 → OmniSS (the ultimate combo)
"""

LINES = {
    # === LINE 1: Cosmos + LFM2.5 → OmniSenter ===
    "omnisenter": {
        "name": "OmniSenter (Cosmos + LFM2.5)",
        "parent_a": {
            "name": "Cosmos3-Nano",
            "path": "/home/sovthpaw/Models/storage/Cosmos3-Nano",
            "text_prefix": "thinker.model.",
            "lm_head_key": "thinker.lm_head.weight",
            "hidden": 15750,  # 15.75B
            "hf_repo": "nvidia/Cosmos3-Nano",
        },
        "parent_b": {
            "name": "LFM2.5-8B-A1B",
            "path": "/home/sovthpaw/Models/storage/LFM2.5-8B-A1B",
            "text_prefix": "model.",
            "lm_head_key": "lm_head.weight",
            "hidden": 8470,  # 8.47B
            "hf_repo": "LiquidAI/LFM2.5-8B-A1B",
        },
        "merge_script": "lfm_cosmos_darwin_merge.py",
        "hf_evo_repo": "sovthpaw/omnisenter-evo",
        "hf_train_repo": "sovthpaw/omnisenter-train",
        "role": "agentic",
        "target_capabilities": ["tool-calling", "reasoning", "agent", "function-execution"],
    },
    
    # === LINE 2: Cosmos + AceStep → OmniStep ===
    "omnistep": {
        "name": "OmniStep (Cosmos + AceStep)",
        "parent_a": {
            "name": "Cosmos3-Nano",
            "path": "/home/sovthpaw/Models/storage/Cosmos3-Nano",
            "text_prefix": "thinker.model.",
            "lm_head_key": "thinker.lm_head.weight",
            "hidden": 15750,
            "hf_repo": "nvidia/Cosmos3-Nano",
        },
        "parent_b": {
            "name": "AceStep-5Hz-LM-4B",
            "path": "/home/sovthpaw/Models/hf/Ace-Step1.5/acestep-5Hz-lm-4B",
            "text_prefix": "model.",
            "lm_head_key": "lm_head.weight",
            "hidden": 4000,  # 4B
            "hf_repo": "ACE-Step/acestep-5Hz-lm-4B",
            "note": "Qwen3-4B, hidden=2560, 36L — larger model, better music understanding",
        },
        "merge_script": "lfm_cosmos_darwin_merge.py",
        "hf_evo_repo": "sovthpaw/omnistep-evo",
        "hf_train_repo": "sovthpaw/omnistep-train",
        "role": "music",
        "target_capabilities": ["music-generation", "voice", "omnimodal"],
    },
    
    # === LINE 3: Best L1 + Best L2 → OmniSS ===
    "omniss": {
        "name": "OmniSS (OmniSenter + OmniStep)",
        "parent_a": {
            "name": "Best-OmniSenter",
            "path": None,  # Set dynamically from L1 best
            "text_prefix": "",  # Already merged
            "lm_head_key": "lm_head.weight",
            "hf_repo": "sovthpaw/omnisenter-evo",
        },
        "parent_b": {
            "name": "Best-OmniStep",
            "path": None,  # Set dynamically from L2 best
            "text_prefix": "",  # Already merged
            "lm_head_key": "lm_head.weight",
            "hf_repo": "sovthpaw/omnistep-evo",
        },
        "merge_script": "lfm_cosmos_darwin_merge.py",
        "hf_evo_repo": "sovthpaw/omniss-evo",
        "hf_train_repo": "sovthpaw/omniss-train",
        "role": "combined",
        "target_capabilities": ["tool-calling", "reasoning", "agent", "music-generation", "voice", "omnimodal"],
        "depends_on": ["omnisenter", "omnistep"],
    },
}

# CMA-ES config per line
CMAES_CONFIG = {
    "omnisenter": {
        "pop_size": 4,
        "sigma_init": 0.3,
        "sigma_min": 0.05,
        "generations_per_cycle": 2,
        "min_improvement_pct": 0.5,
    },
    "omnistep": {
        "pop_size": 4,
        "sigma_init": 0.3,
        "sigma_min": 0.05,
        "generations_per_cycle": 2,
        "min_improvement_pct": 0.5,
    },
    "omniss": {
        "pop_size": 4,
        "sigma_init": 0.2,
        "sigma_min": 0.05,
        "generations_per_cycle": 2,
        "min_improvement_pct": 0.5,
    },
}

# Training data mapping per line
TRAINING_DATA = {
    "omnisenter": {
        "priority_sources": [
            "interstellarninja/hermes_reasoning_tool_use",
            "NousResearch/hermes-function-calling-v1",
            "Jofthomas/hermes-function-calling-thinking-V1",
            "nvidia/Nemotron-Agentic-v1",
            "axolotl-ai-co/carnice-dpo",
            "kai-os/carnice-agent-trance-prompt-bank",
            "lambda/hermes-agent-reasoning-traces",
            "Salesforce/xlam-function-calling-60k",
        ],
        "secondary_sources": [
            "NousResearch/Hermes-3-Dataset",
            "glaiveai/glaive-function-calling-v2",
            "Trelis/function_calling_v3",
            "DeepNLP/Agent-RL-Open-Dataset",
        ],
    },
    "omnistep": {
        "priority_sources": [
            "nvidia/Nemotron-Pretraining-SFT-v1",
            "OusiaResearch/Aureth-SFT-Curriculum",
            "NurtureAI/OpenHermes-2.5-flattened",
        ],
        "secondary_sources": [
            "nvidia/Nemotron-Post-Training-Dataset-v2",
            "nvidia/Nemotron-Math-v2",
        ],
    },
    "omniss": {
        "priority_sources": [
            "interstellarninja/hermes_reasoning_tool_use",
            "nvidia/Nemotron-Agentic-v1",
            "axolotl-ai-co/carnice-dpo",
            "NousResearch/hermes-function-calling-v1",
        ],
        "secondary_sources": [
            "NousResearch/Hermes-3-Dataset",
            "nvidia/Nemotron-Post-Training-Dataset-v2",
        ],
    },
}
