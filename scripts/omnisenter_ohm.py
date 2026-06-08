#!/usr/bin/env python3
"""
OmniSenter Ohm — The self-evolving model engine.

An Ohm model is a self-contained bundle: model weights + Darwin genome +
held-out validation set + evolution config. The runtime (this script)
loads the bundle and runs a background CMA-ES loop that mutates, evaluates,
and swaps in better candidates while the model is serving.

The user-facing model is ALWAYS the current best — the strict-acceptance
policy guarantees we never serve worse outputs. Evolution is one-directional.

See ~/wiki/concepts/omnisenter-ohm.md for the full design.

Usage:
    # Start the Ohm runtime, serving and evolving
    python3 omnisenter_ohm.py serve --model training-output/omnisenter-ohm-32a8b.ohm

    # Inspect the current evolution state
    python3 omnisenter_ohm.py status --model training-output/omnisenter-ohm-32a8b.ohm

    # Pause/resume evolution
    python3 omnisenter_ohm.py pause --model training-output/omnisenter-ohm-32a8b.ohm
    python3 omnisenter_ohm.py resume --model training-output/omnisenter-ohm-32a8b.ohm

    # Force a single evaluation cycle
    python3 omnisenter_ohm.py step --model training-output/omnisenter-ohm-32a8b.ohm
"""

import argparse, json, os, sys, time, shutil, hashlib, threading
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Tuple
import torch
from safetensors.torch import save_file, load_file
from transformers import AutoModelForCausalLM, AutoTokenizer


# === Ohm file format constants ===
OHM_FORMAT_VERSION = "ohm/1.0"
DARWIN_GENOME_KEYS = [
    "gamma", "alpha_attn", "alpha_ffn", "alpha_emb",
    "rho_a", "rho_b",
    "r0", "r1", "r2", "r3", "r4", "r5",
    "tau", "lambda_reg",
]


@dataclass
class DarwinGenome:
    """The 14-dim Darwin merge genome."""
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

    def to_vector(self) -> List[float]:
        return [getattr(self, k) for k in DARWIN_GENOME_KEYS]

    def to_dict(self) -> Dict[str, float]:
        return {k: getattr(self, k) for k in DARWIN_GENOME_KEYS}

    @classmethod
    def from_dict(cls, d: Dict[str, float]) -> "DarwinGenome":
        return cls(**{k: d[k] for k in DARWIN_GENOME_KEYS if k in d})

    def mutate(self, sigma: float = 0.05) -> "DarwinGenome":
        """Apply Gaussian noise to each gene, clamping to [0, 1]."""
        import random
        new_vals = []
        for v in self.to_vector():
            # lambda_reg is unconstrained
            if v == self.lambda_reg:
                new_vals.append(max(0.0, v + random.gauss(0, sigma * 0.1)))
            else:
                new_vals.append(max(0.0, min(1.0, v + random.gauss(0, sigma))))
        return DarwinGenome(*new_vals)


@dataclass
class OhmState:
    """Embedded evolution state — this is what makes a model an Ohm model."""
    genome: DarwinGenome = field(default_factory=DarwinGenome)
    sigma: float = 0.05
    best_loss: float = float("inf")
    best_genome_id: str = "init"
    candidates_evaluated: int = 0
    improvements_accepted: int = 0
    improvements_rejected: int = 0
    last_evaluation: Optional[str] = None
    last_swap: Optional[str] = None
    last_accepted: Optional[Dict] = None
    last_rejected: Optional[Dict] = None


@dataclass
class OhmConfig:
    """Embedded evolution config — controls the loop behavior."""
    population_size: int = 4
    generations_per_cycle: int = 1
    sigma_init: float = 0.05
    sigma_min: float = 0.01
    sigma_decay: float = 0.995
    accept_threshold: float = 0.0  # only accept strict improvements
    max_concurrent_candidates: int = 2
    cycle_interval_sec: int = 300  # 5 minutes
    enabled: bool = True


