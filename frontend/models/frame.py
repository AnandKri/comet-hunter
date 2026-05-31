from dataclasses import dataclass

@dataclass
class Frame:
    filename: str
    instrument: str
    observation_time: str
    image_path: str