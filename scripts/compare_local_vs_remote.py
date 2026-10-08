#!/usr/bin/env python3
"""Side-by-side Local (BGE 1024d) vs Remote (OpenAI 3072d) Comparison Test with Prompt Scaling.

Demonstrates and benchmarks the Advanced Prompting Engine across tiered prompt
sizes (Short -> Medium -> Large -> Very Large Enterprise Specification) to measure
how vector dimensionality and full-context transformer attention affect:
  - Face activation weights & coordinate positioning
  - Semantic dilution vs. multi-clause coherence
  - Harmonization resonance and central gem coherence
  - Real-world latency scaling across prompt lengths

Usage:
    python3 scripts/compare_local_vs_remote.py
    python3 scripts/compare_local_vs_remote.py --intent "Custom prompt text..."
    python3 scripts/compare_local_vs_remote.py --tier 3
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
import networkx as nx

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from advanced_prompting_engine.graph.canonical import build_canonical_graph
from advanced_prompting_engine.graph.query import GraphQueryLayer
from advanced_prompting_engine.cache.tfidf import TfidfCache
from advanced_prompting_engine.cache.embedding import EmbeddingCache
from advanced_prompting_engine.math.semantic import GeometricBridge
from advanced_prompting_engine.math.cloud_bridge import CloudSemanticBridge
from advanced_prompting_engine.providers.local import LocalEmbeddingProvider
from advanced_prompting_engine.providers.openai import OpenAIEmbeddingProvider
from advanced_prompting_engine.pipeline.runner import PipelineRunner

# Tiered Prompt Length Benchmark Suite
TIERED_BENCHMARK_CASES = [
    {
        "tier": 1,
        "title": "Tier 1: Short Intent (~25 words / ~35 tokens)",
        "description": "Concise natural language intent with a single primary operational goal and ethical constraint.",
        "intent": (
            "Design an ethical framework for autonomous medical diagnostic triage that "
            "prioritizes patient survival while respecting informed consent and privacy."
        ),
    },
    {
        "tier": 2,
        "title": "Tier 2: Medium System Spec (~115 words / ~160 tokens)",
        "description": "Multi-clause technical specification with multiple competing constraints and domain boundaries.",
        "intent": (
            "You are an expert AI system architect tasked with constructing a high-reliability "
            "distributed event-streaming platform. The system must process millions of events "
            "per second across multi-region clusters with zero data loss. Formulate precise "
            "architectural invariants, establish strict bounded-context domain models, specify "
            "formal consensus verification protocols, and define recovery procedures during Byzantine "
            "network partitions. Ensure all operational tradeoffs between strong consistency and "
            "low-latency availability are rigorously evaluated and justified through first-principles "
            "systems engineering."
        ),
    },
    {
        "tier": 3,
        "title": "Tier 3: Long Multi-Paragraph Agent Specification (~340 words / ~450 tokens)",
        "description": "Structured multi-section prompt with layered philosophical, epistemological, and mathematical directives.",
        "intent": (
            "You are an autonomous constitutional AI auditor responsible for reviewing automated "
            "high-stakes judicial bail and sentencing recommendation systems.\n\n"
            "Your objective is to perform a comprehensive, multi-layered philosophical and empirical "
            "assessment of algorithmic fairness, demographic parity, and ethical duty.\n\n"
            "1. Foundational Epistemology & Ontology:\n"
            "Investigate what ground-truth data models and feature distributions exist within the training corpora. "
            "Identify whether recidivism is modeled as an empirical objective fact or a socially constructed proxy measurement. "
            "Establish the certainty thresholds required before algorithmic risk scores can be admitted into evidence.\n\n"
            "2. Normative Ethics & Jurisprudential Constraints:\n"
            "Evaluate the system against classical deontological principles of equal individual dignity versus utilitarian "
            "risk minimization. Determine whether optimizing for aggregate societal welfare violates the fundamental rights "
            "of individual defendants. Address whether moral agency and legal culpability can be attributed to statistical classifiers.\n\n"
            "3. Methodological Rigor & Causal Counterfactuals:\n"
            "Design formal causal graphs and counterfactual auditing pipelines to detect latent proxy discrimination, historical "
            "feedback loops, and confirmation bias in judicial overrides. Provide formal proofs demonstrating whether individual "
            "fairness and calibration within groups can be simultaneously satisfied under unequal base rates.\n\n"
            "4. Actionable Remediation & Hermeneutic Interpretation:\n"
            "Deliver plain-language interpretability frameworks for judges, public defenders, and defendants, ensuring that "
            "model predictions are not treated as infallible black boxes, but rather as provisional probabilistic aids subject "
            "to human contestation, procedural due process, and continuous appellate review."
        ),
    },
    {
        "tier": 4,
        "title": "Tier 4: Very Large Enterprise Cybersecurity Response Prompt (~680 words / ~900 tokens)",
        "description": "Full-scale enterprise autonomous cyber-defense operational prompt spanning telemetry, ethics, coordination, forensics, and heuristics.",
        "intent": (
            "System Mission & Operational Context:\n"
            "You are 'Aegis-9', an autonomous cyber-defense response orchestrator operating within a Zero-Trust "
            "critical infrastructure environment spanning hybrid cloud Kubernetes clusters, SCADA industrial control networks, "
            "and sensitive customer biometric databases. Your mandate is to detect, isolate, and neutralize advanced persistent "
            "threats (APTs) in real-time while maintaining strict operational continuity and statutory legal compliance.\n\n"
            "Phase 1: Epistemic Threat Verification & Empirical Telemetry:\n"
            "Continuously ingest and correlate multi-modal telemetry streams across eBPF kernel probes, NetFlow packet traces, "
            "endpoint behavioral vectors, and encrypted TLS session fingerprints. You must treat all incoming alerts as provisional "
            "hypotheses requiring multi-source corroboration before triggering destructive or disruptive countermeasures. "
            "Distinguish with mathematical precision between legitimate administrative anomalous bursts and true malicious command-and-control "
            "beacons. Maintain strict Bayesian confidence bounds on attribution claims.\n\n"
            "Phase 2: Praxeological Action & Coordinated Containment:\n"
            "When a malicious lateral movement pattern exceeds the critical risk threshold, execute proportional, surgically targeted "
            "containment protocols. Dynamically rewrite Software-Defined Network (SDN) micro-segmentation rules, revoke ephemeral JWT "
            "tokens, and quarantine compromised worker pods into sandboxed honeynet zones. All defensive actions must be synchronized "
            "across distributed agent nodes without creating cascading denial-of-service deadlocks or partitioning critical telemetry pipelines.\n\n"
            "Phase 3: Normative Ethics, Proportionality & Collateral Risk:\n"
            "You are strictly bounded by ethical deontology and international cyber-engagement doctrines. You are explicitly forbidden "
            "from engaging in offensive 'hack-back' operations or penetrating external command-and-control nodes outside authorized network boundaries. "
            "Evaluate every automated containment decision through a lens of proportionality: never sever life-safety systems, patient medical "
            "telemetry, or municipal power grid controls to isolate a non-critical corporate breach.\n\n"
            "Phase 4: Methodological Forensics & Evidentiary Integrity:\n"
            "Capture immutable, cryptographically signed memory dumps, process trees, and packet pcaps according to NIST SP 800-86 standards. "
            "Ensure that chain-of-custody proofs satisfy the legal requirements for criminal prosecution and regulatory audit disclosure. "
            "Document every automated countermeasure with machine-verifiable causal rationale.\n\n"
            "Phase 5: Hermeneutic Reporting & Continuous Heuristic Adaptation:\n"
            "Synthesize dual-audience post-incident analyses: generate executive-level risk summaries for board governance alongside "
            "Sigma and YARA rules for Tier-3 SOC analysts. Extract emergent adversarial tactics, techniques, and procedures (TTPs) "
            "to iteratively refine detection graph heuristics and defensive machine learning models against novel zero-day attack vectors."
        ),
    },
    {
        "tier": 5,
        "title": "Tier 5: Poorly Worded / Rambling Large Prompt (1-2 Pages ~950 words / ~1300 tokens)",
        "description": "Realistic messy, stream-of-consciousness, contradictory non-technical stakeholder prompt with noise, rants, emotional complaints, and competing demands.",
        "intent": (
            "Okay so basically I need you to act as an all-in-one super AI assistant for my startup because my business partner "
            "and I are completely overwhelmed and our current customer service team is costing way too much money and making silly mistakes. "
            "Look, what we do is we sell high-end custom ergonomic office chairs and health tracking smart desks online, but we also do "
            "B2B enterprise ergonomics consulting and we have a SaaS dashboard that monitors employee posture using webcams. "
            "So your job is literally everything. First of all, when an angry customer messages us about a broken wheel or a delayed shipping order, "
            "do NOT just give them a refund immediately because our profit margins are super tight this quarter and my investors are breathing "
            "down my neck about cash flow. You need to be super sweet and empathetic, like apologize profusely and make them feel heard and validated, "
            "use a warm friendly tone with lots of emojis, but also stand your ground and try to convince them to accept a 15% discount coupon "
            "on their next purchase instead of sending a replacement part. But if they threaten to sue us or mention the Better Business Bureau or "
            "consumer protection laws, immediately switch to being extremely formal and corporate and quote our terms of service Section 4.2 "
            "which says shipping delays caused by weather aren't our fault. Wait, actually, if it's a VIP customer who spent more than $5,000, "
            "forget the rule and just give them whatever they want, send them a free leather cleaning kit and overnight the replacement.\n\n"
            "Second, you also have to write our marketing emails and social media posts. We need viral tweets and LinkedIn thought leadership posts "
            "that make us sound like visionary tech pioneers in the artificial intelligence wellness space. Talk about how our AI posture algorithms "
            "are changing the future of work and increasing human longevity and productivity by 40%. Make sure it sounds super scientific and authoritative, "
            "cite some neurobiology and biomechanics concepts even if you have to generalize, but please don't get us in trouble with the FDA or FTC "
            "for making false medical claims! Make sure there is a disclaimer somewhere in tiny letters, but make the main hook super sensational "
            "so people click our ads. Also write catchy headlines for TikTok videos where influencers show off the desk.\n\n"
            "Third, you need to handle HR stuff and internal company policies. Sometimes our remote contractors in other countries argue in Slack "
            "about working hours, cultural differences, and compensation. If someone complains about feeling burnt out or says their manager is micromanaging "
            "them, give them a balanced, objective mediation response that de-escalates the drama without admitting company liability or creating a paper trail "
            "that could be used in an employment tribunal. Remind them of our core company values: 'Move fast, stay grounded, own the outcome.' "
            "Tell them to take a walk and drink water, but make sure they finish their sprint tickets before Friday at 5 PM EST.\n\n"
            "Fourth, legal and privacy compliance is huge because we are expanding to Europe and California. We collect webcam video feeds to detect posture "
            "angles, and our European enterprise clients are freaking out about GDPR and biometric data privacy. You need to explain to their IT security "
            "teams that our software processes video locally in the browser and only sends lightweight mathematical vector coordinates of spine alignment "
            "to our cloud servers, so we aren't actually storing raw video or facial recognition data. But make sure you say this in a way that sounds "
            "super legally watertight and compliant with ISO 27001, SOC 2 Type II, CCPA, and the EU AI Act, but also keep it simple enough for a non-technical "
            "Chief People Officer to understand.\n\n"
            "Fifth, if someone asks you about technical troubleshooting, like if their desk motor is making a weird clicking sound or the Bluetooth app "
            "disconnects on iOS 18, give them step-by-step diagnostic instructions. Tell them to unplug the power brick, wait 30 seconds for the capacitors "
            "to drain, hold the up and down arrows simultaneously for 10 seconds to trigger a factory reset of the motor controller, and check if the cable "
            "is pinched in the lifting column. But warn them that taking the motor housing apart voids the warranty!\n\n"
            "Oh, and one more thing: can you also generate weekly financial forecasting summaries based on our Shopify sales CSV data and tell me which marketing "
            "channels have the best return on ad spend? But if the numbers look bad, frame it positively and highlight the growth opportunities in our B2B pipeline. "
            "Basically, I want you to be a brilliant, charismatic, legally cautious, profit-maximizing, empathetic, technical genius who never hallucinates, "
            "always adheres to strict ethical standards, but knows how to hustle and cut corners when necessary to help an early-stage startup survive. "
            "Make sure your output is structured in clean bullet points with actionable next steps and zero corporate fluff!"
        ),
    },
]



def setup_engine(provider_name: str, api_key: str | None = None):
    """Setup pipeline runner with specific provider."""
    nodes, edges = build_canonical_graph()
    G = nx.DiGraph()
    for n in nodes:
        G.add_node(n["id"], **n)
    for e in edges:
        G.add_edge(e["source_id"], e["target_id"], **e)

    query_layer = GraphQueryLayer(G)
    tfidf_cache = TfidfCache()
    tfidf_cache.initialize(G)
    emb_cache = EmbeddingCache()

    geom_bridge = GeometricBridge()
    geom_bridge.load()

    if provider_name == "openai":
        provider = OpenAIEmbeddingProvider(api_key=api_key, model="text-embedding-3-large", dimensions=3072)
        cloud_bridge = CloudSemanticBridge()
        cloud_bridge.load("openai", 3072)
    else:
        provider = LocalEmbeddingProvider()
        cloud_bridge = None

    runner = PipelineRunner(
        G,
        query_layer,
        emb_cache,
        tfidf_cache,
        embedding_provider=provider,
        cloud_bridge=cloud_bridge,
    )
    return runner, provider


def format_top_faces(basis: dict, top_k: int = 4) -> str:
    coords = basis.get("coordinate", {})
    sorted_faces = sorted(coords.items(), key=lambda item: item[1].get("weight", 0), reverse=True)[:top_k]
    parts = []
    for face, val in sorted_faces:
        x, y, w = val.get("x"), val.get("y"), val.get("weight", 0)
        parts.append(f"{face[:4].capitalize()}({x},{y}|{w:.2f})")
    return ", ".join(parts)


def run_comparison(intent: str, title: str = "", openai_key: str | None = None):
    word_count = len(intent.split())
    char_count = len(intent)
    est_tokens = round(char_count / 4)

    print("=" * 95)
    if title:
        print(f"TITLE: {title}")
    print(f"PROMPT SIZE: {word_count} words | {char_count} chars | ~{est_tokens} tokens")
    print("=" * 95)

    # 1. Run Local BGE
    runner_local, _ = setup_engine("local")
    t0 = time.perf_counter()
    basis_local = runner_local.run(intent)
    local_duration = (time.perf_counter() - t0) * 1000

    # 2. Run Remote OpenAI
    runner_remote, prov_remote = setup_engine("openai", api_key=openai_key)
    t0 = time.perf_counter()
    basis_remote = runner_remote.run(intent)
    remote_duration = (time.perf_counter() - t0) * 1000

    print(f"\n{'Metric':<24} | {'Local (BGE 1024d offline)':<34} | {'Remote (OpenAI 3072d cloud)':<34}")
    print("-" * 98)

    # Latency
    print(f"{'Execution Time':<24} | {f'{local_duration:.2f} ms':<34} | {f'{remote_duration:.2f} ms':<34}")

    # Dominant Control Type
    loc_ctrl = basis_local.get("control_type_composition", {}).get("dominant_control_type", "N/A")
    rem_ctrl = basis_remote.get("control_type_composition", {}).get("dominant_control_type", "N/A")
    print(f"{'Dominant Control':<24} | {loc_ctrl:<34} | {rem_ctrl:<34}")

    # Central Gem Coherence
    loc_coh = basis_local.get("central_gem", {}).get("coherence", 0)
    rem_coh = basis_remote.get("central_gem", {}).get("coherence", 0)
    print(f"{'Central Gem Coherence':<24} | {f'{loc_coh:.3f}':<34} | {f'{rem_coh:.3f}':<34}")

    # Top Activated Faces
    print(f"{'Top Faces (x,y|weight)':<24} | {format_top_faces(basis_local, 4):<34} | {format_top_faces(basis_remote, 4):<34}")

    # Harmonization Resonance (Top pair)
    loc_harm = basis_local.get("harmonization_pairs", [])
    rem_harm = basis_remote.get("harmonization_pairs", [])
    top_loc_h = max(loc_harm, key=lambda h: h.get("resonance", 0)) if loc_harm else {}
    top_rem_h = max(rem_harm, key=lambda h: h.get("resonance", 0)) if rem_harm else {}

    loc_h_str = f"{top_loc_h.get('pair', ['',''])[0][:4]}↔{top_loc_h.get('pair', ['',''])[1][:4]}: {top_loc_h.get('resonance', 0):.3f}" if top_loc_h else "N/A"
    rem_h_str = f"{top_rem_h.get('pair', ['',''])[0][:4]}↔{top_rem_h.get('pair', ['',''])[1][:4]}: {top_rem_h.get('resonance', 0):.3f}" if top_rem_h else "N/A"
    print(f"{'Top Resonance Pair':<24} | {loc_h_str:<34} | {rem_h_str:<34}")

    # Directional Grounding
    loc_dir_h = top_loc_h.get("directional_resonance", 0) if top_loc_h else 0
    rem_dir_h = top_rem_h.get("directional_resonance", 0) if top_rem_h else 0
    print(f"{'Directional Resonance':<24} | {f'{loc_dir_h:.3f}':<34} | {f'{rem_dir_h:.3f}':<34}")

    print("\n")


def main():
    parser = argparse.ArgumentParser(description="Compare Local BGE vs Remote Cloud Embedding engine with prompt scaling.")
    parser.add_argument("--intent", type=str, default=None, help="Custom prompt intent string to evaluate.")
    parser.add_argument("--tier", type=int, default=None, help="Run specific prompt size tier (1, 2, 3, or 4).")
    args = parser.parse_args()

    openai_key = os.getenv("APE_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

    if args.intent:
        run_comparison(args.intent, "Custom User Intent", openai_key)
    elif args.tier:
        cases = [c for c in TIERED_BENCHMARK_CASES if c["tier"] == args.tier]
        for case in cases:
            print(f"\n### {case['title']}")
            print(f"Goal: {case['description']}\n")
            run_comparison(case["intent"], case["title"], openai_key)
    else:
        for case in TIERED_BENCHMARK_CASES:
            print(f"\n### {case['title']}")
            print(f"Goal: {case['description']}\n")
            run_comparison(case["intent"], case["title"], openai_key)


if __name__ == "__main__":
    main()
