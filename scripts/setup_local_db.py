import asyncio
import asyncpg

async def setup():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='root',
        database='postgres'
    )
    users = await conn.fetch('SELECT usename FROM pg_user')
    user_names = [u['usename'] for u in users]
    print('Existing users:', user_names)

    if 'vedanta' not in user_names:
        await conn.execute("CREATE USER vedanta WITH PASSWORD 'vedanta_dev_password' SUPERUSER;")
        print('Created user vedanta')
    else:
        await conn.execute("ALTER USER vedanta WITH PASSWORD 'vedanta_dev_password' SUPERUSER;")
        print('Updated user vedanta password')

    dbs = await conn.fetch('SELECT datname FROM pg_database')
    db_names = [d['datname'] for d in dbs]
    print('Existing databases:', db_names)

    if 'vedanta' not in db_names:
        await conn.execute('CREATE DATABASE vedanta OWNER vedanta;')
        print('Created database vedanta')
    else:
        print('Database vedanta already exists')

    await conn.close()

    vconn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='vedanta',
        password='vedanta_dev_password',
        database='vedanta'
    )
    await vconn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    await vconn.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm";')
    await vconn.execute('CREATE EXTENSION IF NOT EXISTS "unaccent";')
    print('Extensions verified in vedanta db!')
    await vconn.close()

if __name__ == '__main__':
    asyncio.run(setup())
