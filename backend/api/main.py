from fastapi import FastAPI
from contextlib import asynccontextmanager
from backend.database.infrastructure.bootstrap import bootstrap_database
from backend.logging_config import setup_logging
from backend.api.dependencies import get_scheduler
from backend.api.routes import frames, slots, health, scheduler as scheduler_routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    bootstrap_database()
    yield
    scheduler = get_scheduler()
    scheduler.shutdown()

app = FastAPI(
    title="Comet Hunter API",
    lifespan=lifespan
)

app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(slots.router, prefix="/slots", tags=["Slots"])
app.include_router(scheduler_routes.router, prefix="/scheduler", tags=["Scheduler"])
app.include_router(frames.router, prefix="/frames", tags=["Frames"])