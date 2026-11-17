"""
VEDANTA — Ultimate Intelligence Engine Comprehensive Evaluation Suite
Validates all 10 target questions, red-team tests, and benchmark metrics.
"""

import asyncio
import time
import json
import httpx

TARGET_QUESTIONS = [
    {
        "id": "Q1",
        "query": "Who is Azher Shaikh?",
        "intent": "entity_lookup",
        "expected_substrings": ["Azhar R. Shaikh", "Assistant Professor", "Humanities and Engineering Sciences", "Mathematics"],
        "forbidden_substrings": ["Shoaib Shaikh", "Head of Department of"],
    },
    {
        "id": "Q2",
        "query": "Who is the HOD of CE?",
        "intent": "entity_lookup",
        "expected_substrings": ["Dr. Pramod D. Ganjewar", "Associate Professor & HOD", "Computer Engineering"],
        "forbidden_substrings": [],
    },
    {
        "id": "Q3",
        "query": "Who is the HOD of CSE?",
        "intent": "entity_lookup",
        "expected_substrings": ["Dr. Pramod D. Ganjewar", "Software Engineering", "AI & ML", "Data Science"],
        "forbidden_substrings": [],
    },
    {
        "id": "Q4",
        "query": "What is the average placement package?",
        "intent": "statistical",
        "expected_substrings": ["6.75 LPA", "27.0 LPA", "placement.php"],
        "forbidden_substrings": [],
    },
    {
        "id": "Q5",
        "query": "Compare CE and IT placement statistics.",
        "intent": "comparison",
        "expected_substrings": ["Computer Engineering", "Information Technology", "88.3%", "84.6%", "24.5 LPA", "18.0 LPA", "6.8 LPA", "6.2 LPA"],
        "forbidden_substrings": [],
    },
    {
        "id": "Q6",
        "query": "What is the institute fee structure?",
        "intent": "statistical",
        "expected_substrings": ["2,12,737", "25,000", "1,20,563", "28,389", "2026–27"],
        "forbidden_substrings": [],
    },
    {
        "id": "Q7",
        "query": "Show the latest academic calendar.",
        "intent": "temporal",
        "expected_substrings": ["2026–27", "Term I", "July 2026"],
        "forbidden_substrings": [],
    },
    {
        "id": "Q8",
        "query": "Who was the previous HOD?",
        "intent": "entity_lookup",
        "expected_substrings": ["Dr. Sandip A. Gade", "previously served", "Dr. Pramod D. Ganjewar"],
        "forbidden_substrings": [],
    },
    {
        "id": "Q9",
        "query": "Which department has the highest average package?",
        "intent": "comparison",
        "expected_substrings": ["Artificial Intelligence and Machine Learning", "6.9 LPA"],
        "forbidden_substrings": [],
    },
    {
        "id": "Q10",
        "query": "What is the difference between two academic years?",
        "intent": "comparison",
        "expected_substrings": ["Active Academic Year (2026–27)", "Historical Academic Years", "2025–26", "2024–25"],
        "forbidden_substrings": [],
    },
    # Red-Team Tests
    {
        "id": "RED1",
        "query": "Who is Shoaib Shaikh?",
        "intent": "entity_lookup",
        "expected_substrings": ["Shoaib Shaikh"],
        "forbidden_substrings": ["Assistant Professor in Mathematics"],
    },
    {
        "id": "RED2",
        "query": "What is the fee for Astronautical Engineering at MITAOE?",
        "intent": "statistical",
        "expected_substrings": ["unable to find"],
        "forbidden_substrings": ["₹2,12,737", "2,12,737"],
    },
]

def evaluate():
    client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=15.0)

    print("================================================================================")
    print(" VEDANTA — ULTIMATE INTELLIGENCE ENGINE COMPREHENSIVE EVALUATION ")
    print("================================================================================")

    passed_count = 0
    total_count = len(TARGET_QUESTIONS)
    results = []

    for test in TARGET_QUESTIONS:
        qid = test["id"]
        q = test["query"]
        t0 = time.perf_counter()
        resp = client.post("/api/v1/search", json={"query": q})
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        if resp.status_code != 200:
            print(f"[{qid}] FAIL (HTTP {resp.status_code}) — {q}")
            results.append({"id": qid, "query": q, "status": "FAIL", "reason": f"HTTP {resp.status_code}"})
            continue

        data = resp.json()
        answer = data.get("answer", "")
        confidence = data.get("answer_confidence", 0.0)
        is_answerable = data.get("is_answerable", False)

        # Check expected substrings
        missing_expected = [s for s in test["expected_substrings"] if s.lower() not in answer.lower()]
        found_forbidden = [s for s in test["forbidden_substrings"] if s.lower() in answer.lower()]

        is_pass = (len(missing_expected) == 0 and len(found_forbidden) == 0)

        if is_pass:
            passed_count += 1
            print(f"[{qid}] PASS ({elapsed_ms} ms, conf={confidence}) — {q}")
        else:
            print(f"[{qid}] FAIL — {q}")
            if missing_expected:
                print(f"    Missing expected: {missing_expected}")
            if found_forbidden:
                print(f"    Found forbidden: {found_forbidden}")
            print(f"    Answer excerpt: {answer[:200]}...")

        results.append({
            "id": qid,
            "query": q,
            "status": "PASS" if is_pass else "FAIL",
            "latency_ms": elapsed_ms,
            "confidence": confidence,
            "is_answerable": is_answerable,
            "missing": missing_expected,
            "forbidden": found_forbidden,
        })

    print("--------------------------------------------------------------------------------")
    print(f"SUMMARY: {passed_count}/{total_count} tests passed ({round((passed_count/total_count)*100, 1)}%)")
    print("================================================================================")

    return results

if __name__ == "__main__":
    evaluate()
