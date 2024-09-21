from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference
from sqlalchemy.exc import NoResultFound
from starlette.responses import JSONResponse

from rizana.api.routes.user import router as user_router
from rizana.api.routes.item import router as item_router
from rizana.api.routes.category import router as category_router
from rizana.api.schemas.error import BaseError


def create_app(lifespan) -> FastAPI:
    """
    It creates a FastAPI app, adds CORS middleware, and includes the routers we created earlier

    :return: A FastAPI object
    """
    origins = ["*"]
    app = FastAPI(title="Rizana", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,  # type: ignore
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(user_router)
    app.include_router(item_router)
    app.include_router(category_router)

    @app.get("/scalar", include_in_schema=False)
    async def scalar_html():
        return get_scalar_api_reference(
            openapi_url="/openapi.json",
            title="Rizana API Scalar",
        )

    @app.exception_handler(NoResultFound)
    async def no_result_found_exception_handler(request: Request, exc: NoResultFound):
        return JSONResponse(
            status_code=404,
            content={"message": "Couldn't find requested resource"},
        )

    @app.exception_handler(BaseError)
    async def base_error_exception_handler(request: Request, exc: BaseError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "name": exc.name,
                "message": exc.message,
                "status_code": exc.status_code,
            },
        )

    return app