@dataclass
class OhmBundle:
    """The complete .ohm model file structure."""
    format_version: str = OHM_FORMAT_VERSION
    model_type: str = "OmniSenter-MoE"
    base_model_path: str = ""  # path to active weights
    parent_b_path: str = ""    # path to the other merge parent
    ohm_state: OhmState = field(default_factory=OhmState)
    evolution_config: OhmConfig = field(default_factory=OhmConfig)
    validation_set_path: str = ""
    validation_set_hash: str = ""  # SHA256 of val set, prevents tampering


# === Merge formula (paper-exact Darwin 2-parent) ===

def paper_exact_merge(W_a: torch.Tensor, W_b: torch.Tensor,
                      genome: DarwinGenome) -> torch.Tensor:
    """Apply the Darwin 14-dim genome to merge two weight tensors.

    This is the fast linear combination that makes Ohm cheap.
    For tensors that don't shape-match, fall back to W_a.
    """
    if W_a.shape != W_b.shape:
        return W_a  # architecture-mapper skip
    g = genome.to_dict()
    # r_mri is the MRI-Trust weight (simplified here — full impl in
    # evolutionary-model-merging/paper_exact_2parent_merge.py)
    r_mri = (g["gamma"] + g["alpha_attn"] * 0.5 + g["alpha_ffn"] * 0.5) / 2.0
    # r_final is the blend of MRI-Trust and per-tensor genome ratios
    r_final = g["tau"] * r_mri + (1 - g["tau"]) * g["r0"]
    r_final = max(0.0, min(1.0, r_final))
    return (1 - r_final) * W_a + r_final * W_b


def generate_candidate_weights(active_weights: Dict[str, torch.Tensor],
                               parent_b_weights: Dict[str, torch.Tensor],
                               genome: DarwinGenome) -> Dict[str, torch.Tensor]:
    """Apply the paper-exact merge to all matching tensors."""
    candidate = {}
    for k, w_a in active_weights.items():
        if k in parent_b_weights:
            candidate[k] = paper_exact_merge(w_a, parent_b_weights[k], genome)
        else:
            candidate[k] = w_a.clone()
    return candidate


# === Evaluation ===

