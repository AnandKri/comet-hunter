from fastapi import APIRouter, Query, Depends
from backend.api.dependencies import get_scheduler
from backend.api.schemas import SchedulerStatusResponse, SchedulerStartResponse, SchedulerShutdownResponse
from backend.util.enums import Instrument
from backend.pipeline.scheduler import Scheduler

router = APIRouter()

@router.get("/status", response_model=SchedulerStatusResponse)
def get_scheduler_status(
    scheduler: Scheduler = Depends(get_scheduler)
) -> SchedulerStatusResponse:
    """
    Returns current scheduler status details.
    """
    result = scheduler.get_status()

    return SchedulerStatusResponse(
        running=result.running,
        next_run_at=result.next_run_at,
        next_run_in=result.next_run_in
    )

@router.post("/start", response_model=SchedulerStartResponse)
def start_scheduler(
    instruments: list[Instrument] = Query(...),
    scheduler: Scheduler = Depends(get_scheduler)
) -> SchedulerStartResponse:
    """
    Starts scheduler if not already running to sync metadata and 
    download files for the given list of instruments

    returns start response
    """
    result = scheduler.start(instruments)

    return SchedulerStartResponse(
        response = result.response
    )

@router.post("/shutdown", response_model=SchedulerShutdownResponse)
def shutdown_scheduler(
    scheduler: Scheduler = Depends(get_scheduler)
) -> SchedulerShutdownResponse:
    """
    Stops the scheduler if running

    returns shutdown response
    """
    result = scheduler.shutdown()

    return SchedulerShutdownResponse(
        response=result.response
    )