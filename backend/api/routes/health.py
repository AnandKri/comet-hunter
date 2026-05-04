import logging
from fastapi import APIRouter, Depends
from backend.api.schemas import HealthResponse
from backend.api.dependencies import get_pipeline, get_scheduler
from backend.pipeline.pipeline import Pipeline
from backend.pipeline.scheduler import Scheduler
from backend.database.infrastructure.base import DatabaseBase

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=HealthResponse)
def health(
    pipeline: Pipeline = Depends(get_pipeline),
    scheduler: Scheduler = Depends(get_scheduler)
):
    """
    Checks server health and verifies initialization of
    - database connectivity
    - scheduler status
    - pipeline availability
    """
    logger.debug("Health check requested")
    try:
        with DatabaseBase.get_connection() as conn:
            conn.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False
    logger.debug(
        "Health check completed",
        extra={
            "database": db_ok,
            "scheduler_initialized": scheduler is not None,
            "pipeline_initialized": pipeline is not None
        }
    )
    return HealthResponse(
        database=db_ok,
        scheduler_initialized=scheduler is not None,
        pipeline_initialized=pipeline is not None
    )