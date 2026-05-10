import logging
from fastapi import APIRouter, Depends
from backend.api.dto.api_response import ApiSuccessResponse
from backend.api.dto.response_models import SyncSlotsResponse
from backend.api.dependencies import get_pipeline
from backend.pipeline.pipeline import Pipeline

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/sync", response_model=ApiSuccessResponse[SyncSlotsResponse])
def sync_slots(
    pipeline: Pipeline = Depends(get_pipeline)
) -> ApiSuccessResponse[SyncSlotsResponse]:
    """
    Trigger slot synchronization

    Intended for:
    - Weekly refresh

    returns number of slots synced
    """
    logger.info("Slots sync triggered")

    try:
        result = pipeline.sync_slots()

        logger.info("Slots sync completed")

        return ApiSuccessResponse[SyncSlotsResponse](
            data=SyncSlotsResponse(
                status="completed",
                slots_synced=result.slots_synced
            )
        )
    
    except Exception:
        logger.exception("Slots sync failed")
        raise