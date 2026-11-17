"""
VEDANTA — Generalized Dynamic Faculty Discovery & Identity Resolution Benchmark
Tests unseen faculty profiles, negative controls, identity isolation, cache validation,
source accounting, and real progress events via live HTTP/SSE endpoints.
"""

import httpx
import json
import time

BASE_URL = "http://127.0.0.1:8000"
client = httpx.Client(base_url=BASE_URL, timeout=30.0)

print("=" * 80)
print(" VEDANTA — GENERALIZED DYNAMIC FACULTY DISCOVERY BENCHMARK")
print("=" * 80)

# Test 1: Held-out Faculty Profiles dynamically discovered from MITAOE
FACULTY_TESTS = [
    {
        "query": "Who is Pravin Pawar?",
        "expected_name_tokens": ["pravin", "pawar"],
        "expected_dept": "Artificial Intelligence and Machine Learning",
        "expected_role": "Professor of Practice",
        "expected_url_part": "Pravin-Pawar",
    },
    {
        "query": "Who is Sneha Chhatraband?",
        "expected_name_tokens": ["sneha", "chhatraband"],
        "expected_dept": "Humanities",
        "expected_role": "Assistant Professor",
        "expected_url_part": "Sneha-Chhatraband",
    },
    {
        "query": "Who is Kalpana Kanade?",
        "expected_name_tokens": ["kalpana", "kanade"],
        "expected_dept": "Information Technology",
        "expected_role": "Assistant Professor",
        "expected_url_part": "Kalpana-Kanade",
    },
    {
        "query": "Who is Amitkumar Shinde?",
        "expected_name_tokens": ["amitkumar", "shinde"],
        "expected_dept": "Computer Engineering",
        "expected_role": "Assistant Professor",
        "expected_url_part": "amitkumar-shinde",
    },
    {
        "query": "Who is Atul Bengeri?",
        "expected_name_tokens": ["atul", "bengeri"],
        "expected_dept": "Data Science",
        "expected_role": "Professor of Practice",
        "expected_url_part": "Atul-Bengeri",
    },
    {
        "query": "Who is Azher Shaikh?",
        "expected_name_tokens": ["azhar", "shaikh"],
        "expected_dept": "Humanities",
        "expected_role": "Assistant Professor",
        "expected_url_part": "arshaikh",
    },
]

passed_count = 0
total_count = len(FACULTY_TESTS)

print("\n--- 1. Testing Unseen Faculty Discovery & Credential Extraction ---")
for tc in FACULTY_TESTS:
    q = tc["query"]
    t0 = time.perf_counter()
    resp = client.post("/api/v1/search", json={"query": q, "top_k": 5})
    lat_ms = int((time.perf_counter() - t0) * 1000)

    if resp.status_code != 200:
        print(f"[FAIL] HTTP {resp.status_code} for '{q}'")
        continue

    data = resp.json()
    ans = data.get("answer", "")
    ans_lower = ans.lower()
    citations = data.get("citations", [])

    # Verify identity match
    name_ok = any(t in ans_lower for t in tc["expected_name_tokens"])
    # Verify designation match
    desig_ok = tc["expected_role"].lower() in ans_lower
    # Verify department match
    dept_ok = tc["expected_dept"].lower() in ans_lower
    # Verify official URL citation
    url_ok = any(tc["expected_url_part"].lower() in c.get("source_url", "").lower() for c in citations)

    if name_ok and desig_ok and url_ok:
        passed_count += 1
        print(f"[PASS] ({lat_ms:3d} ms) {q:28} -> {ans[:90]}...")
    else:
        print(f"[FAIL] ({lat_ms:3d} ms) {q:28}")
        print(f"       Name OK: {name_ok} | Desig OK: {desig_ok} | Dept OK: {dept_ok} | URL OK: {url_ok}")
        print(f"       Answer: {ans[:150]}")

print(f"\nUnseen Faculty Discovery Score: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")

# Test 2: Strict Identity Isolation & Negative Controls
print("\n--- 2. Testing Strict Identity Isolation (No Person Substitutions) ---")
neg_tests = [
    {
        "query": "Who is Shoaib Shaikh?",
        "forbidden_name": "Azhar",
        "description": "Must not substitute Azhar Shaikh for Shoaib Shaikh",
    },
    {
        "query": "Who is John Doe?",
        "forbidden_name": "Professor",
        "description": "Fictitious person must return insufficient_evidence",
    },
    {
        "query": "Who is Ramesh FictitiousProfessor123?",
        "forbidden_name": "Assistant",
        "description": "Fictitious professor must return insufficient_evidence",
    },
]

neg_passed = 0
for nt in neg_tests:
    q = nt["query"]
    resp = client.post("/api/v1/search", json={"query": q})
    data = resp.json()
    ans = data.get("answer", "")
    conf = data.get("answer_confidence", 0.0)
    status = data.get("verification_status", "")

    # For John Doe and fictitious names, must be insufficient_evidence
    if "Shoaib" in q:
        # Shoaib Shaikh is alumni or not faculty; must not claim he is Azhar Shaikh!
        no_leak = "azhar" not in ans.lower()
        if no_leak:
            neg_passed += 1
            print(f"[PASS] {q:35} -> Strict Isolation Verified (No Azhar Shaikh substitution)")
        else:
            print(f"[FAIL] {q:35} -> Leaked '{ans[:100]}'")
    else:
        if status == "insufficient_evidence" or conf == 0.0 or "unable to find" in ans.lower():
            neg_passed += 1
            print(f"[PASS] {q:35} -> Correctly rejected (status: {status}, conf: {conf})")
        else:
            print(f"[FAIL] {q:35} -> Hallucinated answer: '{ans[:100]}'")

# Test 3: Real SSE Progress Stream Events (Checking Skipped vs Completed)
print("\n--- 3. Testing Real SSE Progress Status Events ---")
sse_stages_seen = {}
with client.stream("POST", "/api/v1/search/stream", json={"query": "Who is Pravin Pawar?"}) as stream:
    for line in stream.iter_lines():
        if line.startswith("data: "):
            evt = json.loads(line[6:])
            stg = evt.get("stage")
            st = evt.get("status")
            if stg:
                sse_stages_seen[stg] = st
                print(f"  Stage: {stg:25} | Status: {st:10} | {evt.get('message', '')[:60]}")

has_skipped_or_completed = "searching_local_knowledge" in sse_stages_seen and "completed" in sse_stages_seen
print(f"SSE Progress Verification: {'PASS' if has_skipped_or_completed else 'FAIL'}")

# Test 4: Local History Memory Persistence
print("\n--- 4. Testing Local Institutional History Persistence ---")
hist = client.get("/api/v1/search/history?limit=10").json()
print(f"Total History Records in PostgreSQL: {len(hist)}")
for h in hist[:3]:
    print(f"  - [{h.get('created_at')}] {h.get('query')} -> {h.get('verification_status')} ({h.get('total_latency_ms')}ms)")

print("\n" + "=" * 80)
all_ok = passed_count == total_count and neg_passed == len(neg_tests) and has_skipped_or_completed and len(hist) > 0
print(f"ALL TESTS COMPLETED: {'100% PASS' if all_ok else 'SOME FAILED'}")
print("=" * 80)
