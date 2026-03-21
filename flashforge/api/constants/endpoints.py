from typing import Final


CAMERA_STREAM_PORT: Final[int] = 8080


class Endpoints:
    """
    Endpoints for the "new" HTTP API
    """

    CONTROL = "/control"
    DETAIL = "/detail"
    GCODE_LIST = "/gcodeList"
    GCODE_PRINT = "/printGcode"
    GCODE_THUMB = "/gcodeThumb"
    PRODUCT = "/product"
    UPLOAD_FILE = "/uploadGcode"
