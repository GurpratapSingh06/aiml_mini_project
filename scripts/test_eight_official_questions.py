import asyncio
import time
import json
import httpx
from app.main import app

async def test_eight_questions():
    questions = [
        "Who is the HOD of Computer Engineering?",
        "Who is the HOD of Information Technology?",
        "Who is the Director of MITAOE?",
        "What is the current academic year?",
        "Show the 2026–27 academic calendar.",
        "List all academic departments.",
        "Find the latest examination timetable.",
        "Show the source page for the Computer Engineering HOD.",
    ]
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Warmup health
        await client.get("/api/v1/health")
        
        print("=== 8 OFFICIAL EVALUATION QUESTIONS VIA FASTAPI HTTP API ===\n")
        results = []
        for i, q in enumerate(questions, 1):
            t0 = time.perf_counter()
            resp = await client.post("/api/v1/search", json={"query": q, "academic_year": "2026-27"})
            elapsed = (time.perf_counter() - t0) * 1000
            
            data = resp.json()
            diag = data.get("diagnostics", {}) or {}
            citations = data.get("citations", [])
            
            result_item = {
                "number": i,
                "raw_query": q,
                "latency_ms": round(elapsed, 2),
                "http_status": resp.status_code,
                "normalized_query": diag.get("normalized_query"),
                "selected_intent": diag.get("intent"),
                "verification_status": data.get("verification_status"),
                "is_answerable": data.get("is_answerable"),
                "retrieved_candidates": diag.get("retrieval_candidates"),
                "top_chunks": diag.get("top_chunks", [])[:3],
                "answer": data.get("answer"),
                "citations": list(dict.fromkeys(c.get("source_url") for c in citations if c.get("source_url"))),
            }
            results.append(result_item)
            
            print(f"--- QUESTION {i}: '{q}' ---")
            print(f"HTTP Status: {resp.status_code} | Total Latency: {elapsed:.2f} ms")
            print(f"Normalized Query: {diag.get('normalized_query')}")
            print(f"Selected Intent: {data.get('query_intent')}")
            print(f"Verification Status: {data.get('verification_status')}")
            print(f"Retrieved Candidates: {diag.get('retrieval_candidates')}")
            print("Top Chunks:")
            for tc in diag.get("top_chunks", [])[:3]:
                print(f"  - Score: {tc.get('score')} | Rank: {tc.get('rank')} | URL: {tc.get('source_url')}")
            print(f"Answer: {data.get('answer')[:180]}...")
            print(f"Citation URLs: {result_item['citations']}")
            print("\n" + "="*60 + "\n")
            
        with open("backend/app/evaluation/eight_questions_api_results.json", "w") as f:
            json.dump(results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(test_eight_questions())
