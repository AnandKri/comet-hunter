import logging
from fastapi import APIRouter, Depends, HTTPException
from backend.jobs.background_job_service import BackgroundJobService
from backend.api.dependencies import get_job_service
from backend.api.dto.api_response import ApiSuccessResponse
from backend.api.dto.response_models import JobStatusResponse

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