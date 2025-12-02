from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        # You can customize this for unique constraint violations etc.
        return JSONResponse(
            status_code=400,
            content={"detail": "Database integrity error."},
        )

