from fastapi import FastAPI

from app.routes.health import router as health_router
from app.routes.user_routes import router as user_router
from app.routes.trip_routes import router as trip_router
from app.core.database import init_db

app = FastAPI(title="Trip Planner Service", version="0.1.0")


# Include routers
app.include_router(health_router)
app.include_router(user_router)
app.include_router(trip_router)


@app.on_event("startup")
def _startup() -> None:
    # Create tables automatically for hackathon convenience
    init_db()
