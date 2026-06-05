"""Evolutionary Training — Three Merge Lines
═══════════════════════════════════════════
ARCHITECTURE REQUIREMENT: For real Darwin merges (not just tensor copying),
parents must share the same architecture family and hidden dimensions.
Cosmos3-Nano text backbone = Qwen3-VL (hidden=4096, 36L, vocab=151936)
Qwen3-8B = Qwen3 (hidden=4096, 36L, vocab=151936) ← PERFECT MATCH
LFM2.5 = Lfm2Moe (hidden=2048, 24L) ← CROSS-ARCH (mostly keep one parent)
AceStep 4B = Qwen3 (hidden=2560, 28L) ← SMALLER (mostly keep parent A)
"""

# ═══════════════════════════════════════════════════════════════════
# Line 1: OmniSenter — Agentic / Tool-Calling / Reasoning
# ═══════════════════════════════════════════════════════════════════
#   Parent A: Cosmos3-Nano  (Qwen3-VL, hidden=4096, 36L) ← OPEN omni backbone
#   Parent B: Qwen3-8B      (Qwen3, hidden=4096, 36L)    ← PERFECT architecture match
#   Strategy: REAL BLEND — same hidden, same layers, same vocab
#   Result:  OmniSenter     Omni Senter — agentic assistant
#   HF:     sovthpaw/omnisenter-evo-gen0 → gen1 → gen2 → ...
#   Why: Both are Qwen3-family with hidden=4096. Cosmos has omni training,
#        Qwen3-8B has fresh Qwen3 reasoning. Darwin can actually blend weights.
LINE1 = {
    "name":       "omnisenter",
    "parent_a":   "~/Models/storage/Cosmos3-Nano",
    "parent_b":   "~/Models/storage/Qwen3-8B",
    "hf_repo":    "sovthpaw/omnisenter-evo",
    "description": "Cosmos3-Nano × Qwen3-8B → agentic omni assistant",
    "merge_type":  "full_blend",  # Same arch = real blending
}

# ═══════════════════════════════════════════════════════════════════
# Line 2: OmniStep — Music / Audio / Beat Production
# ═══════════════════════════════════════════════════════════════════
#   Parent A: Qwen3-8B      (Qwen3, hidden=4096, 36L)    ← Best Qwen3 text backbone
#   Parent B: AceStep 5Hz 4B (Qwen3, hidden=2560)         ← Music production LM
#   Strategy: CROSS-DIM (keep Qwen3-8B for backbone, merge where possible)
#   Result:  OmniStep       Omni Step — beat/music production
#   HF:     sovthpaw/omnistep-evo-gen0 → gen1 → gen2 → ...
LINE2 = {
    "name":       "omnistep",
    "parent_a":   "~/Models/storage/Qwen3-8B",
    "parent_b":   "~/Models/hf/Ace-Step1.5/acestep-5Hz-lm-4B",
    "hf_repo":    "sovthpaw/omnistep-evo",
    "description": "Qwen3-8B × AceStep-4B → music production omni",
    "merge_type":  "cross_dim",  # Different hidden sizes
}

# ═══════════════════════════════════════════════════════════════════
# Line 3: OmniSS — Ultimate Combo
# ═══════════════════════════════════════════════════════════════════
#   Parent A: Best from Line 1  (best OmniSenter candidate)
#   Parent B: Best from Line 2  (best OmniStep candidate)
#   Strategy: CROSS-RESULT (merge the best evolved from each line)
#   Result:  OmniSS          Omni Southpaw — the ultimate
#   HF:     sovthpaw/omniss-evo-gen0 → gen1 → gen2 → ...
LINE3 = {
    "name":       "omniss",
    "parent_a":   "sovthpaw/omnisenter-evo:latest",   # placeholder — filled at runtime
    "parent_b":   "sovthpaw/omnistep-evo:latest",     # placeholder — filled at runtime
    "hf_repo":    "sovthpaw/omniss-evo",
    "description": "Best OmniSenter × Best OmniStep → ultimate omni",
    "merge_type":  "cross_result",
}

# ═══════════════════════════════════════════════════════════════════
# Scaling Path (when line 1 saturates)
# ═══════════════════════════════════════════════════════════════════
#   Qwen3-8B is a small target. If it plateaus, scale up:
#     1. Qwen3-Coder-30B-A3B   (hidden=2048, MoE, different arch — CROSS-ARCH)
#     2. Nemotron Nano 30A3B   (hidden=1024, different arch — CROSS-ARCH)
#     3. Qwen3-30B-A3B         (hidden=2048, MoE — CROSS-ARCH)
#     4. Qwen3-32B             (hidden=4096, dense — SAME ARCH if available)
SCALING_PATH = [
    "Qwen3-8B → merge with Cosmos3-Nano (same arch = real blend)",
    "If plateau: add Qwen3-Coder-30B-A3B as 3rd parent (cross-arch)",
    "If plateau: scale to Qwen3-32B or Nemotron Nano 30A3B",
    "Each scale-up = new generation in the upload staging (genN)"
]

ALL_LINES = [LINE1, LINE2, LINE3]
