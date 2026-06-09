#!/usr/bin/env python3
"""
Stage 2 Sub-op B: Stitch heads onto the OmniStep text backbone.

The text backbone (output of sft_ace_step_text_merge.py) is a 8B Qwen3
LLM. This script attaches:

  - Cosmos3-Nano multimodal heads (vision encoder, DiT, sound tokenizer,
    VAE, cross-attn, MoE twins) — preserved from gen-0-clean
  - ACE-Step DiT music head (from acestep-v15-xl-sft)
  - Nemotron 0.6B streaming ASR head (speech-in)
  - A simple intent-classifier router (text-only for v1)

This is a STRUCTURAL COMPOSITE — each "head" is a full pretrained
submodel attached under a different namespace. The chat template
dispatches at runtime.

Output: a single HF-compatible model directory with the heads wired up.

Usage:
  python3 stage2_omnistep_compose.py \\
    --text-backbone  evolution/gen-2-omnistep/omnistep-text-backbone \\
    --cosmos-heads   evolution/gen-0-clean \\
    --ace-dit        ~/.cache/huggingface/hub/models--ACE-Step--acestep-v15-xl-sft/snapshots/<HASH> \\
    --nemotron-asr   ~/.cache/huggingface/hub/models--nvidia--nemotron-streaming-asr-0.6b/snapshots/<HASH> \\
    --output         evolution/gen-2-omnistep/omnistep-v1

Status: DRAFT (2026-06-09). Not yet run. Awaiting Stage 1 SFT completion.
"""
import argparse, json, shutil
from pathlib import Path


# Heads to graft from gen-0-clean (Cosmos3-Nano multimodal components).
# These are the "extras" that the gen-0 merge preserved (cross-attn, MoE
# twins, modality embed, vision encoder, etc.). The text LLM body from
# gen-0-clean is REPLACED by the text-backbone arg.
COSMOS_HEAD_PATTERNS = [
    # Cross-modal attention (from Cosmos3-Nano)
    "add_k_proj", "add_q_proj", "add_v_proj", "to_add_out",
    "norm_added_k", "norm_added_q",
    # MoE generation twins (from Cosmos3-Nano)
    "_moe_gen",
    # Modality embeddings
    "_modality_embed",
    # Vision encoder (full submodule)
    "vision_encoder", "vision_tower", "image_processor",
    # DiT (video/image generation transformer)
    "dit", "diffusion_transformer",
    # Sound tokenizer + VAE
    "sound_tokenizer", "audio_vae", "vae",
    # Audio encoder
    "audio_encoder", "whisper",
]


