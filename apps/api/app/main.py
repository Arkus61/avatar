from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import Response

from app.api.v1.routes_health import router as health_router

app = FastAPI(title="avatar-api", version="0.1.0")


@app.middleware("http")
async def trace_context_middleware(request: Request, call_next) -> Response:
    trace_id = str(uuid4())
    request.state.trace_id = trace_id
    print(f"[trace_id={trace_id}] {request.method} {request.url.path}")

    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response


app.include_router(health_router, prefix="/api/v1")
