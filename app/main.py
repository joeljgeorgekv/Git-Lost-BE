from fastapi import FastAPI

from app.routes.booking import router as booking_router

app = FastAPI(title="Booking Chatbot Service", version="0.1.0")


@app.get("/health")
def health() -> dict:
    """Simple health-check endpoint used for monitoring and tests."""
    return {"status": "ok"}


# Include routers (placeholders; no real endpoints yet)
app.include_router(booking_router, prefix="/booking")
