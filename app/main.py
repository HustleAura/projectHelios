from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from fastapi import FastAPI

from app.firebase import init_firebase
from app.routers import analysis, daily_logs, targets


def run_migrations():
    """Run Alembic migrations to ensure the database schema is up to date."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: run database migrations
    print("[STARTUP] Running database migrations...")
    run_migrations()
    print("[STARTUP] Database migrations complete.")

    # Startup: initialize Firebase Admin SDK
    print("[STARTUP] Initializing Firebase Admin SDK...")
    init_firebase()
    print("[STARTUP] Firebase initialized. Ready to accept requests.")
    yield
    # Shutdown: nothing to clean up for now
    print("[SHUTDOWN] Application shutting down.")


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
