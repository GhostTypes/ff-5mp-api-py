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

# Creator 5 / Creator 5 Pro (/detail) payloads. The Creator 5 series is a
# 4-head tool-changer with no TCP/8899 service: it reports per-nozzle
# temperature arrays, an immutable factory `model`, and presence flags for
# the camera / lidar. Only the Pro variant (pid 41) has a real door sensor.
CREATOR_5_INFO_RESPONSE = {
    "code": 0,
    "detail": {
        "name": "Creator 5",
        "model": "Creator 5",
        "pid": 40,
        "firmwareVersion": "1.0.5",
        "ipAddr": "192.168.1.150",
        "macAddr": "AA:BB:CC:00:00:01",
        "status": "ready",
        "nozzleCnt": 4,
        "nozzleTemps": [200.0, 200.0, 200.0, 200.0],
        "nozzleTargetTemps": [210.0, 210.0, 210.0, 210.0],
        "rightTemp": 200,
        "rightTargetTemp": 210,
        "platTemp": 60,
        "platTargetTemp": 70,
        "chamberTemp": 45,
        "chamberTargetTemp": 50,
        "camera": 1,
        "lidar": 1,
        "doorStatus": "close",
        "autoShutdown": "close",
        "externalFanStatus": "open",
        "internalFanStatus": "close",
        "lightStatus": "open",
        "cumulativePrintTime": 800,
        "cumulativeFilament": 99.0,
        "printProgress": 0.0,
    },
}

CREATOR_5_PRO_INFO_RESPONSE = {
    "code": 0,
    "detail": {
        "name": "Creator 5 Pro",
        "model": "Creator 5 Pro",
        "pid": 41,
        "firmwareVersion": "1.0.5",
        "ipAddr": "192.168.1.151",
        "macAddr": "AA:BB:CC:00:00:02",
        "status": "printing",
        "nozzleCnt": 4,
        "nozzleTemps": [195.0, 200.0, 205.0, 210.0],
        "nozzleTargetTemps": [205.0, 210.0, 210.0, 215.0],
        "rightTemp": 195,
        "rightTargetTemp": 205,
        "platTemp": 65,
        "platTargetTemp": 75,
        "chamberTemp": 50,
        "chamberTargetTemp": 60,
        "camera": 1,
        "lidar": 1,
        "doorStatus": "open",
        "cameraStreamUrl": "",
        "estimatedTime": 3600,
        "printDuration": 600,
        "printProgress": 0.5,
        "estimatedRightLen": 5000,
        "estimatedRightWeight": 200,
        "printLayer": 50,
        "targetPrintLayer": 100,
        "printFileName": "multi_tool_benchy.3mf",
    },
}

# A Material Station block as the Creator 5 Pro reports it (pid 41, firmware
# 1.9.4). Note what is deliberately NOT here: `hasMatlStation`. That field is
# AD5X-only and the Creator 5 series omits it from /detail entirely, even with
# four loaded slots - so anything gating on the raw flag misses the station on
# exactly the models that have one. Merge into a /detail payload to cover that.
CREATOR_5_PRO_MATL_STATION_INFO = {
    "currentLoadSlot": 0,
    "currentSlot": 0,
    "slotCnt": 4,
    "slotInfos": [
        {"slotId": 1, "hasFilament": True, "materialName": "PLA", "materialColor": "#1B1B1B"},
        {"slotId": 2, "hasFilament": True, "materialName": "PETG", "materialColor": "#1B1B1B"},
        {"slotId": 3, "hasFilament": True, "materialName": "PLA", "materialColor": "#FFFFFF"},
        {"slotId": 4, "hasFilament": True, "materialName": "PLA", "materialColor": "#805003"},
    ],
    "stateAction": 0,
    "stateStep": 0,
}

# The same Creator 5 Pro material station, plus fields a firmware update might
# add at the station and slot level. FFPrinterDetail allows extras, but that is
# not sufficient on its own: a *child* model that forbids them fails validation
# for the whole /detail response, which Info.get_detail_response swallows into
# a None return.
CREATOR_5_PRO_MATL_STATION_UNKNOWN_FIELD = {
    **CREATOR_5_PRO_MATL_STATION_INFO,
    "someFutureStationField": "unrecognized",
    "slotInfos": [
        {**slot, "someFutureSlotField": 42} for slot in CREATOR_5_PRO_MATL_STATION_INFO["slotInfos"]
    ],
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

# The AD5X payload as a firmware update might one day send it: same data, plus a
# field this library has never heard of, at both the response and the entry level.
# The models must absorb those rather than fail validation - a failure here drops
# the caller to a names-only list and loses the metadata for every file, which is
# indistinguishable from a printer that genuinely reports names only.
FILE_LIST_AD5X_UNKNOWN_FIELD_RESPONSE = {
    "code": 0,
    "someFutureListField": "unrecognized",
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
            ],
            "useMatlStation": True,
            "someFutureEntryField": 42,
        }
    ],
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

# The /product payload as a firmware update might one day send it: the same
# control states, plus keys this library has never seen, at both the envelope
# and the nested `product` level. These must be absorbed rather than fail
# validation - send_product_command has no fallback, so a failure returns False,
# which every caller reads as the printer rejecting the check code.
PRODUCT_RESPONSE_UNKNOWN_FIELD = {
    "code": 0,
    "someFutureEnvelopeField": "unrecognized",
    "product": {
        **PRODUCT_RESPONSE["product"],
        "someFutureCtrlState": 1,
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
    "ok M115\nMachine Type: Adventurer\nMachine Name: Bench\nFirmware: V1.0.0\nSN: SN123\n"
)

FILE_LIST_TCP_PRO = "/data/[FLASH]/file1.gcode::/data/[FLASH]/file2.gcode"
FILE_LIST_TCP_REGULAR = "/data/file a.gcode::/data/My File(1).gcode"
FILE_LIST_TCP_EMPTY = ""
