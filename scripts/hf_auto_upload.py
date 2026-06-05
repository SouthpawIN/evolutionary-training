#!/usr/bin/env python3
"""
HuggingFace Auto-Upload for Evolved Models

Uploads the best evolved model from the latest evolution cycle.
Creates proper model cards with benchmark results.

Usage:
  python3 hf_auto_upload.py --model MODEL_KEY [--force] [--dry-run]
"""

import json, os, sys, subprocess, argparse
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
EVOLUTION_DIR = BASE_DIR / "evolution"
RESULTS_DIR = BASE_DIR / "benchmarks" / "results"

{
    "lfm-cosmos": {
        "repo_prefix": "sovthpaw/lfm-cosmos-evo",
        "name": "LFM2.5 x Cosmos3-Nano (Darwin Evolved)",
        "description": "Cross-architecture Darwin Family merge of LiquidAI LFM2.5 8B-A1B and NVIDIA Cosmos3-Nano. Evolved via CMA-ES genome optimization.",
        "parent_a": "nvidia/Cosmos3-Nano",
        "parent_b": "LiquidAI/LFM2.5-8B-A1B",
    },
    "omnistep": {
        "repo_prefix": "sovthpaw/omnistep-evo",
        "name": "OmniStep Evolved (Darwin Family)",
        "description": "Darwin Family evolved OmniStep 12A3B. Self-improving omnimodal model.",
        "parent_a": "sovthpaw/omnistep-12a3b",
        "parent_b": "LiquidAI/LFM2.5-8B-A1B",
    },
}


def get_repo_name(model_key, generation):
    """Staged repo naming: sovthpaw/lfm-cosmos-evo-gen0, gen1, etc."""
    prefix = MODEL_CONFIGS[model_key]["repo_prefix"]
    return f"{prefix}-gen{generation}"



def generate_model_card(config, generation, fitness, genome):
    """Generate a proper model card with benchmark results."""
    genome_json = json.dumps(genome, indent=2)
    card = f"""---
license: apache-2.0
tags:
  - darwin-family
  - evolutionary-merging
  - cma-es
  - cross-architecture
  - omnimodal
---

# {config["name"]}

> **Generation {generation}** | Fitness: {fitness:.4f} | Auto-evolved via Darwin Family (arXiv:2605.14386)

## Overview

{config["description"]}

## Parents

- **Parent A**: [{config["parent_a"]}](https://huggingface.co/{config["parent_a"]})
- **Parent B**: [{config["parent_b"]}](https://huggingface.co/{config["parent_b"]})

## Evolution Details

- **Method**: Darwin Family MRI-Trust Fusion with CMA-ES genome optimization
- **Generation**: {generation}
- **Fitness Score**: {fitness:.4f}
- **Paper**: [arXiv:2605.14386](https://arxiv.org/abs/2605.14386)

### Genome Parameters

```json
{genome_json}
```

## Usage

This model is auto-evolved. The latest generation represents the best-performing
merge found by CMA-ES over the Darwin genome space.

## Methodology

The Darwin Family technique merges two pretrained LLMs without any gradient updates:

1. **14-dimensional merge genome** controls per-tensor blending ratios
2. **MRI-Trust Fusion** combines diagnostic signals with evolutionary priors
3. **CMA-ES** optimizes the genome over generations
4. **Architecture Mapper** handles cross-architecture dimension mismatches

This is a **self-improving** model - new generations are uploaded automatically
as CMA-ES finds better merge configurations.

## License

Apache 2.0 (inherits from parent models).
"""
    return card


def find_best_model(model_key):
    """Find the best evolved model from the latest cycle."""
    evo_dir = EVOLUTION_DIR / model_key
    if not evo_dir.exists():
        return None, 0, 0.0, {}

    best_dirs = sorted(evo_dir.glob("gen*_best"))
    if not best_dirs:
        return None, 0, 0.0, {}

    latest = best_dirs[-1]
    gen_num = int(latest.name.replace("gen", "").replace("_best", ""))

    log_file = BASE_DIR / "logs" / f"evolution_{model_key}.jsonl"
    fitness = 0.0
    genome = {}
    if log_file.exists():
        with open(log_file) as f:
            for line in f:
                entry = json.loads(line)
                if entry.get("action") == "cycle_complete":
                    fitness = entry.get("best_fitness", 0.0)
                    genome = entry.get("best_genome", {})

    return str(latest), gen_num, fitness, genome


def get_repo_name(model_key, generation):
    """Staged repo naming: sovthpaw/lfm-cosmos-evo-gen0, gen1, etc."""
    prefix = MODEL_CONFIGS[model_key]["repo_prefix"]
    return f"{prefix}-gen{generation}"


def upload_model(model_key, dry_run=False):
    """Upload the best evolved model to HuggingFace as a staged generation."""
    config = MODEL_CONFIGS[model_key]
    model_path, generation, fitness, genome = find_best_model(model_key)

    if not model_path:
        print(f"No evolved model found for {model_key}")
        return False

    repo_name = get_repo_name(model_key, generation)

    print(f"\n{'='*60}")
    print(f"HuggingFace Upload: {config['name']}")
    print(f"{'='*60}")
    print(f"  Model: {model_path}")
    print(f"  Generation: {generation}")
    print(f"  Fitness: {fitness:.4f}")
    print(f"  Repo: {repo_name}")

    if dry_run:
        print("\n  DRY RUN - not uploading")
        return True

    card = generate_model_card(config, generation, fitness, genome)
    card_path = Path(model_path) / "README.md"
    with open(card_path, "w") as f:
        f.write(card)
    print(f"  Model card written to {card_path}")

    print(f"\n  Uploading to {repo_name}...")
    result = subprocess.run(
        ["huggingface-cli", "upload", repo_name, model_path, ".",
         "--commit-message", f"Darwin evolution generation {generation}, fitness={fitness:.4f}"],
        capture_output=True, text=True, timeout=3600,
    )

    if result.returncode == 0:
        print(f"  Upload complete: https://huggingface.co/{repo_name}")
        return True
    else:
        print(f"  Upload failed: {result.stderr[:300]}")
        return False


def main():
    parser = argparse.ArgumentParser(description="HF Auto-Upload for Evolved Models")
    parser.add_argument("--model", choices=list(MODEL_CONFIGS.keys()), default="lfm-cosmos")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    upload_model(args.model, args.dry_run)


if __name__ == "__main__":
    main()
