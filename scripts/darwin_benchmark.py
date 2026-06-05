#!/usr/bin/env python3
"""
Darwin Family Benchmark Runner
Runs GPQA-style evaluation against local Darwin-28B-REASON model.

Usage:
  python3 darwin_benchmark.py [--model MODEL_NAME] [--suite SUITE] [--output DIR]

Suites:
  - quick: 10-question smoke test
  - standard: 50-question GPQA subset
  - full: all available benchmarks
"""

import json, os, sys, time, argparse
from pathlib import Path
from datetime import datetime

# === Configuration ===
BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "benchmarks" / "results"
CONFIGS_DIR = BASE_DIR / "configs"

# Model endpoints
MODELS = {
    "darwin-main": {
        "endpoint": "http://127.0.0.1:8080/v1",
        "model": "Darwin-28B-REASON",
        "description": "Darwin-28B-REASON Q4_K_M on GPU 0 (262K ctx)",
        "quant": "Q4_K_M",
        "gpu": 0,
    },
    "apex-mtp-aux": {
        "endpoint": "http://127.0.0.1:8081/v1",
        "model": "Qwen3.6-35B-A3B-APEX-MTP",
        "description": "APEX-MTP I-Compact on GPU 1 (1M ctx, CPU MoE, MTP draft)",
        "quant": "I-Compact",
        "gpu": 1,
    },
}

# === Benchmark Questions ===
# GPQA-style reasoning questions for Darwin evaluation
BENCHMARK_QUESTIONS = {
    "physics": [
        {
            "id": "phys-001",
            "question": "A particle moves along x(t) = t³ − 6t² + 9t. Find when it is at rest and classify the motion.",
            "domain": "classical_mechanics",
            "difficulty": "undergraduate",
        },
        {
            "id": "phys-002",
            "question": "Calculate the energy levels of a hydrogen atom using the Bohr model. Express in terms of the principal quantum number n.",
            "domain": "quantum_mechanics",
            "difficulty": "undergraduate",
        },
        {
            "id": "phys-003",
            "question": "A spherical capacitor has inner radius a and outer radius b. Derive the capacitance and the energy stored when charged to voltage V.",
            "domain": "electrodynamics",
            "difficulty": "graduate",
        },
    ],
    "chemistry": [
        {
            "id": "chem-001",
            "question": "Predict the product and mechanism of the reaction between 2-bromo-2-methylpropane and sodium hydroxide in aqueous solution.",
            "domain": "organic_chemistry",
            "difficulty": "undergraduate",
        },
        {
            "id": "chem-002",
            "question": "Calculate the standard cell potential for a galvanic cell made from Zn/Zn²⁺ and Cu/Cu²⁺ half-cells. Show your work.",
            "domain": "physical_chemistry",
            "difficulty": "undergraduate",
        },
    ],
    "mathematics": [
        {
            "id": "math-001",
            "question": "Prove that the sum of the first n odd numbers equals n². Use mathematical induction.",
            "domain": "number_theory",
            "difficulty": "undergraduate",
        },
        {
            "id": "math-002",
            "question": "Find the eigenvalues and eigenvectors of the matrix [[2,1],[1,2]]. Show all steps.",
            "domain": "linear_algebra",
            "difficulty": "undergraduate",
        },
        {
            "id": "math-003",
            "question": "Evaluate the contour integral ∮(z²+1)/(z²-1) dz around the unit circle |z|=2 using the residue theorem.",
            "domain": "complex_analysis",
            "difficulty": "graduate",
        },
    ],
    "biology": [
        {
            "id": "bio-001",
            "question": "Explain the mechanism of CRISPR-Cas9 gene editing, including guide RNA design, PAM recognition, and double-strand break repair pathways.",
            "domain": "molecular_biology",
            "difficulty": "graduate",
        },
    ],
    "computer_science": [
        {
            "id": "cs-001",
            "question": "Implement a function to find the longest common subsequence of two strings. Analyze the time and space complexity.",
            "domain": "algorithms",
            "difficulty": "undergraduate",
        },
        {
            "id": "cs-002",
            "question": "Explain the difference between a mutex and a semaphore. When would you use each? Provide a deadlock scenario and how to prevent it.",
            "domain": "systems",
            "difficulty": "undergraduate",
        },
    ],
}