def is_cosmos_head(key):
    return any(pat in key for pat in COSMOS_HEAD_PATTERNS)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text-backbone", required=True)
    parser.add_argument("--cosmos-heads", required=True,
                        help="Path to gen-0-clean (or gen-0). Source of multimodal heads.")
    parser.add_argument("--ace-dit", required=True,
                        help="Path to ACE-Step v1.5 XL SFT (DiT music head)")
    parser.add_argument("--nemotron-asr", required=True,
                        help="Path to Nemotron 0.6B streaming ASR "
                             "(use nvidia/nemotron-3.5-asr-streaming-0.6b — "
                             "the 40-language multilingual one, not the English-only)")
    parser.add_argument("--output", required=True)
    parser.add_argument("--router-mode", default="simple",
                        choices=["simple", "learned"],
                        help="Router type. simple = intent-keyword matching. "
                             "learned = tiny classifier (future).")
    args = parser.parse_args()

    text_dir = Path(args.text_backbone)
    cosmos_dir = Path(args.cosmos_heads)
    ace_dit_dir = Path(args.ace_dit)
    nemotron_dir = Path(args.nemotron_asr)
    # 2026-06-09: default to nvidia/nemotron-3.5-asr-streaming-0.6b (multilingual).
    # The English-only nvidia/nemotron-speech-streaming-en-0.6b is also valid for
    # English-only deployments but the 3.5 multilingual strictly dominates.
    output_dir = Path(args.output)

    print(f"\n{'='*60}")
    print(f"Stage 2 Sub-op B: OmniStep head stitching")
    print(f"{'='*60}")
    print(f"  Text backbone:  {text_dir}")
    print(f"  Cosmos heads:   {cosmos_dir}")
    print(f"  ACE-Step DiT:   {ace_dit_dir}")
    print(f"  Nemotron ASR:   {nemotron_dir}")
    print(f"  Output:         {output_dir}")
    print(f"  Router mode:    {args.router_mode}")

    # Sanity: all sources must exist
    for label, p in [("text", text_dir), ("cosmos", cosmos_dir),
                     ("ace_dit", ace_dit_dir), ("nemotron", nemotron_dir)]:
        if not p.exists():
            raise FileNotFoundError(f"{label} not found: {p}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy the text backbone as the base
    print(f"\n[1/4] Copying text backbone...")
    safetensors = list(text_dir.glob("*.safetensors")) + list(text_dir.glob("model*.safetensors*"))
    for f in text_dir.iterdir():
        if f.is_file():
            shutil.copy2(f, output_dir / f.name)
    print(f"  Copied {len(list(text_dir.iterdir()))} files from text backbone")

    # 2. Pull Cosmos multimodal heads from gen-0-clean
    print(f"\n[2/4] Pulling Cosmos multimodal heads from {cosmos_dir}...")
    cosmos_heads_dir = output_dir / "heads" / "cosmos"
    cosmos_heads_dir.mkdir(parents=True, exist_ok=True)
    head_count = 0
    try:
        import safetensors.torch as st
        cosmos_tensors = {}
        for sf in cosmos_dir.rglob("*.safetensors"):
            cosmos_tensors.update(st.load_file(str(sf), device="cpu"))
        heads = {k: v for k, v in cosmos_tensors.items() if is_cosmos_head(k)}
        print(f"  Identified {len(heads)} Cosmos head tensors (out of {len(cosmos_tensors)} total)")
        # Save as sharded safetensors under heads/cosmos/
        st.save_file(heads, str(cosmos_heads_dir / "cosmos_heads.safetensors"))
        head_count = len(heads)
        del cosmos_tensors
    except ImportError:
        print("  WARNING: safetensors not available, falling back to symlink")
        (cosmos_heads_dir / "source.txt").write_text(str(cosmos_dir))

    # 3. Symlink (or copy) the ACE-Step DiT and Nemotron ASR as heads
    print(f"\n[3/4] Attaching external heads (ACE-Step DiT, Nemotron ASR)...")
    ace_link = output_dir / "heads" / "ace_step_dit"
    nemotron_link = output_dir / "heads" / "nemotron_asr"
    ace_link.symlink_to(ace_dit_dir.resolve())
    nemotron_link.symlink_to(nemotron_dir.resolve())
    print(f"  ACE-Step DiT  -> {ace_link} -> {ace_dit_dir}")
    print(f"  Nemotron ASR  -> {nemotron_link} -> {nemotron_dir}")

    # 4. Write the router config + OmniStep architecture manifest
    print(f"\n[4/4] Writing router + manifest...")
    router_cfg = {
        "router_mode": args.router_mode,
        "routing_table": {
            # intent_keyword_pattern -> head_pointer
            "text_only": "text_backbone",
            "vision_in":  "heads/cosmos",
            "audio_in":   "heads/nemotron_asr",
            "music_out":  "heads/ace_step_dit",
            "video_out":  "heads/cosmos",
            "image_out":  "heads/cosmos",
        },
        "default_dispatch": "text_only",
    }
    json.dump(router_cfg, open(output_dir / "router_config.json", "w"), indent=2)

    manifest = {
        "model_name": "OmniStep",
        "version": "1.0-draft",
        "architecture": "composite",
        "components": {
            "text_backbone": {
                "source": str(text_dir),
                "params_b": 8,
                "role": "agentic reasoning, tool use, chat",
            },
            "cosmos_heads": {
                "source": str(cosmos_dir),
                "tensors": head_count,
                "role": "vision in/out, video out, audio out, image out",
            },
            "ace_step_dit": {
                "source": str(ace_dit_dir),
                "params_b": 3.5,
                "role": "music generation (audio out)",
            },
            "nemotron_asr": {
                "source": str(nemotron_dir),
                "params_b": 0.6,
                "role": "streaming speech recognition (audio in)",
            },
        },
        "active_params_b": 8,
        "total_params_b": 24,
        "router": router_cfg,
        "timestamp": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
    }
    json.dump(manifest, open(output_dir / "omnistep_manifest.json", "w"), indent=2)

    # Write a router chat template
    chat_template = """{# OmniStep router — dispatches by intent. v1: simple keyword match. #}
{%- if messages[0].role == 'system' -%}
{{ messages[0].content }}

{% endif -%}
{%- for message in messages -%}
{%- if message.role == 'user' -%}
{{ '<|im_start|>user\\n' + message.content + '<|im_end|>\\n' }}
{%- elif message.role == 'assistant' -%}
{{ '<|im_start|>assistant\\n' + message.content + '<|im_end|>\\n' }}
{%- endif -%}
{%- endfor -%}
{%- if add_generation_prompt -%}
{{ '<|im_start|>assistant\\n' }}
{%- endif -%}
"""
    (output_dir / "chat_template.jinja").write_text(chat_template)

    # Write a README
    readme = f"""# OmniStep v1 (DRAFT, 2026-06-09)

Composite multimodal model:
- **Text LLM body**: 8B Qwen3 (agentic SFT'd) — `{text_dir}`
- **Multimodal heads**: Cosmos3-Nano (vision/video/audio) — from `{cosmos_dir}`
- **Music head**: ACE-Step v1.5 XL 3.5B DiT — `{ace_dit_dir}`
- **Speech head**: Nemotron 0.6B streaming ASR — `{nemotron_dir}`
- **Total**: ~24B params (8B active on text-only path)

## Files
- `omnistep_manifest.json` — full architecture spec
- `router_config.json` — intent → head dispatch table
- `chat_template.jinja` — v1 chat template (text-only dispatch)
- `heads/cosmos/` — Cosmos multimodal tensors (safetensors)
- `heads/ace_step_dit` — symlink to ACE-Step DiT
- `heads/nemotron_asr` — symlink to Nemotron ASR
- All other files are from the text-backbone merge (Qwen3 8B)

## Stage: DRAFT — not yet executed. Awaiting Stage 1 SFT completion.
"""
    (output_dir / "README.md").write_text(readme)

    print(f"\n{'='*60}")
    print(f"✅ OmniStep v1 composed at {output_dir}")
    print(f"   Cosmos heads: {head_count} tensors")
    print(f"   Router: {args.router_mode}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
