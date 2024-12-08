from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from richapi import enrich_openapi
from scalar_fastapi import get_scalar_api_reference
from starlette.responses import JSONResponse

from rizana.api.routes.category import router as category_router
from rizana.api.routes.chat import router as chat_router
from rizana.api.routes.item import router as item_router
from rizana.api.routes.order import router as order_router
from rizana.api.routes.payment import router as payment_router
from rizana.api.routes.user import router as user_router
from rizana.api.routes.wishlist import router as wishlist_router
from rizana.api.schemas.error import BaseError


def create_app(lifespan) -> FastAPI:
    """
    Creates a FastAPI app, adds CORS middleware, and includes the routers we created earlier.

    Args:
        lifespan: The lifespan of the FastAPI app.

    Returns:
        FastAPI: The created FastAPI app.
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
    app.include_router(order_router)
    app.include_router(category_router)
    app.include_router(payment_router)
    app.include_router(wishlist_router)
    app.include_router(chat_router)

    @app.get("/scalar", include_in_schema=False)
    async def scalar_html():
        """
        Returns the Scalar API reference for the Rizana API.

        This endpoint is not included in the OpenAPI schema. It provides a reference to the Scalar API
        documentation for the Rizana API. The Scalar API is a tool for generating API documentation and
        client code.

        Returns:
            dict: A dictionary containing the Scalar API reference.
        """
        return get_scalar_api_reference(
            openapi_url="/openapi.json",
            title="Rizana API Scalar",
        )

    @app.exception_handler(BaseError)
    async def base_error_exception_handler(request: Request, exc: BaseError):
        """
        Handles BaseError exceptions by returning a JSON response with error details.

        This function is an exception handler for BaseError exceptions. It catches BaseError exceptions,
        extracts the error details, and returns a JSON response to the client with the error information.

        Args:
            request (Request): The incoming request that triggered the exception.
            exc (BaseError): The BaseError exception that was raised.

        Returns:
            JSONResponse: A JSON response containing the error details.
        """
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "name": exc.name,
                "message": exc.message,
                "status_code": exc.status_code,
            },
        )

    app.openapi = enrich_openapi(app, target_module=["main"])

    return app
