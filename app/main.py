from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import register_exception_handlers
from app.api_router import api_router


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
    )

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