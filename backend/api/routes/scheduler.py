import logging
from fastapi import APIRouter, Query, Depends
from backend.api.dependencies import get_scheduler
from backend.api.dto.api_response import ApiSuccessResponse
from backend.api.dto.response_models import SchedulerStatusResponse, SchedulerStartResponse, SchedulerStopResponse
from backend.util.enums import Instrument
from backend.pipeline.scheduler import Scheduler

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/status", response_model=ApiSuccessResponse[SchedulerStatusResponse])
def get_scheduler_status(
    scheduler: Scheduler = Depends(get_scheduler)
) -> ApiSuccessResponse[SchedulerStatusResponse]:
    """
    Returns current scheduler status details.
    """
    logger.debug("Scheduler status requested")

    try:
        result = scheduler.get_status()
        
        logger.debug(
            "Scheduler status checked",
            extra={
                "running": result.running,
                "next_run_at": str(result.next_run_at) if result.next_run_at else None,
                "next_run_in": str(result.next_run_in) if result.next_run_in else None
            }
        )

        return ApiSuccessResponse[SchedulerStatusResponse](
            data=SchedulerStatusResponse(
                running=result.running,
                next_run_at=result.next_run_at,
                next_run_in=result.next_run_in
            )
        )
    except Exception:
        logger.exception("Scheduler status check failed")
        raise

@router.post("/start", response_model=ApiSuccessResponse[SchedulerStartResponse])
def start_scheduler(
    instruments: list[Instrument] = Query(...),
    scheduler: Scheduler = Depends(get_scheduler)
) -> ApiSuccessResponse[SchedulerStartResponse]:
    """
    Starts scheduler if not already running to sync metadata and 
    download files for the given list of instruments

    returns start response
    """
    logger.info(
        "Scheduler start requested", 
        extra = {"instruments": instruments}
    )

    try:
        result = scheduler.start(instruments)

        if result.started:
            logger.info("Scheduler started")
        else:
            logger.warning("Scheduler already running")
        
        return ApiSuccessResponse[SchedulerStartResponse](
            data=SchedulerStartResponse(
                started = result.started,
                running = result.running
            )
        )
    
    except Exception:
        logger.exception("Scheduler start failed")
        raise

@router.post("/stop", response_model=ApiSuccessResponse[SchedulerStopResponse])
def stop_scheduler(
    scheduler: Scheduler = Depends(get_scheduler)
) -> ApiSuccessResponse[SchedulerStopResponse]:
    """
    Stops the scheduler if running

    returns stop response
    """
    logger.info("Scheduler stop requested")

    try:
        result = scheduler.stop()

        if result.stopped:
            logger.info("Scheduler stopped")
        else:
            logger.warning("Scheduler already stopped")

        return ApiSuccessResponse[SchedulerStopResponse](
            data=SchedulerStopResponse(
                stopped = result.stopped,
                running = result.running
            )
        )
    except Exception:
        logger.exception("Scheduler stop failed")
        raise