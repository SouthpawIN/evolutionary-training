---
title: Blog
---


> **Revised 2026-06-08 (naming).** The 4-model lineup is:
> **OmniStep** + **OmniStep Ohm** + **Senter** + **Senter Ohm**.
> "OmniSenter" is the project name only. The flagship is **Senter
> Ohm**. See [`the-omni-family.md`](./the-omni-family.md).

# Blog

13 posts in the OmniSenter catalog, in reading order.

<div class="tow-badge">TOWARDS SELF-IMPROVEMENT</div>

---

## Foundations (read first)

<div class="blog-grid">
<div class="blog-card">
<h3><a href="the-omni-family.html">The Omni Family</a></h3>
<p class="meta">2026-06-07 · <span class="read-time">5 min read</span></p>
<p>The naming convention: Omni (multimodal), Senter (agentic core), Ohm (self-evolving), Senter Ohm (the flagship). With the family tree.</p>
</div>

<div class="blog-card">
<h3><a href="the-omnimodal-fusion.html">The Omnimodal Fusion</a></h3>
<p class="meta">2026-06-07 · <span class="read-time">8 min read</span></p>
<p>The three-component fusion that powers every Omni model: Cosmos × ACE-Step × Nemotron ASR.</p>
</div>

<div class="blog-card">
<h3><a href="the-omnistep-multimodal.html">OmniStep Multimodal</a></h3>
<p class="meta">2026-06-07 · <span class="read-time">7 min read</span></p>
<p>The destination unified model — a single Darwin-merged text backbone with all modality heads attached.</p>
</div>
</div>

## The flagship

<div class="blog-grid">
<div class="blog-card">
<h3><a href="senter-ohm-flagship.html">Senter Ohm: The Self-Evolving Flagship</a></h3>
<p class="meta">2026-06-07 · <span class="read-time">15 min read</span></p>
<p>The design doc. Senter Ohm = ~32B-total / 8B-active MoE with the Ohm self-evolution engine. Three new ideas, one architecture diagram.</p>
</div>

<div class="blog-card">
<h3><a href="senter-ohm-32a8b-math.html">Senter Ohm 32A8B: The Math</a></h3>
<p class="meta">2026-06-07 · <span class="read-time">8 min read</span></p>
<p>Per-layer params, active vs total, 4-bit vs bf16 disk, VRAM at inference + training.</p>
</div>

<div class="blog-card">
<h3><a href="the-5-stage-pipeline.html">The 5-Stage Pipeline</a></h3>
<p class="meta">2026-06-07 · <span class="read-time">10 min read</span></p>
<p>SFT → evolutionary merge → sparse upcycle → 256K YaRN → plugin+notebook+Ohm wiring. With wall times.</p>
</div>

<div class="blog-card">
<h3><a href="sparse-upcycling-deep-dive.html">Sparse Upcycling: The Stage 3 Deep Dive</a></h3>
<p class="meta">2026-06-07 · <span class="read-time">12 min read</span></p>
<p>Turning an 8B dense into a 32B MoE with 8B active. Math, script, design choices, wild cards.</p>
</div>
</div>

## The concepts

<div class="blog-grid">
<div class="blog-card">
<h3><a href="the-synthesia-layer.html">Synthesia: The Cross-Modal Memory Layer</a></h3>
<p class="meta">2026-06-07 · <span class="read-time">10 min read</span></p>
<p>Joint (text, audio, image) embeddings, 10 concrete benefits, the data it needs, the MoE expert.</p>
</div>

<div class="blog-card">
<h3><a href="the-ohm-runtime.html">The Ohm Runtime</a></h3>
<p class="meta">2026-06-07 · <span class="read-time">12 min read</span></p>
<p>The self-evolving model file. The .ohm bundle format, the background CMA-ES loop, the safety properties.</p>
</div>

<div class="blog-card">
<h3><a href="the-senter-architecture.html">The OmniSenter Architecture</a></h3>
<p class="meta">2026-06-07 · <span class="read-time">15 min read</span></p>
<p>Stream I/O → MoE → notebook → plugins → Hermes. The full system architecture.</p>
</div>
</div>

## The integration

<div class="blog-grid">
<div class="blog-card">
<h3><a href="senter-as-hermes-auxiliary.html">The Senter Local Model Server</a></h3>
<p class="meta">2026-06-08 · <span class="read-time">12 min read</span></p>
<p>Standalone (radio, note-taker, user-idea wiki) + Hermes auxiliary when Senter Ohm 32A8B is loaded. Wake-on-ping, liquid VRAM, opt-in wiki handoff. <em>(revised 2026-06-08 from the 2026-06-07 aux-only framing)</em></p>
</div>

<div class="blog-card">
<h3><a href="evolutionary-radio-as-desk-pet.html">The Evolutionary Radio is the Desk Pet</a></h3>
<p class="meta">2026-06-08 · <span class="read-time">12 min read</span></p>
<p>One button starts the whole local intelligence stack: omni-va + brain + wiki + vault + compactor. The local model IS the gold judge, the Hermes aux, and the brain. The unified vision post (Chris's 2026-06-08 epiphany).</p>
</div>
<div class="blog-card">
<h3><a href="the-omni-va-architecture.html">The Omni VA Architecture</a></h3>
<p class="meta">2026-06-08 · <span class="read-time">12 min read</span></p>
<p>The local model server (omni-va) — wake-on-ping, liquid VRAM, auto-heal. Bedrock of Evolution Radio, the note-taker, and the Hermes aux. The canonical arch doc for the slot.</p>
</div>

<div class="blog-card">
<h3><a href="the-notebook-schema.html">The Notebook Schema</a></h3>
<p class="meta">2026-06-07 · <span class="read-time">10 min read</span></p>
<p>YAML session files, cross-modal moments, the compaction policy, the privacy model.</p>
</div>
</div>

## The research direction

<div class="blog-grid">
<div class="blog-card">
<h3><a href="generative-darwin-evolution.html">Generative Darwin Evolution</a></h3>
<p class="meta">2026-06-07 · <span class="read-time">10 min read</span></p>
<p>Extending Darwin Family weight-space merging to DiT/audio/video. The research direction.</p>
</div>
</div>

---

<div class="tow-callout">TOWARDS SELF-IMPROVEMENT</div>
