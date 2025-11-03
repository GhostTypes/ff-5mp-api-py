"""
Shared printer response fixtures for unit tests.

These fixtures provide representative payloads returned by the FlashForge HTTP
and TCP APIs. Tests import these structures to avoid duplicating verbose sample
data and to keep scenarios consistent across modules.
"""

AD5X_INFO_RESPONSE = {
    "code": 0,
    "detail": {
        "name": "FlashForge AD5X",
        "firmwareVersion": "1.1.7-1.0.2",
        "ipAddr": "192.168.1.120",
        "macAddr": "AA:BB:CC:DD:EE:FF",
        "hasMatlStation": True,
        "matlStationInfo": {
            "currentLoadSlot": 1,
            "currentSlot": 1,
            "slotCnt": 4,
            "slotInfos": [
                {
                    "slotId": 1,
                    "hasFilament": True,
                    "materialName": "PLA",
                    "materialColor": "#FF0000",
                }
            ],
            "stateAction": 0,
            "stateStep": 0,
        },
        "status": "ready",
        "printLayer": 10,
        "estimatedTime": 3600,
        "printDuration": 600,
        "cumulativePrintTime": 1200,
        "cumulativeFilament": 123.45,
        "printProgress": 0.25,
        "estimatedRightLen": 5000,
        "estimatedRightWeight": 200,
        "autoShutdown": "close",
        "doorStatus": "close",
        "externalFanStatus": "open",
        "internalFanStatus": "close",
        "lightStatus": "open",
        "rightTemp": 215,
        "rightTargetTemp": 220,
        "platTemp": 55,
        "platTargetTemp": 60,
        "printFileName": "calibration_cube.gcode",
        "flashRegisterCode": "flash123",
        "polarRegisterCode": "polar456",
        "printSpeedAdjust": 0,
        "currentPrintSpeed": 100,
    },
}

FIVE_M_PRO_INFO_RESPONSE = {
    "code": 0,
    "detail": {
        "name": "Adventurer 5M Pro",
        "firmwareVersion": "3.2.0",
        "ipAddr": "192.168.1.140",
        "macAddr": "11:22:33:44:55:66",
        "hasMatlStation": False,
        "status": "ready",
        "printLayer": 0,
        "cumulativePrintTime": 500,
        "cumulativeFilament": 42.0,
        "printProgress": 0.0,
    },
}

FILE_LIST_AD5X_RESPONSE = {
    "code": 0,
    "gcodeListDetail": [
        {
            "gcodeFileName": "multi_color_test.3mf",
            "printingTime": 1800,
            "gcodeToolCnt": 2,
            "gcodeToolDatas": [
                {
                    "toolId": 0,
                    "slotId": 1,
                    "materialName": "PLA",
                    "materialColor": "#FF0000",
                    "filamentWeight": 15.5,
                },
                {
                    "toolId": 1,
                    "slotId": 2,
                    "materialName": "PLA",
                    "materialColor": "#0000FF",
                    "filamentWeight": 14.2,
                },
            ],
            "useMatlStation": True,
        }
    ],
}

FILE_LIST_5M_PRO_RESPONSE = {
    "code": 0,
    "gcodeList": ["benchy.gcode", "calibration_cube.gcode"],
}

THUMBNAIL_RESPONSE = {
    "code": 0,
    "imageData": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=",
}

PRODUCT_RESPONSE = {
    "code": 0,
    "product": {
        "lightCtrlState": 1,
        "internalFanCtrlState": 1,
        "externalFanCtrlState": 1,
        "chamberTempCtrlState": 1,
        "nozzleTempCtrlState": 1,
        "platformTempCtrlState": 1,
    },
}

PRINTER_INFO_REPLAY = (
    "ok M115\n"
    "Machine Type: Adventurer 5M Pro\n"
    "Machine Name: Shop Printer\n"
    "Firmware: V3.2.0\n"
    "SN: SNMOMC9900728\n"
    "X:220 Y:220 Z:220\n"
    "Tool count: 1\n"
    "Mac Address:11:22:33:44:55:66\n"
)

PRINTER_INFO_MINIMAL_REPLAY = (
    "ok M115\n"
    "Machine Type: Adventurer\n"
    "Machine Name: Bench\n"
    "Firmware: V1.0.0\n"
    "SN: SN123\n"
)

FILE_LIST_TCP_PRO = "/data/[FLASH]/file1.gcode::/data/[FLASH]/file2.gcode"
FILE_LIST_TCP_REGULAR = "/data/file a.gcode::/data/My File(1).gcode"
FILE_LIST_TCP_EMPTY = ""
