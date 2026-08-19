class Commands:
    """
    Commands used in the "new" HTTP API
    """

    LIGHT_CONTROL_CMD = "lightControl_cmd"
    PRINTER_CONTROL_CMD = "printerCtl_cmd"
    JOB_CONTROL_CMD = "jobCtl_cmd"
    CIRCULATION_CONTROL_CMD = "circulateCtl_cmd"
    CAMERA_CONTROL_CMD = "streamCtrl_cmd"
    TEMP_CONTROL_CMD = "temperatureCtl_cmd"
    # AD5X + Creator 5 material-station slot metadata (name + color). Filament
    # load/unload (`ms_cmd`) stays AD5X-only — the Creator 5 firmware has no
    # `ms_cmd` (verified in the firmware).
    MATERIAL_STATION_CONFIG_CMD = "msConfig_cmd"
