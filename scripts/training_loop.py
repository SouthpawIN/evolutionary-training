#!/usr/bin/env python3
"""
Evolutionary Training Loop — Cron Script
Runs benchmarks, tracks progress, reports to Discord.

Designed to run as a Hermes cron job or standalone.

Usage:
  python3 training_loop.py [--phase PHASE] [--dry-run]

Phases:
  benchmark  — Run benchmarks against both models
  ingest     — Check for new data and ingest
  report     — Generate and post progress report
  full       — All phases in sequence
"""

import json, os, sys, subprocess, time
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "benchmarks" / "results"
LOGS_DIR = BASE_DIR / "logs"
CONFIGS_DIR = BASE_DIR / "configs"

# Discord webhook for automated posting (set via env or config)
DISCORD_REPORT_CHANNEL = os.environ.get("DISCORD_REPORT_CHANNEL", "")

# Model endpoints
MODELS = {
    "darwin-main": "http://127.0.0.1:8080/v1",
    "apex-mtp-aux": "http://127.0.0.1:8081/v1",
}


def check_model_health(endpoint):
    """Check if a model endpoint is responding."""
    import urllib.request
    try:
        # Try the health endpoint first
        health_url = endpoint.replace("/v1", "/health")
        with urllib.request.urlopen(health_url, timeout=5) as resp:
            return resp.status == 200
    except:
        # Try a minimal completions request
        try:
            payload = json.dumps({
                "model": "test",
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1,
            }).encode()
            req = urllib.request.Request(
                f"{endpoint}/chat/completions",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return True
        except:
            return False


def run_benchmark_phase():
    """Run benchmarks against all available models."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "phase": "benchmark",
        "models": {},
    }
    
    for model_key, endpoint in MODELS.items():
        health = check_model_health(endpoint)
        report["models"][model_key] = {
            "endpoint": endpoint,
            "healthy": health,
        }
        
        if health:
            # Run quick benchmark
            result = subprocess.run(
                [sys.executable, str(BASE_DIR / "scripts" / "darwin_benchmark.py"),
                 "--model", model_key, "--suite", "quick"],
                capture_output=True, text=True, timeout=300,
            )
            report["models"][model_key]["benchmark_output"] = result.stdout[-500:]
            report["models"][model_key]["benchmark_exit"] = result.returncode
        else:
            report["models"][model_key]["error"] = "Model not responding"
    
    # Save report
    report_path = LOGS_DIR / f"loop_report_{timestamp}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    return report


def run_ingest_phase():
    """Check for new data sources and ingest."""
    import urllib.request
    
    new_sources = []
    
    # Check Nous Research HF for new datasets
    try:
        url = "https://huggingface.co/api/datasets?author=NousResearch&sort=lastModified&direction=-1&limit=5"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            datasets = json.loads(resp.read())
            for ds in datasets:
                new_sources.append({
                    "repo": ds.get("id", ""),
                    "last_modified": ds.get("lastModified", ""),
                    "downloads": ds.get("downloads", 0),
                })
    except Exception as e:
        new_sources.append({"error": f"Nous Research check failed: {e}"})
    
    # Check NVIDIA HF for new datasets
    try:
        url = "https://huggingface.co/api/datasets?author=nvidia&sort=lastModified&direction=-1&limit=5"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            datasets = json.loads(resp.read())
            for ds in datasets:
                new_sources.append({
                    "repo": ds.get("id", ""),
                    "last_modified": ds.get("lastModified", ""),
                    "downloads": ds.get("downloads", 0),
                })
    except Exception as e:
        new_sources.append({"error": f"NVIDIA check failed: {e}"})
    
    return {
        "timestamp": datetime.now().isoformat(),
        "phase": "ingest",
        "new_sources": new_sources,
    }


def generate_report(benchmark_report, ingest_report):
    """Generate a human-readable progress report."""
    lines = []
    lines.append("# 🧬 Evolutionary Training Loop — Status Report")
    lines.append(f"**Timestamp:** {datetime.now().isoformat()}")
    lines.append("")
    
    # Model Status
    lines.append("## 🤖 Model Status")
    for model_key, info in benchmark_report.get("models", {}).items():
        status = "🟢 ONLINE" if info.get("healthy") else "🔴 OFFLINE"
        lines.append(f"- **{model_key}**: {status}")
        if info.get("benchmark_exit") == 0:
            lines.append(f"  - Benchmark: ✓ Passed")
        elif info.get("benchmark_exit"):
            lines.append(f"  - Benchmark: ✗ Failed (exit {info['benchmark_exit']})")
    lines.append("")
    
    # Data Ingestion
    lines.append("## 📥 Data Ingestion")
    new_sources = ingest_report.get("new_sources", [])
    hf_sources = [s for s in new_sources if "repo" in s and "NousResearch" in s.get("repo", "")]
    nvidia_sources = [s for s in new_sources if "repo" in s and "nvidia" in s.get("repo", "")]
    
    if hf_sources:
        lines.append(f"**Nous Research** — {len(hf_sources)} recent datasets:")
        for s in hf_sources[:3]:
            lines.append(f"  - {s['repo']} ({s.get('downloads', 0):,} downloads)")
    
    if nvidia_sources:
        lines.append(f"**NVIDIA** — {len(nvidia_sources)} recent datasets:")
        for s in nvidia_sources[:3]:
            lines.append(f"  - {s['repo']} ({s.get('downloads', 0):,} downloads)")
    lines.append("")
    
    # Recent Results
    lines.append("## 📈 Recent Benchmark Results")
    if RESULTS_DIR.exists():
        results = sorted(RESULTS_DIR.glob("*.json"))[-5:]
        for r in results:
            try:
                with open(r) as f:
                    data = json.load(f)
                lines.append(f"- {r.name}: {data.get('successful', '?')}/{data.get('total_questions', '?')} passed, {data.get('total_tokens', 0):,} tokens")
            except:
                pass
    else:
        lines.append("*No benchmark results yet*")
    
    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Evolutionary Training Loop")
    parser.add_argument("--phase", choices=["benchmark", "ingest", "report", "full"], default="full")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN — checking model health only")
        for model_key, endpoint in MODELS.items():
            health = check_model_health(endpoint)
            print(f"  {model_key}: {'🟢' if health else '🔴'}")
        return
    
    if args.phase in ("benchmark", "full"):
        benchmark_report = run_benchmark_phase()
    else:
        benchmark_report = {}
    
    if args.phase in ("ingest", "full"):
        ingest_report = run_ingest_phase()
    else:
        ingest_report = {}
    
    if args.phase in ("report", "full"):
        report = generate_report(benchmark_report, ingest_report)
        print(report)
        
        # Save report
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOGS_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md", "w") as f:
            f.write(report)


if __name__ == "__main__":
    main()
