from fastapi import APIRouter, Query, Depends
from backend.api.dependencies import get_pipeline
from backend.util.enums import Instrument
from backend.api.schemas import FramesResponse, ProcessedFileResponse
from backend.pipeline.pipeline import Pipeline
from datetime import datetime

router = APIRouter()

@router.get("/get_processed_frames", response_model=FramesResponse)
def get_processed_frames(
    instrument: Instrument = Query(...),
    start: str = Query(..., description = "ISO UTC observation start time"),
    end: str = Query(..., description = "ISO UTC observation end time"),
    pipeline: Pipeline = Depends(get_pipeline)
) -> FramesResponse:
    """
    Fetch processed frames for a given observation window and instrument

    - Triggers metadata sync
    - Downloads missing files
    - Processes eligible frames
    - Returns processed file details
    """

    result = pipeline.get_processed_frames(instrument, start, end)

    files = [
        ProcessedFileResponse(
            processed_file_name = file.processed_file_name,
            instrument = file.instrument,
            processed_file_path = file.processed_file_path,
            datetime_of_observation=datetime.fromisoformat(file.datetime_of_observation)
        )
        for file in result.processed_files
    ]

    return FramesResponse(
        metadata_synced=result.metadata_synced,
        downloaded=result.downloaded,
        marked_ready=result.marked_ready,
        processed=result.processed,
        files=files
    )