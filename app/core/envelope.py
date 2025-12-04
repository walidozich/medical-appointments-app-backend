import json
from typing import Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response


def make_envelope(data: Any = None, message: str | None = None, success: bool = True):
    return {"success": success, "data": data, "message": message}


class ResponseEnvelopeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)

        # Skip non-JSON responses or docs/openapi
        path = request.url.path
        if path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi"):
            return response
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        # Extract body
        raw_body: bytes = b""
        if getattr(response, "body", None) is not None:
            raw_body = response.body
        elif hasattr(response, "body_iterator"):
            chunks = [chunk async for chunk in response.body_iterator]
            raw_body = b"".join(chunks)

        try:
            payload = json.loads(raw_body.decode()) if raw_body else None
        except Exception:
            return response

        # Avoid double-wrapping
        if isinstance(payload, dict) and "success" in payload and "data" in payload:
            enveloped = payload
        else:
            is_success = 200 <= response.status_code < 400
            msg = None
            if not is_success and isinstance(payload, dict):
                msg = payload.get("detail") or payload.get("message")
            enveloped = make_envelope(data=payload, message=msg, success=is_success)

        headers = dict(response.headers)
        headers.pop("content-length", None)
        return JSONResponse(content=enveloped, status_code=response.status_code, headers=headers)
