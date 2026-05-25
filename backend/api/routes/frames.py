from fastapi import APIRouter, Query, Depends
from backend.api.dependencies import get_pipeline, get_job_service
from backend.util.enums import Instrument, JobType
from backend.api.dto.api_response import ApiSuccessResponse
from backend.api.dto.response_models import JobQueuedResponse, GetFramesResponse
from backend.pipeline.pipeline import Pipeline
from backend.jobs.background_job_service import BackgroundJobService
from backend.api.dto.serializers import serialize_get_frames_response
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=ApiSuccessResponse[GetFramesResponse])
def get_processed_frames(
    instrument: Instrument = Query(...),
    start: str = Query(..., description = "ISO UTC observation start time"),
    end: str = Query(..., description = "ISO UTC observation end time"),
    limit: int = Query(15, ge=1, le=100),
    offset: int = Query(0, ge=0),
    pipeline: Pipeline = Depends(get_pipeline)
) -> ApiSuccessResponse[GetFramesResponse]:
    """
    Retrieve of processed frames for a given observation window and instrument
    """
    logger.info(
        "Processed frames retrieval requested",
        extra={
            "instrument":instrument,
            "observation_start_utc":start,
            "observation_end_utc":end
        }
    )
    try:

        result = pipeline.get_processed_frames(
            instrument,
            start,
            end,
            limit,
            offset
        )

        logger.info("Processed frames retrieval successful")

        return ApiSuccessResponse[GetFramesResponse](
            data=serialize_get_frames_response(result)
        )
        
    except Exception:
        logger.exception("Processed frames retrieval failed")
        raise

@router.post("/sync", response_model=ApiSuccessResponse[JobQueuedResponse])
def sync_processed_frames(
    instrument: Instrument = Query(...),
    start: str = Query(..., description = "ISO UTC observation start time"),
    end: str = Query(..., description = "ISO UTC observation end time"),
    pipeline: Pipeline = Depends(get_pipeline),
    background_job_service: BackgroundJobService = Depends(get_job_service)
) -> ApiSuccessResponse[JobQueuedResponse]:
    """
    Trigger the job for syncing and updating processed frames based on 
    instrument and observation time

    - Triggers metadata sync
    - Downloads missing files
    - Processes eligible frames
    - Returns details of the sync operation including counts of metadata synced, files downloaded, frames marked ready and frames processed
    """
    logger.info(
        "Processed frames sync job requested",
        extra={
            "instrument":instrument,
            "observation_start_utc":start,
            "observation_end_utc":end
        }
    )
    try:
        job = background_job_service.submit(
            JobType.SYNC_PROCESSED_FRAMES,
            pipeline.sync_processed_frames,
            instrument,
            start,
            end
        )

        if job.existing:
            logger.warning("Processed frames sync job already running",
                           extra={"job_id": job.job.id})
        else:
            logger.info("Processed frames sync job queued",
                    extra={"job_id": job.job.id})

        return ApiSuccessResponse[JobQueuedResponse](
            data=JobQueuedResponse(
                job_id=job.job.id,
                existing=job.existing,
                status=job.job.status.value
            )
        )
    except Exception:
        logger.exception("Processed frames sync failed to start")
        raise