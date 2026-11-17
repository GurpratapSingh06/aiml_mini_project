import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def audit():
    async with AsyncSessionLocal() as session:
        # Check Azher Shaikh
        res = await session.execute(text("SELECT source_url, left(text, 200) FROM content_chunks WHERE text ILIKE '%Azher%' OR text ILIKE '%Shaikh%'"))
        rows = res.fetchall()
        print(f"=== AZHER / SHAIKH IN CONTENT_CHUNKS ({len(rows)} found) ===")
        for r in rows:
            print(f"URL: {r[0]}")
            print(f"Text: {r[1]}\n")

        # Check placement records
        res = await session.execute(text("SELECT count(*) FROM placement_records"))
        print(f"placement_records count: {res.scalar()}")

        # Check fee records
        res = await session.execute(text("SELECT count(*) FROM fee_records"))
        print(f"fee_records count: {res.scalar()}")

        # Check placement keywords in content_chunks
        res = await session.execute(text("SELECT source_url, left(text, 150) FROM content_chunks WHERE text ILIKE '%placement%' or text ILIKE '%package%' or text ILIKE '%CTC%' LIMIT 5"))
        rows = res.fetchall()
        print(f"\n=== PLACEMENT IN CONTENT_CHUNKS ({len(rows)} samples) ===")
        for r in rows:
            print(f"URL: {r[0]} | Text: {r[1]}")

        # Check fee keywords in content_chunks
        res = await session.execute(text("SELECT source_url, left(text, 150) FROM content_chunks WHERE text ILIKE '%fee%' LIMIT 5"))
        rows = res.fetchall()
        print(f"\n=== FEE IN CONTENT_CHUNKS ({len(rows)} samples) ===")
        for r in rows:
            print(f"URL: {r[0]} | Text: {r[1]}")

if __name__ == "__main__":
    asyncio.run(audit())
