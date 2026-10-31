"""Benchmark the brain: each method x10 on sample data -> p50/p95 latency + fallback rate.

Usage: python -m scripts.bench_llm [runs]
"""
from __future__ import annotations

import statistics
import sys
import time

from app.brain.api import brain
from app.brain.llm import llm
from app.brain.samples import sample_case, sample_pack, sample_txns
from app.contracts import Action


def pct(vals: list[float], p: float) -> float:
    s = sorted(vals)
    return s[min(len(s) - 1, int(round(p * (len(s) - 1))))]


def main(runs: int = 10) -> None:
    case, txns, pack = sample_case("en"), sample_txns(), sample_pack()
    calls = {
        "explain_risk": lambda: brain.explain_risk(case, txns),
        "verification_messages": lambda: brain.verification_messages(sample_case("hi"), txns),
        "classify_reply": lambda: brain.classify_reply("hmm what is this about", "en"),
        "evidence_narratives": lambda: brain.evidence_narratives(pack, "hi"),
        "decision_rationale": lambda: brain.decision_rationale(case, Action.RAISE_DISPUTE),
        "ncrp_guidance": lambda: brain.ncrp_guidance(pack, "en"),
    }
    print(f"model={llm.model}  api_up={brain.is_up()}  runs={runs}")
    if llm.enabled and not brain.is_up():
        print("NOTE: Claude API not reachable (no ANTHROPIC_API_KEY or no network); all calls use templates.")
    print(f"{'method':24s} {'p50 ms':>9s} {'p95 ms':>9s} {'fallback':>9s}")
    total_fb = total = 0
    for name, call in calls.items():
        lat, fb = [], 0
        for _ in range(runs):
            t0 = time.perf_counter()
            call()
            lat.append((time.perf_counter() - t0) * 1000)
            fb += bool(brain.last_used_fallback)
        total_fb, total = total_fb + fb, total + runs
        print(f"{name:24s} {statistics.median(lat):9.1f} {pct(lat, 0.95):9.1f} {fb / runs:9.0%}")
    print(f"overall fallback rate: {total_fb / total:.0%}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 10)
