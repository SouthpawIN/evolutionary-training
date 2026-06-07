#!/usr/bin/env python3
"""
OmniSenter Benchmark Suite

Runs comprehensive evaluations across multiple benchmarks:
- SWE-bench (software engineering)
- GPQA Diamond (reasoning)
- BFCL (function calling)
- Toolathlon (multi-step tool use)

Usage:
  python3 benchmark_omnisenter.py --model MODEL_PATH [--benchmarks all]
  python3 benchmark_omnisenter.py --model MODEL_PATH --benchmarks swe gpqa bfcl
  python3 benchmark_omnisenter.py --model MODEL_PATH --benchmark all --verbose
"""

import json, os, sys, time, subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "benchmarks" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Benchmark configurations
BENCHMARKS = {
    "swe": {
        "name": "SWE-bench",
        "description": "Software Engineering Benchmark",
        "script": str(BASE_DIR / "scripts" / "swe_benchmark.py"),
        "timeout": 3600,
        "required_model_size": "large",  # Requires substantial compute
    },
    "gpqa": {
        "name": "GPQA Diamond",
        "description": "Graduate-Level Google-Proof Q&A",
        "script": str(BASE_DIR / "scripts" / "gpqa_benchmark.py"),
        "timeout": 1800,
        "required_model_size": "medium",
    },
    "bfcl": {
        "name": "BFCL v4",
        "description": "Berkeley Function Calling Leaderboard",
        "script": str(BASE_DIR / "scripts" / "bfcl_benchmark.py"),
        "timeout": 1800,
        "required_model_size": "small",
    },
    "toolathlon": {
        "name": "Toolathlon",
        "description": "Multi-step Tool Use Benchmark",
        "script": str(BASE_DIR / "scripts" / "toolathlon_benchmark.py"),
        "timeout": 1800,
        "required_model_size": "small",
    },
}

def run_benchmark(benchmark_key: str, model_path: str, verbose: bool = False) -> Dict:
    """Run a specific benchmark and return results."""
    config = BENCHMARKS.get(benchmark_key)
    if not config:
        return {"error": f"Unknown benchmark: {benchmark_key}"}
    
    # Check if script exists
    script_path = Path(config["script"])
    if not script_path.exists():
        return {"error": f"Benchmark script not found: {script_path}"}
    
    print(f"\n{'='*60}")
    print(f"Running {config['name']}...")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    
    # Run benchmark
    cmd = [
        sys.executable, script_path,
        "--model", model_path,
        "--output-dir", str(RESULTS_DIR / benchmark_key),
    ]
    
    if verbose:
        cmd.append("--verbose")
    
    result = subprocess.run(
        cmd, 
        capture_output=True, 
        text=True, 
        timeout=config["timeout"],
    )
    
    elapsed = time.time() - start_time
    
    if result.returncode != 0:
        print(f"❌ {config['name']} failed:")
        print(result.stderr[:500])
        return {
            "benchmark": benchmark_key,
            "status": "error",
            "error": result.stderr[:500],
            "elapsed": elapsed,
        }
    
    # Parse results
    try:
        results_file = sorted(RESULTS_DIR.glob(f"{benchmark_key}/*.json"))[-1]
        with open(results_file) as f:
            benchmark_results = json.load(f)
    except:
        benchmark_results = {"status": "completed", "raw_output": result.stdout[:1000]}
    
    print(f"✅ {config['name']} completed in {elapsed:.0f}s")
    return {
        "benchmark": benchmark_key,
        "status": "completed",
        "results": benchmark_results,
        "elapsed": elapsed,
    }

def aggregate_results(model_path: str, benchmark_keys: List[str], verbose: bool = False) -> Dict:
    """Run multiple benchmarks and aggregate results."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = RESULTS_DIR / f"omnisenter_{timestamp}.json"
    
    all_results = {
        "model": model_path,
        "timestamp": timestamp,
        "results": {},
        "summary": {},
    }
    
    for key in benchmark_keys:
        all_results["results"][key] = run_benchmark(key, model_path, verbose)
    
    # Calculate summary
    summary = {
        "total_benchmarks": len(benchmark_keys),
        "completed": sum(1 for r in all_results["results"].values() if r.get("status") == "completed"),
        "errors": sum(1 for r in all_results["results"].values() if r.get("status") == "error"),
    }
    
    all_results["summary"] = summary
    
    # Save results
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"BENCHMARK SUMMARY")
    print(f"{'='*60}")
    print(f"  Model: {model_path}")
    print(f"  Benchmarks: {summary['completed']}/{summary['total_benchmarks']} completed")
    print(f"  Results saved to: {results_file}")
    print(f"{'='*60}")
    
    return all_results

def main():
    import argparse
    parser = argparse.ArgumentParser(description="OmniSenter Benchmark Suite")
    parser.add_argument("--model", required=True, help="Model path or HuggingFace ID")
    parser.add_argument("--benchmarks", nargs="*", default=["bfcl", "gpqa"], 
                       help="Benchmarks to run (all, swe, gpqa, bfcl, toolathlon)")
    parser.add_argument("--output-dir", default=None, help="Override output directory")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    # Determine which benchmarks to run
    if "all" in args.benchmarks:
        benchmark_keys = list(BENCHMARKS.keys())
    else:
        benchmark_keys = args.benchmarks
    
    # Validate benchmark keys
    for key in benchmark_keys:
        if key not in BENCHMARKS:
            print(f"❌ Unknown benchmark: {key}")
            print(f"   Available: {', '.join(BENCHMARKS.keys())}")
            sys.exit(1)
    
    # Run benchmarks
    results = aggregate_results(args.model, benchmark_keys, args.verbose)
    
    # Return appropriate exit code
    if results["summary"]["errors"] > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
