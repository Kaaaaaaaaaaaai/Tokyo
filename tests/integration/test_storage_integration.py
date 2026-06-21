from sqlalchemy import text

from tokyo.packages.storage.database import Database


async def test_database_session_executes_query() -> None:
    database = Database("sqlite+aiosqlite:///:memory:")
    try:
        async for session in database.session():
            result = await session.execute(text("select 1"))
            assert result.scalar_one() == 1
            break
    finally:
        await database.dispose()
