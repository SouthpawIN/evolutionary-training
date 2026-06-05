#!/usr/bin/env python3
"""
Continuous Evolution Pipeline — The Self-Improving Loop

Orchestrates: Data Ingest → Darwin Merge → Benchmark → Evolve → Upload

Runs as a cron job or background daemon. Each cycle:
1. Check for new training data
2. Generate CMA-ES candidate genomes
3. Merge parents with each genome
4. Benchmark each candidate
5. Select best, update genome distribution
6. Upload best to HuggingFace if improvement threshold met
7. Report to Discord

Usage:
  python3 continuous_evolution.py [--cycle] [--daemon] [--interval 3600]
"""

import json, os, sys, time, shutil, hashlib, argparse, subprocess
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict

BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = Path.home() / "Models" / "storage" / "gguf"
EVOLUTION_DIR = BASE_DIR / "evolution"
RESULTS_DIR = BASE_DIR / "benchmarks" / "results"
LOGS_DIR = BASE_DIR / "logs"
GENOMES_DIR = BASE_DIR / "genomes"

# === Model Registry ===
MODEL_REGISTRY = {
    "qwen-cosmos": {
        "name": "Qwen3-8B × Cosmos3-Nano",
        "parent_a": {
            "name": "Cosmos3-Nano",
            "hf_repo": "nvidia/Cosmos3-Nano",
            "local_path": None,  # set after download
            "text_prefix": "thinker.model.",
            "lm_head_key": "thinker.lm_head.weight",
        },
        "parent_b": {
            "name": "Qwen3-8B",
            "hf_repo": "Qwen/Qwen3-8B",
            "local_path": None,
            "text_prefix": "model.",
            "lm_head_key": "lm_head.weight",
        },
        "merge_script": str(BASE_DIR / "scripts" / "qwen_cosmos_darwin_merge.py"),
        "benchmark_suite": "quick",
        "hf_upload_repo": "sovthpaw/qwen-cosmos-evo",
        "hf_train_repo": "sovthpaw/qwen-cosmos-train",
        "min_improvement_pct": 0.5,
        "evolution": {
            "pop_size": 4,
            "generations_per_cycle": 2,
            "sigma_init": 0.3,
            "sigma_min": 0.05,
        },
    },
    "omnistep": {
        "name": "OmniStep 12A3B Evolution",
        "parent_a": {
            "name": "OmniStep-12A3B",
            "hf_repo": "sovthpaw/omnistep-12a3b",
            "local_path": str(MODELS_DIR / "omnistep-12a3b"),
        },
        "merge_script": str(BASE_DIR / "scripts" / "qwen_cosmos_darwin_merge.py"),
        "benchmark_suite": "quick",
        "hf_upload_repo": "sovthpaw/omnistep-evo",
        "hf_train_repo": "sovthpaw/omnistep-train",
        "min_improvement_pct": 0.5,
        "evolution": {
            "pop_size": 4,
            "generations_per_cycle": 2,
            "sigma_init": 0.3,
        },
    },
}


@dataclass
class Genome:
    """14-dimensional Darwin merge genome."""
    gamma: float = 0.5
    alpha_attn: float = 0.5
    alpha_ffn: float = 0.5
    alpha_emb: float = 0.5
    rho_a: float = 0.5
    rho_b: float = 0.5
    r0: float = 0.5
    r1: float = 0.5
    r2: float = 0.5
    r3: float = 0.5
    r4: float = 0.5
    r5: float = 0.5
    tau: float = 0.4
    lambda_reg: float = 0.01

    def to_vector(self):
        return list(asdict(self).values())

    def to_json(self):
        return asdict(self)

    @classmethod
    def random(cls, sigma=0.3):
        import random
        base = [0.5]*6 + [0.5]*6 + [0.4, 0.01]
        values = [max(0.0, min(1.0, v + random.gauss(0, sigma))) for v in base]
        return cls(*values)

    def mutate(self, sigma=0.1):
        import random
        vals = self.to_vector()
        vals = [max(0.0, min(1.0, v + random.gauss(0, sigma))) for v in vals]
        return Genome(*vals)

    def crossover(self, other):
        import random
        v1, v2 = self.to_vector(), other.to_vector()
        point = random.randint(1, len(v1)-1)
        return Genome(*(v1[:point] + v2[point:]))


