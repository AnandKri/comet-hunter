from fastapi import APIRouter, Query, Depends
from backend.api.dependencies import get_pipeline
from backend.api.dto.serializers import serialize_get_frames_response
from backend.util.enums import Instrument
from backend.api.dto.api_response import ApiSuccessResponse
from backend.api.dto.response_models import GetFramesResponse, SyncFramesResponse
from backend.pipeline.pipeline import Pipeline
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=ApiSuccessResponse[GetFramesResponse])
def get_processed_frames(
    instrument: Instrument = Query(...),
    start: str = Query(..., description = "ISO UTC observation start time"),
    end: str = Query(..., description = "ISO UTC observation end time"),
    pipeline: Pipeline = Depends(get_pipeline)
) -> ApiSuccessResponse[GetFramesResponse]:
    """
    Fetch processed frames for a given observation window and instrument
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
        result = pipeline.get_processed_frames(instrument, start, end)

        logger.info("Processed frames retrieved")

        return ApiSuccessResponse[GetFramesResponse](
            data=serialize_get_frames_response(result)
        )
    
    except Exception:
        logger.exception("Processed frames retrieval failed")
        raise

@router.post("/sync", response_model=ApiSuccessResponse[SyncFramesResponse])
def sync_processed_frames(
    instrument: Instrument = Query(...),
    start: str = Query(..., description = "ISO UTC observation start time"),
    end: str = Query(..., description = "ISO UTC observation end time"),
    pipeline: Pipeline = Depends(get_pipeline)
) -> ApiSuccessResponse[SyncFramesResponse]:
    """
    Sync and update processed frames based on instrument and observation time

    - Triggers metadata sync
    - Downloads missing files
    - Processes eligible frames
    - Returns details of the operation done
    """
    logger.info(
        "Processed frames sync requested",
        extra={
            "instrument":instrument,
            "observation_start_utc":start,
            "observation_end_utc":end
        }
    )
    try:
        result = pipeline.sync_processed_frames(instrument, start, end)

        logger.info("Processed frames synced")

        return ApiSuccessResponse[SyncFramesResponse](
            data=SyncFramesResponse(
                metadata_synced=result.metadata_synced,
                downloaded=result.downloaded,
                marked_ready=result.marked_ready,
                processed=result.processed
            )
        )
    except Exception:
        logger.exception("Processed frames sync failed")
        raise