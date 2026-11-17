import asyncio
from app.intelligence.answer_engine.pipeline import AnswerPipeline

async def run_query(query: str):
    pipeline = AnswerPipeline()
    res = await pipeline.answer(query)
    print("=" * 60)
    print(f"QUERY: {query}")
    print(f"INTENT: {res.get('query_intent')}")
    print(f"ANSWERABLE: {res.get('is_answerable')} | CONFIDENCE: {res.get('confidence')}")
    print(f"ANSWER:\n{res.get('answer')}")
    print("EVIDENCE:")
    for e in res.get("evidence", [])[:2]:
        print(f"  - {e.get('source_url')}: {e.get('passage')[:120]}...")
    print("=" * 60)

async def main():
    queries = [
        "Who is Azher Shaikh?",
        "Who is the HOD of CE?",
        "Who is the HOD of CSE?",
        "What is the average placement package?",
        "Compare CE and IT placement statistics.",
        "What is the institute fee structure?",
        "Show the latest academic calendar.",
        "Who was the previous HOD?",
        "Which department has the highest average package?",
        "What is the difference between two academic years?",
    ]
    for q in queries:
        await run_query(q)

if __name__ == "__main__":
    asyncio.run(main())
