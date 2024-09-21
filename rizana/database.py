from sqlalchemy.event import listens_for
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel

from rizana.settings import Settings


async def create_app_engine() -> AsyncEngine:
    settings = Settings()
    if "sqlite" in settings.database_url:
        engine = create_async_engine(
            settings.database_url, connect_args={"check_same_thread": False}, echo=True
        )

        @listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        # SQLAlchemyInstrumentor().instrument(engine=engine)

    else:
        engine = create_async_engine(settings.database_url, echo=True)
    return engine


async def create_db_and_tables(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