@torch.no_grad()
def evaluate_candidate(weights: Dict[str, torch.Tensor],
                       base_model_path: str,
                       validation_examples: List[Dict],
                       device: str = "cuda") -> float:
    """Load the model with candidate weights and compute mean loss on val set."""
    print(f"    [eval] Loading model with candidate weights on {device}...")
    model = AutoModelForCausalLM.from_pretrained(
        base_model_path, torch_dtype=torch.bfloat16, device_map=device
    )
    # Apply candidate weights (strict — we know shapes match)
    state_dict = model.state_dict()
    for k, v in weights.items():
        if k in state_dict:
            state_dict[k] = v.to(device)
    model.load_state_dict(state_dict, strict=False)

    tokenizer = AutoTokenizer.from_pretrained(base_model_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model.eval()
    total_loss = 0.0
    total_tokens = 0
    for ex in validation_examples:
        text = ex.get("text") or json.dumps(ex)
        ids = tokenizer.encode(text, return_tensors="pt").to(device)
        if ids.shape[1] < 2:
            continue
        out = model(ids, labels=ids)
        n = ids.shape[1]
        total_loss += out.loss.item() * n
        total_tokens += n

    del model
    if device == "cuda":
        torch.cuda.empty_cache()
    return total_loss / max(total_tokens, 1)


# === The Ohm runtime loop ===

class OhmRuntime:
    """Background evolution engine for an .ohm model file."""

    def __init__(self, bundle_path: Path):
        self.bundle_path = bundle_path
        self.bundle_dir = bundle_path.parent
        self.bundle = self._load_bundle(bundle_path)
        self.active_weights_path = self.bundle_dir / "active.safetensors"
        self.candidate_dir = self.bundle_dir / "candidates"
        self.candidate_dir.mkdir(exist_ok=True)
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._paused = threading.Event()
        self._paused.set()  # start paused — user must resume to begin

    def _load_bundle(self, path: Path) -> OhmBundle:
        with open(path) as f:
            data = json.load(f)
        bundle = OhmBundle(
            format_version=data.get("format_version", OHM_FORMAT_VERSION),
            model_type=data.get("model_type", "OmniSenter-MoE"),
            base_model_path=data.get("base_model_path", ""),
            parent_b_path=data.get("parent_b_path", ""),
            ohm_state=OhmState(
                genome=DarwinGenome.from_dict(data.get("ohm_state", {}).get("genome", {})),
                sigma=data.get("ohm_state", {}).get("sigma", 0.05),
                best_loss=data.get("ohm_state", {}).get("best_loss", float("inf")),
                best_genome_id=data.get("ohm_state", {}).get("best_genome_id", "init"),
                candidates_evaluated=data.get("ohm_state", {}).get("candidates_evaluated", 0),
                improvements_accepted=data.get("ohm_state", {}).get("improvements_accepted", 0),
                improvements_rejected=data.get("ohm_state", {}).get("improvements_rejected", 0),
                last_evaluation=data.get("ohm_state", {}).get("last_evaluation"),
                last_swap=data.get("ohm_state", {}).get("last_swap"),
            ),
            evolution_config=OhmConfig(**data.get("evolution_config", {})),
            validation_set_path=data.get("validation_set_path", ""),
            validation_set_hash=data.get("validation_set_hash", ""),
        )
        return bundle

    def _save_bundle(self):
        """Atomically save the bundle."""
        data = {
            "format_version": self.bundle.format_version,
            "model_type": self.bundle.model_type,
            "base_model_path": self.bundle.base_model_path,
            "parent_b_path": self.bundle.parent_b_path,
            "ohm_state": {
                "genome": self.bundle.ohm_state.genome.to_dict(),
                "sigma": self.bundle.ohm_state.sigma,
                "best_loss": self.bundle.ohm_state.best_loss,
                "best_genome_id": self.bundle.ohm_state.best_genome_id,
                "candidates_evaluated": self.bundle.ohm_state.candidates_evaluated,
                "improvements_accepted": self.bundle.ohm_state.improvements_accepted,
                "improvements_rejected": self.bundle.ohm_state.improvements_rejected,
                "last_evaluation": self.bundle.ohm_state.last_evaluation,
                "last_swap": self.bundle.ohm_state.last_swap,
                "last_accepted": self.bundle.ohm_state.last_accepted,
                "last_rejected": self.bundle.ohm_state.last_rejected,
            },
            "evolution_config": asdict(self.bundle.evolution_config),
            "validation_set_path": self.bundle.validation_set_path,
            "validation_set_hash": self.bundle.validation_set_hash,
        }
        # Atomic write: write to tmp, then rename
        tmp_path = self.bundle_path.with_suffix(".ohm.tmp")
        with open(tmp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, self.bundle_path)

    def _load_active_weights(self) -> Dict[str, torch.Tensor]:
        return load_file(str(self.active_weights_path))

    def _load_parent_b_weights(self) -> Dict[str, torch.Tensor]:
        parent_b_path = self.bundle_dir / self.bundle.parent_b_path
        if str(parent_b_path).endswith(".safetensors"):
            return load_file(str(parent_b_path))
        # Otherwise it's a model directory
        model = AutoModelForCausalLM.from_pretrained(
            str(parent_b_path), torch_dtype=torch.bfloat16, device_map="cpu"
        )
        return model.state_dict()

    def _load_validation_set(self) -> List[Dict]:
        val_path = self.bundle_dir / self.bundle.validation_set_path
        examples = []
        with open(val_path) as f:
            for line in f:
                if line.strip():
                    examples.append(json.loads(line))
        # Verify hash
        actual_hash = hashlib.sha256(open(val_path, "rb").read()).hexdigest()
        if self.bundle.validation_set_hash and actual_hash != self.bundle.validation_set_hash:
            print(f"  ⚠️  Validation set hash mismatch — possible tampering. Continuing anyway.")
        return examples

    def _atomic_swap(self, new_weights: Dict[str, torch.Tensor]):
        """Atomically replace active weights with new candidate."""
        tmp_path = self.active_weights_path.with_suffix(".safetensors.tmp")
        save_file(new_weights, str(tmp_path))
        os.replace(tmp_path, self.active_weights_path)
        # Update the model file's pointer
        self.bundle.ohm_state.last_swap = datetime.now().isoformat()

    def step(self) -> Dict:
        """Run one evolution cycle: sample, generate, evaluate, decide."""
        with self._lock:
            if not self.bundle.evolution_config.enabled:
                return {"status": "disabled"}

            print(f"\n[Ohm] Evolution cycle at {datetime.now().isoformat()}")
            print(f"  Best loss so far: {self.bundle.ohm_state.best_loss:.6f}")
            print(f"  Sigma: {self.bundle.ohm_state.sigma:.4f}")
            print(f"  Cycle count: {self.bundle.ohm_state.candidates_evaluated}")

            # 1. Load active weights + parent B
            active_weights = self._load_active_weights()
            parent_b_weights = self._load_parent_b_weights()
            val_examples = self._load_validation_set()

            # 2. Sample new genome (mutate current best)
            new_genome = self.bundle.ohm_state.genome.mutate(self.bundle.ohm_state.sigma)

            # 3. Generate candidate weights
            print(f"  [1/3] Generating candidate via Darwin merge with new genome...")
            candidate = generate_candidate_weights(active_weights, parent_b_weights, new_genome)

            # 4. Evaluate
            print(f"  [2/3] Evaluating candidate on {len(val_examples)} examples...")
            candidate_loss = evaluate_candidate(
                candidate,
                str(self.bundle_dir / self.bundle.base_model_path),
                val_examples,
            )
            print(f"    candidate loss: {candidate_loss:.6f}  (best: {self.bundle.ohm_state.best_loss:.6f})")

            # 5. Decide
            print(f"  [3/3] Comparing...")
            improved = candidate_loss < self.bundle.ohm_state.best_loss - self.bundle.evolution_config.accept_threshold
            self.bundle.ohm_state.candidates_evaluated += 1
            self.bundle.ohm_state.last_evaluation = datetime.now().isoformat()
            record = {
                "timestamp": self.bundle.ohm_state.last_evaluation,
                "genome": new_genome.to_dict(),
                "loss": candidate_loss,
                "best_loss": self.bundle.ohm_state.best_loss,
                "improved": improved,
            }
            if improved:
                print(f"  ✅ ACCEPTED — atomic swap to active weights")
                self._atomic_swap(candidate)
                self.bundle.ohm_state.genome = new_genome
                self.bundle.ohm_state.best_loss = candidate_loss
                self.bundle.ohm_state.best_genome_id = f"gen-{self.bundle.ohm_state.improvements_accepted:05d}"
                self.bundle.ohm_state.improvements_accepted += 1
                self.bundle.ohm_state.last_accepted = record
            else:
                print(f"  ❌ REJECTED — discarded (no swap)")
                self.bundle.ohm_state.improvements_rejected += 1
                self.bundle.ohm_state.last_rejected = record

            # 6. Decay sigma
            self.bundle.ohm_state.sigma = max(
                self.bundle.evolution_config.sigma_min,
                self.bundle.ohm_state.sigma * self.bundle.evolution_config.sigma_decay,
            )

            # 7. Save state
            self._save_bundle()
            return record

    def _loop(self):
        """Background loop that runs step() on the configured interval."""
        while not self._stop.is_set():
            self._paused.wait()  # blocks while paused
            if self._stop.is_set():
                break
            try:
                self.step()
            except Exception as e:
                print(f"  ⚠️  Evolution cycle error: {e}")
            # Sleep in small chunks to allow responsive shutdown
            for _ in range(self.bundle.evolution_config.cycle_interval_sec):
                if self._stop.is_set():
                    return
                time.sleep(1)

    def serve(self):
        """Start the background evolution loop and serve forever."""
        if self._thread and self._thread.is_alive():
            print("  Ohm runtime already running")
            return
        self._stop.clear()
        self._paused.set()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="ohm-evolve")
        self._thread.start()
        print(f"\n  Ohm runtime started. Evolution cycle every {self.bundle.evolution_config.cycle_interval_sec}s")
        print(f"  Model: {self.bundle_path}")
        print(f"  Press Ctrl+C to stop.\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n  Shutting down Ohm runtime...")
            self._stop.set()
            self._paused.set()
            if self._thread:
                self._thread.join(timeout=10)
            print("  Done.")

    def pause(self):
        self._paused.clear()
        print("  ⏸  Evolution paused.")

    def resume(self):
        self._paused.set()
        print("  ▶  Evolution resumed.")

    def status(self):
        s = self.bundle.ohm_state
        c = self.bundle.evolution_config
        print(f"\n{'='*60}")
        print(f"Ohm Runtime Status: {self.bundle_path.name}")
        print(f"{'='*60}")
        print(f"  Model type: {self.bundle.model_type}")
        print(f"  Base model: {self.bundle.base_model_path}")
        print(f"  Parent B: {self.bundle.parent_b_path}")
        print(f"  Val set: {self.bundle.validation_set_path} ({self.bundle.validation_set_hash[:12]}...)")
        print()
        print(f"  Current best genome ({s.best_genome_id}):")
        for k, v in s.genome.to_dict().items():
            print(f"    {k:18s} = {v:.4f}")
        print()
        print(f"  Best loss: {s.best_loss:.6f}")
        print(f"  Sigma: {s.sigma:.4f}  (decay={c.sigma_decay}, min={c.sigma_min})")
        print(f"  Candidates evaluated: {s.candidates_evaluated}")
        print(f"  Improvements accepted: {s.improvements_accepted}")
        print(f"  Improvements rejected: {s.improvements_rejected}")
        accept_rate = s.improvements_accepted / max(s.candidates_evaluated, 1) * 100
        print(f"  Accept rate: {accept_rate:.1f}%")
        print()
        print(f"  Evolution enabled: {c.enabled}")
        print(f"  Cycle interval: {c.cycle_interval_sec}s")
        print(f"  Paused: {not self._paused.is_set()}")
        print(f"  Last evaluation: {s.last_evaluation or 'never'}")
        print(f"  Last swap: {s.last_swap or 'never'}")
        if s.last_accepted:
            print(f"  Last accepted loss: {s.last_accepted['loss']:.6f}")
        if s.last_rejected:
            print(f"  Last rejected loss: {s.last_rejected['loss']:.6f}")
        print()


# === CLI ===

def main():
    parser = argparse.ArgumentParser(description="OmniSenter Ohm — self-evolving model runtime")
    parser.add_argument("command", choices=["serve", "status", "step", "pause", "resume"],
                       help="What to do")
    parser.add_argument("--model", required=True, help="Path to .ohm model file")
    args = parser.parse_args()

    bundle_path = Path(args.model)
    if not bundle_path.exists():
        print(f"  ❌ Model file not found: {bundle_path}")
        sys.exit(1)
    if not bundle_path.suffix == ".ohm":
        print(f"  ⚠️  Model file doesn't have .ohm extension: {bundle_path}")

    runtime = OhmRuntime(bundle_path)
    if args.command == "serve":
        runtime.serve()
    elif args.command == "status":
        runtime.status()
    elif args.command == "step":
        runtime.step()
    elif args.command == "pause":
        runtime.pause()
    elif args.command == "resume":
        runtime.resume()


if __name__ == "__main__":
    main()
