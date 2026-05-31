from dataclasses import dataclass

@dataclass
class ProcessedFile:
    processed_file_name: str
    instrument: str
    processed_file_url: str
    datetime_of_observation: str