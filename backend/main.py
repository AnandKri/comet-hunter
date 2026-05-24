from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from backend.api.dto.api_response import ApiErrorResponse, ApiErrorDetail
from contextlib import asynccontextmanager
from backend.database.infrastructure.bootstrap import bootstrap_database
from backend.core.logging_config import setup_logging
from backend.api.dependencies import get_scheduler
from backend.api.routes import frames, slots, health, jobs, scheduler as scheduler_routes
from backend.api.middleware import LoggingMiddleware
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    bootstrap_database()
    yield
    scheduler = get_scheduler()
    scheduler.stop()

app = FastAPI(
    title="Comet Hunter API",
    lifespan=lifespan
)

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    
    response = ApiErrorResponse(
        error=ApiErrorDetail(
            code="VALIDATION_ERROR",
            message=str(exc)
        )
    )

    return JSONResponse(
        status_code=400,
        content=response.model_dump()
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    
    response = ApiErrorResponse(
        error=ApiErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="Unexpected server error"
        )
    )

    return JSONResponse(
        status_code=500,
        content=response.model_dump()
    )

app.add_middleware(LoggingMiddleware)

app.mount(
    "/media",
    StaticFiles(directory=PROCESSED_DIR),
    name="media"
)

app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(slots.router, prefix="/slots", tags=["Slots"])
app.include_router(scheduler_routes.router, prefix="/scheduler", tags=["Scheduler"])
app.include_router(frames.router, prefix="/frames", tags=["Frames"])
app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])