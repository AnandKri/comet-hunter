import logging
from fastapi import APIRouter, Depends
from backend.api.dto.api_response import ApiSuccessResponse
from backend.api.dto.response_models import HealthResponse
from backend.api.dependencies import get_pipeline, get_scheduler
from backend.pipeline.pipeline import Pipeline
from backend.pipeline.scheduler import Scheduler
from backend.database.infrastructure.base import DatabaseBase

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=ApiSuccessResponse[HealthResponse])
def health(
    pipeline: Pipeline = Depends(get_pipeline),
    scheduler: Scheduler = Depends(get_scheduler)
) -> ApiSuccessResponse[HealthResponse]:
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
    
    scheduler_ok = scheduler is not None
    pipeline_ok = pipeline is not None
    healthy = db_ok and scheduler_ok and pipeline_ok
    status = "healthy" if healthy else "degraded"
    
    logger.debug(
        "Health check completed",
        extra={
            "status": status,
            "database": db_ok,
            "scheduler_initialized": scheduler_ok,
            "pipeline_initialized": pipeline_ok
        }
    )
    return ApiSuccessResponse[HealthResponse](
        data = HealthResponse(
            status=status,
            database=db_ok,
            scheduler_initialized=scheduler_ok,
            pipeline_initialized=pipeline_ok
        )
    )