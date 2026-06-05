#!/usr/bin/env python3
"""
Discord Status Reporter for Evolution Pipeline

Generates status reports for the evolution pipeline and formats them
for Discord posting. Designed to be called by a Hermes cron job.

Usage:
  python3 discord_evolution_report.py [--model MODEL_KEY] [--all]
"""

import json, os, argparse
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
EVOLUTION_DIR = BASE_DIR / "evolution"
LOGS_DIR = BASE_DIR / "logs"
RESULTS_DIR = BASE_DIR / "benchmarks" / "results"


def get_evolution_status(model_key):
    """Get current evolution status for a model."""
    evo_dir = EVOLUTION_DIR / model_key
    cmaes_state = evo_dir / "cmaes_state.json"
    log_file = LOGS_DIR / f"evolution_{model_key}.jsonl"

    status = {
        "model": model_key,
        "generation": 0,
        "best_fitness": 0.0,
        "sigma": 0.0,
        "total_cycles": 0,
        "last_cycle": None,
        "hf_upload": None,
    }

    if cmaes_state.exists():
        with open(cmaes_state) as f:
            data = json.load(f)
        status["generation"] = data.get("generation", 0)
        status["best_fitness"] = data.get("best_fitness", 0.0)
        status["sigma"] = data.get("sigma", 0.0)

    if log_file.exists():
        with open(log_file) as f:
            lines = f.readlines()
        cycles = [json.loads(l) for l in lines if '"cycle_complete"' in l]
        uploads = [json.loads(l) for l in lines if '"hf_upload"' in l]
        status["total_cycles"] = len(cycles)
        if cycles:
            status["last_cycle"] = cycles[-1].get("timestamp")
        if uploads:
            status["hf_upload"] = uploads[-1].get("timestamp")

    return status


def format_discord_report(statuses):
    """Format status for Discord posting."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# Evolution Pipeline Status - {now}",
        "",
    ]

    for status in statuses:
        emoji = "GREEN" if status["best_fitness"] > 0 else "RED"
        lines.append(f"## {status['model']}")
        lines.append(f"- Generation: {status['generation']}")
        lines.append(f"- Best Fitness: {status['best_fitness']:.4f}")
        lines.append(f"- Sigma: {status['sigma']:.4f}")
        lines.append(f"- Total Cycles: {status['total_cycles']}")
        if status["last_cycle"]:
            lines.append(f"- Last Cycle: {status['last_cycle']}")
        if status["hf_upload"]:
            lines.append(f"- Last Upload: {status['hf_upload']}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Discord Evolution Report")
    parser.add_argument("--model", help="Specific model key")
    parser.add_argument("--all", action="store_true", help="Report all models")
    args = parser.parse_args()

    models = ["qwen-cosmos", "omnistep"] if args.all else [args.model or "qwen-cosmos"]
    statuses = [get_evolution_status(m) for m in models]
    report = format_discord_report(statuses)
    print(report)


if __name__ == "__main__":
    main()