SUITES = {
    "quick": ["phys-001", "chem-001", "math-001", "bio-001", "cs-001"],
    "standard": None,  # all questions
    "full": None,  # all questions + extended eval
}


def get_all_questions(suite="standard"):
    """Get questions for the requested suite."""
    all_q = []
    for domain, questions in BENCHMARK_QUESTIONS.items():
        for q in questions:
            if suite == "quick":
                if q["id"] in SUITES["quick"]:
                    all_q.append(q)
            else:
                all_q.append(q)
    return all_q


def query_model(endpoint, model_name, question, max_tokens=2048, temperature=0.1):
    """Send a question to the model and get a response."""
    import urllib.request

    payload = json.dumps({
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a graduate-level STEM reasoning assistant. Show your work step by step. Be precise and rigorous."},
            {"role": "user", "content": question},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }).encode()

    req = urllib.request.Request(
        f"{endpoint}/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    try:
        start = time.time()
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            elapsed = time.time() - start
            content = result["choices"][0]["message"]["content"]
            tokens = result.get("usage", {})
            return {
                "success": True,
                "content": content,
                "elapsed_s": round(elapsed, 2),
                "prompt_tokens": tokens.get("prompt_tokens", 0),
                "completion_tokens": tokens.get("completion_tokens", 0),
                "total_tokens": tokens.get("total_tokens", 0),
            }
    except Exception as e:
        return {"success": False, "error": str(e), "elapsed_s": 0}


def run_benchmark(model_key, suite="standard"):
    """Run a full benchmark suite against a model."""
    model = MODELS[model_key]
    questions = get_all_questions(suite)

    print(f"\n{'='*60}")
    print(f"Benchmark: {model['description']}")
    print(f"Suite: {suite} ({len(questions)} questions)")
    print(f"{'='*60}\n")

    results = []
    for i, q in enumerate(questions):
        print(f"[{i+1}/{len(questions)}] {q['id']}: {q['question'][:80]}...")
        result = query_model(model["endpoint"], model["model"], q["question"])
        result["question_id"] = q["id"]
        result["domain"] = q["domain"]
        result["difficulty"] = q["difficulty"]
        results.append(result)

        if result["success"]:
            print(f"  ✓ {result['elapsed_s']}s, {result['total_tokens']} tokens")
        else:
            print(f"  ✗ Error: {result['error'][:80]}")

    # Summary
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    total_tokens = sum(r["total_tokens"] for r in successful)
    avg_time = sum(r["elapsed_s"] for r in successful) / max(len(successful), 1)

    summary = {
        "model": model_key,
        "model_description": model["description"],
        "suite": suite,
        "timestamp": datetime.now().isoformat(),
        "total_questions": len(questions),
        "successful": len(successful),
        "failed": len(failed),
        "total_tokens": total_tokens,
        "avg_response_time_s": round(avg_time, 2),
        "results": results,
    }

    # Save results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = RESULTS_DIR / f"benchmark_{model_key}_{suite}_{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Results: {len(successful)}/{len(questions)} successful")
    print(f"Total tokens: {total_tokens:,}")
    print(f"Avg response time: {avg_time:.1f}s")
    print(f"Saved to: {output_path}")
    print(f"{'='*60}")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Darwin Family Benchmark Runner")
    parser.add_argument("--model", choices=list(MODELS.keys()), default="darwin-main")
    parser.add_argument("--suite", choices=list(SUITES.keys()), default="quick")
    parser.add_argument("--all-models", action="store_true", help="Run against all models")
    args = parser.parse_args()

    if args.all_models:
        for model_key in MODELS:
            run_benchmark(model_key, args.suite)
    else:
        run_benchmark(args.model, args.suite)


if __name__ == "__main__":
    main()
