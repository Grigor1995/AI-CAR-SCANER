"""Bounded correlation IDs; never accept arbitrary log-control characters."""
from contextvars import ContextVar
import re
from uuid import uuid4
correlation_id = ContextVar("correlation_id", default="")

def install(app):
    @app.middleware("http")
    async def correlate(request, call_next):
        incoming = request.headers.get("x-correlation-id", "")
        value = incoming if re.fullmatch(r"[A-Za-z0-9_-]{1,64}", incoming) else uuid4().hex
        token = correlation_id.set(value)
        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = value
            return response
        finally:
            correlation_id.reset(token)