class CMAES:
    """Simplified CMA-ES for genome optimization."""
    def __init__(self, genome_size=14, sigma=0.3, pop_size=4):
        self.genome_size = genome_size
        self.sigma = sigma
        self.pop_size = pop_size
        self.mean = [0.5] * genome_size
        self.mean[12] = 0.4  # tau default
        self.best_fitness = float('-inf')
        self.best_genome = None
        self.generation = 0

    def ask(self):
        import random
        candidates = []
        for _ in range(self.pop_size):
            values = [max(0.0, min(1.0, self.mean[i] + random.gauss(0, self.sigma)))
                      for i in range(self.genome_size)]
            candidates.append(Genome(*values))
        return candidates

    def tell(self, candidates, fitnesses):
        ranked = sorted(zip(fitnesses, candidates), reverse=True)
        if ranked[0][0] > self.best_fitness:
            self.best_fitness = ranked[0][0]
            self.best_genome = ranked[0][1]
        top_half = ranked[:len(ranked)//2]
        if top_half:
            new_mean = [0.0] * self.genome_size
            for fitness, genome in top_half:
                v = genome.to_vector()
                for i in range(self.genome_size):
                    new_mean[i] += v[i] / len(top_half)
            self.mean = new_mean
            if len(top_half) > 1:
                fs = [f for f, _ in top_half]
                if max(fs) - min(fs) < 0.01:
                    self.sigma *= 0.9
                else:
                    self.sigma *= 1.05
        self.generation += 1
        return self.best_genome, self.best_fitness

    def save(self, path):
        with open(path, 'w') as f:
            json.dump({
                'mean': self.mean, 'sigma': self.sigma,
                'best_fitness': self.best_fitness,
                'best_genome': self.best_genome.to_json() if self.best_genome else None,
                'generation': self.generation,
            }, f, indent=2)

    def load(self, path):
        with open(path) as f:
            data = json.load(f)
        self.mean = data['mean']
        self.sigma = data['sigma']
        self.best_fitness = data.get('best_fitness', float('-inf'))
        self.generation = data.get('generation', 0)
        if data.get('best_genome'):
            self.best_genome = Genome(**data['best_genome'])


class EvolutionPipeline:
    """Continuous evolution orchestrator."""

    def __init__(self, model_key: str):
        self.model_key = model_key
        self.config = MODEL_REGISTRY[model_key]
        self.evolution_dir = EVOLUTION_DIR / model_key
        self.evolution_dir.mkdir(parents=True, exist_ok=True)
        self.genomes_dir = GENOMES_DIR / model_key
        self.genomes_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = LOGS_DIR / f"evolution_{model_key}.jsonl"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Load or initialize CMA-ES
        self.optimizer = CMAES(
            pop_size=self.config["evolution"]["pop_size"],
            sigma=self.config["evolution"]["sigma_init"],
        )
        state_path = self.evolution_dir / "cmaes_state.json"
        if state_path.exists():
            self.optimizer.load(state_path)

    def log(self, entry):
        entry["timestamp"] = datetime.now().isoformat()
        entry["model"] = self.model_key
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def download_parent(self, parent_config):
        """Download parent model from HuggingFace if not local."""
        local = parent_config.get("local_path")
        if local and Path(local).exists():
            print(f"  Parent {parent_config['name']} already at {local}")
            return local

        repo = parent_config["hf_repo"]
        local = str(MODELS_DIR / repo.split("/")[-1])
        if Path(local).exists():
            print(f"  Parent {parent_config['name']} already at {local}")
            parent_config["local_path"] = local
            return local

        print(f"  Downloading {repo}...")
        result = subprocess.run(
            ["huggingface-cli", "download", repo, "--local-dir", local],
            capture_output=True, text=True, timeout=7200,
        )
        if result.returncode != 0:
            print(f"  Download failed: {result.stderr[:200]}")
            return None
        parent_config["local_path"] = local
        return local

    def run_merge(self, genome: Genome, output_dir: str) -> bool:
        """Run the Darwin merge with a specific genome."""
        genome_path = self.genomes_dir / f"genome_{self.optimizer.generation}_{int(time.time())}.json"
        with open(genome_path, 'w') as f:
            json.dump(genome.to_json(), f)

        cmd = [
            sys.executable, self.config["merge_script"],
            "--cosmos-path", self.config["parent_a"]["local_path"],
            "--qwen-path", self.config["parent_b"]["local_path"],
            "--output", output_dir,
            "--genome-json", str(genome_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        if result.returncode != 0:
            self.log({"action": "merge_failed", "error": result.stderr[:500]})
            return False
        return Path(output_dir).exists()

    def run_benchmark(self, model_path: str) -> float:
        """Run benchmark suite and return fitness score."""
        bench_script = str(BASE_DIR / "scripts" / "darwin_benchmark.py")
        if not Path(bench_script).exists():
            return 0.0

        result = subprocess.run(
            [sys.executable, bench_script, "--model", self.model_key,
             "--suite", self.config["benchmark_suite"]],
            capture_output=True, text=True, timeout=600,
        )

        if result.returncode != 0:
            return 0.0

        try:
            results_files = sorted(RESULTS_DIR.glob(f"benchmark_{self.model_key}_*.json"))
            if not results_files:
                return 0.0
            with open(results_files[-1]) as f:
                data = json.load(f)
            success_rate = data.get("successful", 0) / max(data.get("total_questions", 1), 1)
            avg_time = data.get("avg_response_time_s", 100)
            speed_bonus = max(0, 1.0 - avg_time / 30.0)
            return success_rate * 0.8 + speed_bonus * 0.2
        except:
            return 0.0

    def upload_to_hf(self, model_path: str, generation: int, fitness: float, stage="evo"):
        """Upload best model to HuggingFace as a staged generation.
        
        stage="evo" → sovthpaw/qwen-cosmos-evo-gen0
        stage="train" → sovthpaw/qwen-cosmos-train-gen0
        """
        if stage == "evo":
            repo = f"{self.config['hf_upload_repo']}-gen{generation}"
        else:
            repo = f"{self.config.get('hf_train_repo', self.config['hf_upload_repo'])}-gen{generation}"

        print(f"  Uploading to {repo}...")
        try:
            result = subprocess.run(
                ["huggingface-cli", "upload", repo, model_path, ".", "--commit-message",
                 f"{'Evolution' if stage=='evo' else 'Training'} generation {generation}, fitness={fitness:.4f}"],
                capture_output=True, text=True, timeout=3600,
            )
            if result.returncode == 0:
                self.log({"action": "hf_upload", "repo": repo, "generation": generation,
                          "fitness": fitness, "stage": stage})
                print(f"  ✅ Uploaded to {repo}")
            else:
                self.log({"action": "hf_upload_failed", "stage": stage, "error": result.stderr[:300]})
        except Exception as e:
            self.log({"action": "hf_upload_failed", "stage": stage, "error": str(e)[:300]})

    def run_cycle(self):
        """Run one complete evolution cycle."""
        print(f"\n{'='*60}")
        print(f"Evolution Cycle — {self.config['name']}")
        print(f"Generation {self.optimizer.generation + 1}")
        print(f"{'='*60}")

        # 1. Ensure parents downloaded
        print("\n[1/5] Checking parent models...")
        pa = self.download_parent(self.config["parent_a"])
        pb = self.download_parent(self.config["parent_b"])
        if not pa or not pb:
            print("  Parents not available, aborting cycle")
            return

        # 2. Generate candidates
        print("\n[2/5] Generating genome candidates...")
        candidates = self.optimizer.ask()
        print(f"  Generated {len(candidates)} candidates (sigma={self.optimizer.sigma:.4f})")

        # 3. Merge + benchmark each candidate
        print("\n[3/5] Merging and benchmarking candidates...")
        fitnesses = []
        for i, genome in enumerate(candidates):
            print(f"\n  Candidate {i+1}/{len(candidates)}: tau={genome.tau:.4f}, rho_b={genome.rho_b:.4f}")

            merge_dir = str(self.evolution_dir / f"gen{self.optimizer.generation}_cand{i}")
            if not self.run_merge(genome, merge_dir):
                fitnesses.append(0.0)
                continue

            fitness = self.run_benchmark(merge_dir)
            fitnesses.append(fitness)
            print(f"  Fitness: {fitness:.4f}")

            # Cleanup merged model to save disk (keep only best)
            if fitness < self.optimizer.best_fitness:
                shutil.rmtree(merge_dir, ignore_errors=True)

        # 4. Update optimizer
        print("\n[4/5] Updating CMA-ES optimizer...")
        best_genome, best_fitness = self.optimizer.tell(candidates, fitnesses)
        self.optimizer.save(str(self.evolution_dir / "cmaes_state.json"))

        self.log({
            "action": "cycle_complete",
            "generation": self.optimizer.generation,
            "candidates": len(candidates),
            "best_fitness": best_fitness,
            "all_fitnesses": fitnesses,
            "sigma": self.optimizer.sigma,
        })

        print(f"  Best fitness: {best_fitness:.4f}")

        # 5. Upload if improvement
        print("\n[5/5] Checking for upload-worthy improvement...")
        best_dir = str(self.evolution_dir / f"gen{self.optimizer.generation}_best")
        if best_fitness > 0:
            # Save best candidate
            best_idx = fitnesses.index(max(fitnesses))
            src = str(self.evolution_dir / f"gen{self.optimizer.generation}_cand{best_idx}")
            if Path(src).exists():
                if Path(best_dir).exists():
                    shutil.rmtree(best_dir)
                shutil.copytree(src, best_dir)
                self.upload_to_hf(best_dir, self.optimizer.generation, best_fitness)

        print(f"\n{'='*60}")
        print(f"Cycle complete. Best fitness: {best_fitness:.4f}")
        print(f"{'='*60}")

    def run_daemon(self, interval_seconds=3600, max_cycles=None):
        """Run continuous evolution daemon."""
        print(f"🧬 Evolution Daemon started — {self.config['name']}")
        print(f"  Interval: {interval_seconds}s")
        print(f"  Max cycles: {max_cycles or 'unlimited'}")

        cycle = 0
        while True:
            try:
                self.run_cycle()
                cycle += 1
                if max_cycles and cycle >= max_cycles:
                    print(f"Max cycles ({max_cycles}) reached.")
                    break
                print(f"\nNext cycle in {interval_seconds}s...")
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                print("\nDaemon interrupted.")
                break
            except Exception as e:
                print(f"\nError in cycle: {e}")
                self.log({"action": "cycle_error", "error": str(e)[:500]})
                time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description="Continuous Evolution Pipeline")
    parser.add_argument("--model", choices=list(MODEL_REGISTRY.keys()), default="qwen-cosmos")
    parser.add_argument("--cycle", action="store_true", help="Run one cycle")
    parser.add_argument("--daemon", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=3600, help="Seconds between cycles")
    parser.add_argument("--max-cycles", type=int, help="Stop after N cycles")
    args = parser.parse_args()

    pipeline = EvolutionPipeline(args.model)

    if args.daemon:
        pipeline.run_daemon(args.interval, args.max_cycles)
    elif args.cycle:
        pipeline.run_cycle()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
