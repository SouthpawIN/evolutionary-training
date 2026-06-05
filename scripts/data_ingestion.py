#!/usr/bin/env python3
"""
Data Ingestion Pipeline for Evolutionary Training
Downloads, converts, and indexes training data from all sources.

Usage:
  python3 data_ingestion.py [--source SOURCE] [--output DIR] [--sample]
"""

import json, os, sys, subprocess, hashlib
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data-sources"
INGEST_LOG = BASE_DIR / "logs" / "ingestion.jsonl"

# === Data Sources ===
SOURCES = {
    # Hermes Agent Reasoning (CRITICAL)
    "hermes-tool-use": {
        "type": "hf_dataset",
        "repo": "interstellarninja/hermes_reasoning_tool_use",
        "format": "sharegpt",
        "priority": 1,
        "description": "51K tool-calling conversations (single/multi-turn, relevance)",
        "tags": ["agent", "tool-use", "reasoning", "sft"],
    },
    "hermes-agent-traces": {
        "type": "hf_dataset",
        "repo": "lambda/hermes-agent-reasoning-traces",
        "format": "sharegpt",
        "priority": 1,
        "description": "Real Hermes agent multi-turn trajectories",
        "tags": ["agent", "traces", "reasoning"],
    },
    # Nemotron Datasets (HIGH)
    "nemotron-sft": {
        "type": "hf_dataset",
        "repo": "nvidia/Nemotron-Pretraining-SFT-v1",
        "format": "parquet",
        "priority": 2,
        "description": "6.5T tokens — SFT data across STEM, code, math, multilingual",
        "tags": ["sft", "nvidia", "massive", "multilingual"],
        "requires_agreement": True,
    },
    "nemotron-code": {
        "type": "hf_dataset",
        "repo": "nvidia/Nemotron-Pretraining-Code-v2",
        "format": "parquet",
        "priority": 2,
        "description": "836M code rows from GitHub",
        "tags": ["code", "nvidia"],
    },
    "nemotron-math": {
        "type": "hf_dataset",
        "repo": "nvidia/Nemotron-CC-Math-v1",
        "format": "parquet",
        "priority": 2,
        "description": "190M math rows from Common Crawl",
        "tags": ["math", "nvidia"],
    },
    # Nous Research (HIGH)
    "atropos-swe-smith": {
        "type": "hf_dataset",
        "repo": "NousResearch/SWE-smith-oracle",
        "format": "parquet",
        "priority": 2,
        "description": "10.2K SWE tasks from Atropos RL framework",
        "tags": ["code", "agent", "rl", "nous"],
    },
    # Multimodal
    "open-mm-rl": {
        "type": "hf_dataset",
        "repo": "TuringEnterprises/Open-MM-RL",
        "format": "json",
        "priority": 2,
        "description": "Multimodal STEM reasoning (40→3K tasks)",
        "tags": ["multimodal", "stem", "reasoning"],
    },
    # Local session traces
    "local-sessions": {
        "type": "local",
        "path": os.path.expanduser("~/.hermes"),
        "format": "json",
        "priority": 1,
        "description": "Local Hermes agent session traces (318 files, 134MB)",
        "tags": ["agent", "traces", "local"],
    },
    # Discord data
    "discord-darwin": {
        "type": "local",
        "path": str(DATA_DIR / "discord" / "darwin"),
        "format": "markdown",
        "priority": 1,
        "description": "Darwin paper breakdown + merge methodology",
        "tags": ["darwin", "methodology"],
    },
    "discord-hermes-docs": {
        "type": "local",
        "path": str(DATA_DIR / "discord" / "hermes-docs"),
        "format": "markdown",
        "priority": 1,
        "description": "Hermes fleet guide, ops blueprint, MCP setup",
        "tags": ["hermes", "docs", "agent"],
    },
}


