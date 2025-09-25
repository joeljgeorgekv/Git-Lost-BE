from fastapi import FastAPI, Request
import time

from app.core.logger import log_info

from app.routes.health import router as health_router
from app.routes.user_routes import router as user_router
from app.routes.trip_routes import router as trip_router
from app.core.database import init_db
from app.routes.clean_chat_routes import router as chat_router
from app.routes.travel_planning_routes import router as travel_router

app = FastAPI(title="Trip Planner Service", version="0.1.0")


# Include routers
app.include_router(health_router)
app.include_router(user_router)
app.include_router(trip_router)
app.include_router(chat_router)
app.include_router(travel_router)


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
