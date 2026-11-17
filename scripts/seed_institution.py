import asyncio
import uuid
from app.core.database import async_engine
from sqlalchemy import text

async def seed_institution():
    async with async_engine.begin() as conn:
        # Insert Institution
        inst_id = "00000000-0000-0000-0000-000000000001"
        res = await conn.execute(
            text("SELECT id FROM institutions WHERE id = :id"),
            {"id": inst_id}
        )
        if not res.fetchone():
            await conn.execute(
                text("""
                INSERT INTO institutions (id, name, short_name, website, city, state, country, is_active)
                VALUES (:id, :name, :short_name, :website, :city, :state, :country, :is_active)
                """),
                {
                    "id": inst_id,
                    "name": "MIT Academy of Engineering",
                    "short_name": "MITAOE",
                    "website": "https://mitaoe.ac.in",
                    "city": "Pune",
                    "state": "Maharashtra",
                    "country": "India",
                    "is_active": True,
                }
            )
            print("MITAOE institution created.")
        else:
            print("MITAOE institution already exists.")

if __name__ == "__main__":
    asyncio.run(seed_institution())
