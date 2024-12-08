from sqlalchemy.event import listens_for
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel

from rizana.settings import Settings


async def create_app_engine() -> AsyncEngine:
    """
    Creates and configures the application's database engine.

    This function initializes the application's database engine based on the database URL
    specified in the settings. If the database URL is for SQLite, it sets the foreign keys
    pragma to ON for each connection. It then prints the database URL and returns the engine.

    Returns:
        AsyncEngine: The configured database engine.
    """
    settings = Settings()
    if "sqlite" in settings.database_url:
        engine = create_async_engine(
            settings.database_url, connect_args={"check_same_thread": False}, echo=True
        )

        @listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """
            Sets the foreign keys pragma to ON for SQLite connections.

            This function is a listener for the "connect" event of the engine's sync_engine.
            It sets the foreign keys pragma to ON for each connection to ensure foreign key
            constraints are enforced.

            Args:
                dbapi_connection: The database API connection.
                connection_record: The connection record.
            """
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        # SQLAlchemyInstrumentor().instrument(engine=engine)

    else:
        engine = create_async_engine(settings.database_url, echo=True)
    return engine


async def create_db_and_tables(engine: AsyncEngine):
    """
    Creates the database and tables based on the SQLModel metadata.

    This function creates the database and tables based on the SQLModel metadata using the
    provided engine. It ensures the database schema is up-to-date with the model definitions.

    Args:
        engine (AsyncEngine): The database engine to use for creating the database and tables.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
