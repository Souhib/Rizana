from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from rizana.app import create_app
from rizana.database import create_app_engine, create_db_and_tables
from rizana.logger_config import configure_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logger()
    engine = await create_app_engine()
    await create_db_and_tables(engine)
    await engine.dispose()
    yield


app = create_app(lifespan=lifespan)

if __name__ == "__main__":
    uvicorn.run(app, port=8000)
