import logging
from fastapi import APIRouter, Depends
from backend.api.dto.api_response import ApiSuccessResponse
from backend.api.dto.response_models import SlotResponse, SyncSlotsResponse
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