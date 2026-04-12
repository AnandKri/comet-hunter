from datetime import datetime
from backend.util.enums import Instrument

class DB:
    """
    Contains database and table names
    """
    NAME = "comet-hunter"
    DOWNLINK_SLOT = "downlink_slot"
    PROCESSED_FILE = "processed_file"
    FILE_METADATA = "file_metadata"

class Url:
    """
    URL builder utility for LASCO data endpoints
    """

    SCHEDULE = "https://soho.nascom.nasa.gov/operations/schedule/schedule.html"
    BASE = "https://umbra.nascom.nasa.gov/pub/lasco/lastimage/level_05"
    METADATA_FILE = "img_hdr.txt"

    @staticmethod
    def _format_date(dt: str) -> str:
        """
        Convert ISO datetime -> YYMMDD format
        
        Example:
        2026-04-12T14:15:25 -> 260412

        :param dt: date which needs to be converted
        :return: returns date in valid format to append in url 
        """

        return datetime.fromisoformat(dt).strftime("%y%m%d")

    @classmethod
    def build_base_path(cls, dt: str, instrument: Instrument) -> str:
        """
        Builds base path:
        .../level_05/<yymmdd>/<instrument>/
        
        :param dt: date
        :param instrument: coronagraph (Instrument enum type)
        :return: returns the base url
        """
        
        date_part = cls._format_date(dt)
        return f"{cls.BASE}/{date_part}/{instrument.value}/"

    @classmethod
    def build_metadata_url(cls, dt: str, instrument: Instrument) -> str:
        """
        Metadata URL

        :param dt: date
        :param instrument: coronagraph
        :return: returns metadata url
        """

        return cls.build_base_path(dt, instrument) + cls.METADATA_FILE

    @classmethod
    def build_fits_url(cls, dt: str, instrument: Instrument, filename: str) -> str:
        """
        FITS file URL

        :param dt: date
        :param instrument: coronagraph
        :param filename: raw filename (as mentioned in metadata) with extension
        :return: returns file download url
        """

        return cls.build_base_path(dt, instrument) + filename