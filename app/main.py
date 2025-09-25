from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db
from app.core.logger import log_info
from app.core.config import settings
from app.routes.chat_routes import router as chat_router
from app.routes.trip_routes import router as trip_router
from app.routes.user_routes import router as user_router


def _setup_langsmith():
    """Setup LangSmith tracing if configured."""
    if settings.langchain_tracing_v2 and settings.langsmith_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
        log_info("LangSmith tracing enabled", project=settings.langchain_project)
    else:
        log_info("LangSmith tracing disabled")


app = FastAPI(title="Trip Planner Service", version="0.1.0")

# Setup LangSmith tracing
_setup_langsmith()

# Include routers
app.include_router(user_router)
app.include_router(trip_router)
app.include_router(chat_router)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start = time.time()
    log_info("request", method=request.method, path=request.url.path)
    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)
    log_info(
        "response",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response


@app.on_event("startup")
def _startup() -> None:
    # Create tables automatically for hackathon convenience
    log_info("app starting - initializing database")
    try:
        init_db()
        log_info("database initialized successfully")
    except Exception as e:
        log_info("database initialization failed", error=str(e))
        log_info("app will continue without database features")
