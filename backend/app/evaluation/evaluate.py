"""
VEDANTA — MITAOE Standardized Institutional Benchmark Evaluation Engine
Executes the 38 institutional test items across 9 categories.
Computes Precision@5, Recall@5, MRR, Correctness, Citation Accuracy, and Latency (p50, p95, p99).
"""

from __future__ import annotations

import asyncio
import json
import math
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.evaluation.dataset import MITAOE_EVALUATION_DATASET, EvaluationItem
from app.intelligence.answer_engine.pipeline import AnswerPipeline
from app.retrieval.pipeline import get_retrieval_pipeline


async def run_evaluation() -> Dict[str, Any]:
    print("=" * 88)
    print(" VEDANTA — MITAOE GROUND TRUTH BENCHMARK EVALUATION (ACADEMIC YEAR 2026–27)")
    print("=" * 88)

    retrieval_pipe = get_retrieval_pipeline()
    if not retrieval_pipe.bm25.is_ready or not retrieval_pipe.faiss.is_ready:
        print("[WARN] Retrieval pipeline was uninitialized. Loading indexes from disk...")
        retrieval_pipe.initialize()

    pipeline = AnswerPipeline()
    results = []
    latencies = []
    reciprocal_ranks = []
    precision_at_5_list = []
    recall_at_5_list = []
    citation_accuracies = []

    total_items = len(MITAOE_EVALUATION_DATASET)
    print(f"\nExecuting {total_items} benchmark questions across 9 institutional categories...\n")

    for idx, item in enumerate(MITAOE_EVALUATION_DATASET, start=1):
        t0 = time.perf_counter()
        resp = await pipeline.answer(item.question, top_k=5)
        duration_ms = (time.perf_counter() - t0) * 1000
        latencies.append(duration_ms)

        answer_text = resp.get("answer", "")
        verification_status = resp.get("verification_status", "uncertain")
        is_answerable = resp.get("is_answerable", True)
        evidence = resp.get("evidence", [])

        # 1. Correctness Check
        keywords_matched = [kw for kw in item.expected_answer_keywords if kw.lower() in answer_text.lower()]
        if not item.is_answerable:
            # For unanswerable items, passing means honest refusal and insufficient_evidence
            is_correct = (
                not is_answerable
                or verification_status == "insufficient_evidence"
                or any(ref in answer_text.lower() for ref in ["unable to find", "cannot find", "not available", "insufficient evidence", "no verified information"])
            )
        else:
            is_correct = len(keywords_matched) > 0 and is_answerable and verification_status in ["verified", "partially_verified"]

        # 2. Retrieval Metrics (Precision@5, Recall@5, MRR)
        if item.is_answerable:
            relevant_retrieved = 0
            first_relevant_rank = None

            for r_idx, ev in enumerate(evidence[:5], start=1):
                ev_text = (ev.get("passage") or ev.get("text") or "").lower()
                source_url = ev.get("source_url") or ""
                # A chunk is considered relevant if it contains an expected keyword or matches source domain
                is_rel = any(kw.lower() in ev_text for kw in item.expected_answer_keywords) or (
                    item.expected_source_domain in source_url and "mitaoe" in ev_text
                )
                if is_rel:
                    relevant_retrieved += 1
                    if first_relevant_rank is None:
                        first_relevant_rank = r_idx

            p5 = relevant_retrieved / 5.0
            precision_at_5_list.append(p5)

            # Recall@5: Did we retrieve at least 1 relevant chunk for this query?
            r5 = 1.0 if relevant_retrieved > 0 else 0.0
            recall_at_5_list.append(r5)

            rr = 1.0 / first_relevant_rank if first_relevant_rank else 0.0
            reciprocal_ranks.append(rr)

            # Citation accuracy: verify cited sources are official mitaoe.ac.in links
            valid_citations = [e for e in evidence if item.expected_source_domain in (e.get("source_url") or "")]
            citation_acc = len(valid_citations) / len(evidence) if evidence else 0.0
            citation_accuracies.append(citation_acc)
        else:
            # Negative control: correctly identifying insufficient evidence gives perfect precision/recall for refusal
            precision_at_5_list.append(1.0 if is_correct else 0.0)
            recall_at_5_list.append(1.0 if is_correct else 0.0)
            reciprocal_ranks.append(1.0 if is_correct else 0.0)
            citation_accuracies.append(1.0)

        results.append({
            "id": item.id,
            "category": item.category,
            "question": item.question,
            "latency_ms": round(duration_ms, 1),
            "correct": is_correct,
            "status": verification_status,
            "cache_hit": resp.get("cache_hit", False),
            "keywords_matched": len(keywords_matched),
            "answer_preview": answer_text[:120].replace("\n", " "),
        })

        status_tag = "[PASS]" if is_correct else "[FAIL]"
        cat_tag = item.category[:22]
        print(f"[{idx:02d}/{total_items:02d}] {status_tag:<6} | {cat_tag:<22} | {duration_ms:5.1f} ms | Status: {verification_status:<20}")
        print(f"       Q: {item.question}")
        if not is_correct:
            print(f"       ❌ Answer: {answer_text[:100]}...")

    # Aggregations & Metrics Calculation
    total_q = len(results)
    passed_q = sum(1 for r in results if r["correct"])
    correctness_pct = (passed_q / total_q) * 100.0
    mean_precision_5 = sum(precision_at_5_list) / len(precision_at_5_list) * 100.0
    mean_recall_5 = sum(recall_at_5_list) / len(recall_at_5_list) * 100.0
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
    mean_citation_acc = sum(citation_accuracies) / len(citation_accuracies) * 100.0

    sorted_latencies = sorted(latencies)
    avg_latency = sum(latencies) / len(latencies)
    p50_lat = sorted_latencies[len(sorted_latencies) // 2]
    p95_lat = sorted_latencies[int(len(sorted_latencies) * 0.95)]
    p99_lat = sorted_latencies[min(int(len(sorted_latencies) * 0.99), len(sorted_latencies) - 1)]

    print("\n" + "=" * 88)
    print(" VEDANTA BENCHMARK EVALUATION SCORECARD")
    print("=" * 88)
    print(f" Total Benchmark Questions:  {total_q}")
    print(f" Ground Truth Accuracy:      {passed_q} / {total_q} ({correctness_pct:.1f}%)")
    print(f" Precision@5:                {mean_precision_5:.1f}%")
    print(f" Recall@5:                   {mean_recall_5:.1f}%")
    print(f" Mean Reciprocal Rank (MRR): {mrr:.3f}")
    print(f" Official Citation Accuracy: {mean_citation_acc:.1f}%")
    print("-" * 88)
    print(f" Average Latency:            {avg_latency:.1f} ms")
    print(f" p50 Response Time:          {p50_lat:.1f} ms")
    print(f" p95 Response Time:          {p95_lat:.1f} ms")
    print(f" p99 Response Time:          {p99_lat:.1f} ms")
    print("=" * 88)

    summary = {
        "total_questions": total_q,
        "passed_questions": passed_q,
        "correctness_rate": round(correctness_pct, 2),
        "precision_at_5": round(mean_precision_5, 2),
        "recall_at_5": round(mean_recall_5, 2),
        "mrr": round(mrr, 4),
        "citation_accuracy": round(mean_citation_acc, 2),
        "latency_avg_ms": round(avg_latency, 2),
        "latency_p50_ms": round(p50_lat, 2),
        "latency_p95_ms": round(p95_lat, 2),
        "latency_p99_ms": round(p99_lat, 2),
        "results": results,
    }

    # Persist scorecard artifact
    output_path = Path("backend/app/evaluation/benchmark_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nBenchmark scorecard persisted to: {output_path}")

    return summary


if __name__ == "__main__":
    asyncio.run(run_evaluation())
