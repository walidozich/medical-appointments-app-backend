from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import register_exception_handlers
from app.api_router import api_router
from app.core.envelope import ResponseEnvelopeMiddleware


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
    )

    # Standard response envelope
    app.add_middleware(ResponseEnvelopeMiddleware)

    # Add OpenAPI security scheme for refresh tokens (header `X-Refresh-Token`).
    # This makes the Swagger "Authorize" dialog allow entering a refresh token.
    from fastapi.openapi.utils import get_openapi

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version="1.0.0",
            routes=app.routes,
        )
        components = openapi_schema.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})
        security_schemes.setdefault(
            "RefreshToken",
            {
                "type": "apiKey",
                "name": "X-Refresh-Token",
                "in": "header",
            },
        )
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # CORS – adjust origins as needed
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # in prod, restrict this
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(api_router, prefix="/api/v1")

    # Exception handlers
    register_exception_handlers(app)

    return app


app = create_app()
