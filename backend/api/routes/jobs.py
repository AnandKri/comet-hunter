import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from queue import Queue, Empty
from typing import Generator
from dataclasses import asdict
import json
import time
from backend.jobs.background_job_service import BackgroundJobService
from backend.jobs.event_bus import EventBus
from backend.jobs.job_store import JobStore
from backend.api.dependencies import get_job_service, get_job_store, get_event_bus
from backend.api.dto.api_response import ApiSuccessResponse
from backend.api.dto.response_models import JobStatusResponse 
from backend.util.enums import JobStatus

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{job_id}", response_model=ApiSuccessResponse[JobStatusResponse])
def get_job(
    job_id: str,
    background_job_service: BackgroundJobService = Depends(get_job_service)
) -> ApiSuccessResponse[JobStatusResponse]:
    """
    Retrieve background job execution details.

    Returns:
    - current lifecycle status
    - result payload if completed
    - failure error if failed

    :param job_id:
        Unique identifier of the background job.

    :param background_job_service:
        Background job service dependency.

    :raises HTTPException:
        404 if job does not exist.

    :return:
        Standardized API response containing job details.
    """

    logger.info(
        "Job status requested",
        extra={"job_id": job_id}
    )

    try:

        job = background_job_service.get_job(job_id)

        if job is None:

            logger.warning(
                "Job not found",
                extra={"job_id": job_id}
            )

            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )

        logger.info(
            "Job status retrieved",
            extra={
                "job_id": job.id,
                "job_type": job.type,
                "job_status": job.status.value
            }
        )

        return ApiSuccessResponse[JobStatusResponse](
            data=JobStatusResponse(
                job_id=job.id,
                type=job.type.value,
                status=job.status.value,
                created_at=job.created_at,
                started_at=job.started_at,
                stopped_at=job.stopped_at,
                progress=job.progress,
                result=job.result,
                error=job.error
            )
        )

    except HTTPException:
        raise

    except Exception:

        logger.exception(
            "Failed to retrieve job status",
            extra={"job_id": job_id}
        )
        raise

@router.get("/{job_id}/events")
def stream_job_events(
    job_id: str,
    event_bus: EventBus = Depends(get_event_bus)
) -> StreamingResponse:
    """
    Stream real-time events using server-sent events.
    
    Responsibilities:
    - Subscribe client to job-specific event stream
    - Continously stream published events.
    - Cleanup subscription on client disconnect or job completion.

    Event format:
        "event": <event_type>,
        "data": <json_payload>
    
    Example streamed payload:
        "event": "progress",
        "data":{"download": 12}

    Notes:
    - Connection remains open until job completion or client disconnect.
    - Intended for real-time monitoring of long-running jobs.
    - Uses in-memory event bus subscriptions.
    - Each connected client gets dedicated queue.

    :param job_id:
        Unique identifier of the background job.
    
    :param event_bus:
        Shared event bus dependency.
    
    :return:
        StreamingResponse configured for server-sent events.
    """
    logger.info(
        "Job event stream requested",
        extra={"job_id": job_id}
    )

    def event_generator() -> Generator[str, None, None]:
        """
        Generate SSE-formatted event stream.

        Workflow:
        - Subscribe to event bus.
        - Wait for events.
        - Yield events in SSE format.
        - Cleanup / Disconnect.

        Yields:
            str: SSE-formatted event string.
        """

        queue = event_bus.subscribe(job_id)

        terminal_events = {
            "COMPLETED",
            "FAILED",
            "CANCELLED"
        }


        try:
            while True:
                try:
                    event = queue.get(timeout=5)

                    payload = asdict(event)
                    payload["job_status"] = payload["job_status"].value
                    payload["job_type"] = payload["job_type"].value
                    payload["timestamp"] = payload["timestamp"].isoformat()

                    yield (
                        f"event: {event.event}\n"
                        f"data: {json.dumps(payload)}\n\n"
                    )

                    if event.job_status in terminal_events:
                        break
                
                except Empty:
                    """
                    Heartbeat to keep connection alive.

                    Prevents:
                    - proxy timeout
                    - connection idle termination
                    """
                    yield ": keepalive\n\n"
                
                time.sleep(0.1)
        except GeneratorExit:
            logger.info(
                "job event stream disconnected",
                extra={"job_id": job_id}
            )
        finally:

            event_bus.unsubscribe(job_id, queue)
            logger.info(
                "job event subscription cleaned up",
                extra={"job_id": job_id}
            )
        
    return StreamingResponse(
        content = event_generator(),
        media_type = "text/event-stream",
        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/{job_id}/cancel", response_model=ApiSuccessResponse[dict])
def cancel_job(
    job_id: str,
    job_store: JobStore = Depends(get_job_store)
) -> ApiSuccessResponse[dict]:
    """
    Trigger cancellation request for a running job.

    Notes:
    - Cancellation is cooperative.
    - Actual job termination depends on cancellation checkpoints.
    """

    logger.info(
        "Job Cancellation triggered",
        extra={"job_id": job_id}
    )

    try:

        job = job_store.get_job(job_id)

        if not job:
            logger.warning(
                "Job not found",
                extra={"job_id": job_id}
            )

            raise HTTPException(
                status_code=404,
                detail="job not found"
            )
        
        job.cancel_event.set()

        job_store.update_job(
            job_id,
            JobStatus.CANCELLING
        )

        logger.info(
            "Job cancellation signal sent",
            extra={"job_id":job_id}
        )

        return ApiSuccessResponse(
            data={
                "job_id":job_id,
                "message":"Cancellation Signal Sent"
            }
        )
    
    except HTTPException:
        raise
    
    except Exception:
        logger.exception("Job cancellation failed")
        raise