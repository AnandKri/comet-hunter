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
    Contains all the relevant URLs.
    Append date and instrument format after FITS_IMAGE_YYMMDD
    example : https://umbra.nascom.nasa.gov/pub/lasco/lastimage/level_05/260113/c3/
    """
    SCHEDULE = "https://soho.nascom.nasa.gov/operations/schedule/schedule.html"
    FTS_IMAGES_YYMMDD = "https://umbra.nascom.nasa.gov/pub/lasco/lastimage/level_05/"