import logging
from fastapi import APIRouter, Depends
from backend.api.dto.api_response import ApiSuccessResponse
from backend.api.dto.response_models import SlotResponse, JobQueuedResponse
from backend.api.dependencies import get_pipeline, get_job_service
from backend.pipeline.pipeline import Pipeline
from backend.jobs.background_job_service import BackgroundJobService
from backend.util.enums import JobType

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/sync", response_model=ApiSuccessResponse[JobQueuedResponse])
def sync_slots(
    pipeline: Pipeline = Depends(get_pipeline),
    background_job_service: BackgroundJobService = Depends(get_job_service)
) -> ApiSuccessResponse[JobQueuedResponse]:
    """
    Trigger slot synchronization

    Intended for:
    - Weekly refresh

    returns number of slots synced
    """
    logger.info("Slots sync job triggered")

    try:
        job = background_job_service.submit(JobType.SYNC_SLOTS, pipeline.sync_slots)

        logger.info("Slots sync job queued", 
                    extra={"job_id": job.id})

        return ApiSuccessResponse[JobQueuedResponse](
            data=JobQueuedResponse(
                job_id=job.id,
                status=job.status.value
            )
        )
    
    except Exception:
        logger.exception("Slots sync job failed to start")
        raise

@router.get("/active", response_model=ApiSuccessResponse[SlotResponse])
def get_active_slot(
    pipeline: Pipeline = Depends(get_pipeline)
) -> ApiSuccessResponse[SlotResponse]:
    """
    Get details of active slot if present
    """
    logger.info("Active slot fetch triggered")

    try:
        result = pipeline.get_active_slot()

        logger.info("Active slot fetch completed")

        return ApiSuccessResponse[SlotResponse](
            data=SlotResponse(
                start=result.start,
                end=result.end
            )
        )
    
    except Exception:
        logger.exception("Active slot fetch failed")
        raise

@router.get("/next-active", response_model=ApiSuccessResponse[SlotResponse])
def get_next_active_slot(
    pipeline: Pipeline = Depends(get_pipeline)
) -> ApiSuccessResponse[SlotResponse]:
    """
    Get details of next active slot if present
    """
    logger.info("Next active slot fetch triggered")
    
    try:
        result = pipeline.get_next_active_slot()

        logger.info("Next active slot fetch completed")
        return ApiSuccessResponse[SlotResponse](
            data=SlotResponse(
                start=result.start,
                end=result.end
            )
        )
    
    except Exception:
        logger.exception("Next active slot fetch failed")
        raise