def log_ingestion(source, status, details=""):
    """Append to ingestion log."""
    INGEST_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "source": source,
        "status": status,
        "details": details,
    }
    with open(INGEST_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def download_hf_dataset(repo, output_dir, sample=False):
    """Download a HuggingFace dataset using huggingface-cli or Python."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Try using Python datasets library
    try:
        cmd = f"""python3 -c "
from datasets import load_dataset
import os
ds = load_dataset('{repo}', streaming={'True' if sample else 'False'})
if hasattr(ds, 'keys'):
    for split in ds.keys():
        print(f'  Split: {{split}}')
        if {sample}:
            subset = ds[split].take(100)
            subset.to_json('{output_dir}/{{split}}_sample.jsonl')
            print(f'  Saved sample: {{split}}_sample.jsonl')
        else:
            ds[split].to_json('{output_dir}/{{split}}.jsonl')
            print(f'  Saved: {{split}}.jsonl')
print('Done')
" 2>&1"""
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Timeout after 600s"
    except Exception as e:
        return False, str(e)


def scan_local_sessions(hermes_dir):
    """Scan and index local Hermes session files."""
    sessions_dir = Path(hermes_dir) / "sessions"
    profiles_dir = Path(hermes_dir) / "profiles"
    
    index = []
    
    # Main sessions
    if sessions_dir.exists():
        for f in sessions_dir.glob("*.json"):
            try:
                with open(f) as fh:
                    data = json.load(fh)
                index.append({
                    "path": str(f),
                    "profile": "main",
                    "size_bytes": f.stat().st_size,
                    "type": "session",
                })
            except:
                pass
    
    # Profile sessions
    if profiles_dir.exists():
        for profile_dir in profiles_dir.iterdir():
            if profile_dir.is_dir():
                sessions = profile_dir / "sessions"
                if sessions.exists():
                    for f in sessions.glob("*.json"):
                        if f.name == "sessions.json":
                            continue
                        try:
                            index.append({
                                "path": str(f),
                                "profile": profile_dir.name,
                                "size_bytes": f.stat().st_size,
                                "type": "session",
                            })
                        except:
                            pass
    
    return index


def ingest_source(source_key, sample=False):
    """Ingest a single data source."""
    source = SOURCES[source_key]
    output_dir = DATA_DIR / "ingested" / source_key
    
    print(f"\n{'='*50}")
    print(f"Ingesting: {source_key}")
    print(f"  Type: {source['type']}")
    print(f"  Description: {source['description']}")
    print(f"{'='*50}")
    
    if source["type"] == "hf_dataset":
        if source.get("requires_agreement"):
            print(f"  ⚠️  Requires NVIDIA data agreement — skipping auto-download")
            print(f"  Manual download: https://huggingface.co/datasets/{source['repo']}")
            log_ingestion(source_key, "skipped", "requires_agreement")
            return
        
        ok, msg = download_hf_dataset(source["repo"], output_dir, sample)
        if ok:
            print(f"  ✓ Downloaded successfully")
            log_ingestion(source_key, "success", msg[:200])
        else:
            print(f"  ✗ Failed: {msg[:200]}")
            log_ingestion(source_key, "failed", msg[:200])
    
    elif source["type"] == "local":
        if "hermes" in source.get("path", ""):
            index = scan_local_sessions(source["path"])
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(output_dir / "session_index.json", "w") as f:
                json.dump(index, f, indent=2)
            print(f"  ✓ Indexed {len(index)} session files")
            log_ingestion(source_key, "indexed", f"{len(index)} files")
        else:
            path = Path(source["path"])
            if path.exists():
                files = list(path.rglob("*"))
                print(f"  ✓ Found {len(files)} files in {path}")
                log_ingestion(source_key, "found", f"{len(files)} files")
            else:
                print(f"  ✗ Path not found: {path}")
                log_ingestion(source_key, "not_found", str(path))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Data Ingestion Pipeline")
    parser.add_argument("--source", choices=list(SOURCES.keys()), help="Specific source to ingest")
    parser.add_argument("--all", action="store_true", help="Ingest all sources")
    parser.add_argument("--sample", action="store_true", help="Download samples only (faster)")
    parser.add_argument("--list", action="store_true", help="List available sources")
    args = parser.parse_args()
    
    if args.list:
        print("\nAvailable data sources:")
        for key, src in sorted(SOURCES.items(), key=lambda x: x[1]["priority"]):
            tags = ", ".join(src["tags"])
            print(f"  P{src['priority']} [{src['type']}] {key}: {src['description']}")
            print(f"       Tags: {tags}")
        return
    
    if args.source:
        ingest_source(args.source, args.sample)
    elif args.all:
        for key in sorted(SOURCES.keys(), key=lambda k: SOURCES[k]["priority"]):
            ingest_source(key, args.sample)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
