from fastapi import FastAPI
from backend.api.routes import frames, slots, health, scheduler as scheduler_routes

app = FastAPI(title="Comet Hunter API")

app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(slots.router, prefix="/slots", tags=["Slots"])
app.include_router(scheduler_routes.router, prefix="/scheduler", tags=["Scheduler"])
app.include_router(frames.router, prefix="/frames", tags=["Frames"])