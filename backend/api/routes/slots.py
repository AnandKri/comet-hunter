import logging
from fastapi import APIRouter, Depends
from backend.api.schemas import SyncSlotsResponse
from backend.api.dependencies import get_pipeline
from backend.pipeline.pipeline import Pipeline

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/sync", response_model=SyncSlotsResponse)
def sync_slots(
    pipeline: Pipeline = Depends(get_pipeline)
) -> SyncSlotsResponse:
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

        return SyncSlotsResponse(
            slots_synced=result.slots_synced
        )
    
    except Exception:
        logger.exception("Slots sync failed")
        raise