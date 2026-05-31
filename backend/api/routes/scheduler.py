from fastapi import APIRouter, Query, Depends
from backend.api.dependencies import get_job_service, get_scheduler
from backend.api.dto.api_response import ApiSuccessResponse
from backend.api.dto.response_models import JobQueuedResponse
from backend.jobs.background_job_service import BackgroundJobService
from backend.util.enums import Instrument, JobType
from backend.pipeline.scheduler import Scheduler
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/start", response_model=ApiSuccessResponse[JobQueuedResponse])
def start_scheduler(
    instruments: list[Instrument] = Query(...),
    scheduler: Scheduler = Depends(get_scheduler),
    background_job_service: BackgroundJobService = Depends(get_job_service)
) -> ApiSuccessResponse[JobQueuedResponse]:
    """
    Trigger scheduler if not already running to sync metadata and 
    download files for the given list of instruments

    returns start response
    """
    logger.info(
        "Scheduler start requested", 
        extra = {"instruments": instruments}
    )

    try:
        job = background_job_service.submit(
            JobType.START_SCHEDULER,
            scheduler.start,
            instruments
        )

        if job.existing:
            logger.warning("Scheduler already running")
        else:
            logger.info("Scheduler started")

        return ApiSuccessResponse[JobQueuedResponse](
            data=JobQueuedResponse(
                job_id=job.job.id,
                existing=job.existing,
                status=job.job.status.value
            )
        )
    
    except Exception:
        logger.exception("Scheduler failed to start")
        raise