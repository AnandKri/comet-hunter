from backend.api.dto.response_models import GetFramesResponse, ProcessedFileResponse
from backend.database.domain.processed_file import ProcessedFile
from backend.pipeline.models import GetProcessedFramesResult

def serialize_processed_file(
    file: ProcessedFile
) -> ProcessedFileResponse:
    """
    Converts ProcessedFile domain model to ProcessedFileResponse DTO
    """

    return ProcessedFileResponse(
        processed_file_name=file.processed_file_name,
        instrument=file.instrument,
        processed_file_url=f"/media/{str(file.processed_file_name)}",
        datetime_of_observation=file.datetime_of_observation
    )

def serialize_get_frames_response(result: GetProcessedFramesResult) -> GetFramesResponse:
    """
    Converts GetProcessedFramesResult pipeline result domain model to GetFramesResponse DTO
    """
    return GetFramesResponse(
        files=[
            serialize_processed_file(file) 
            for file in result.processed_files
        ],
        total=result.total,
        limit=result.limit,
        offset=result.offset
    )