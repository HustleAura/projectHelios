from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.firebase import init_firebase
from app.routers import analysis, daily_logs, targets


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: initialize Firebase Admin SDK
    init_firebase()
    yield
    # Shutdown: nothing to clean up for now


app = FastAPI(
    title="Project Helios — Personal Health Daily Tracker",
    version="1.0.0",
    lifespan=lifespan,
)

# Register routers
app.include_router(targets.router, prefix="/api/v1", tags=["Targets"])
app.include_router(daily_logs.router, prefix="/api/v1", tags=["Daily Logs"])
app.include_router(analysis.router, prefix="/api/v1", tags=["Analysis"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
