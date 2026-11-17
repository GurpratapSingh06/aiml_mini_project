import httpx
import json

client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=20.0)

print("--- Testing SSE Stream ---")
with client.stream("POST", "/api/v1/search/stream", json={"query": "Who is Azher Shaikh?"}) as response:
    print("Status:", response.status_code)
    for line in response.iter_lines():
        if line.startswith("data: "):
            evt = json.loads(line[6:])
            print(f"  [{evt.get('elapsed_ms')}ms] Stage: {evt.get('stage')} | {evt.get('message')}")
            if evt.get("status") == "completed":
                ans = evt.get("data", {}).get("answer", "")
                print(f"  --> Final Answer: {ans[:100]}...")

print("\n--- Testing History Persistence ---")
hist = client.get("/api/v1/search/history").json()
print("History count:", len(hist))
for h in hist[:3]:
    print(f"  - [{h.get('created_at')}] Query: {h.get('query')} -> Status: {h.get('verification_status')}")
