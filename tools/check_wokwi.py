#!/usr/bin/env python3
"""Check every examples/**/diagram.json against the Wokwi diagram format.

Standard library only. Exits 1 when any diagram has a problem.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Allowed part types and their pins.
# https://docs.wokwi.com/parts/wokwi-arduino-uno
# https://docs.wokwi.com/parts/wokwi-pushbutton
# https://docs.wokwi.com/parts/wokwi-potentiometer
# https://docs.wokwi.com/parts/wokwi-led
# https://docs.wokwi.com/parts/wokwi-resistor
# https://docs.wokwi.com/parts/wokwi-mpu6050
# https://docs.wokwi.com/parts/wokwi-logic-analyzer
# ESP32-S3 board: https://docs.wokwi.com/guides/esp32 and
# https://github.com/wokwi/wokwi-boards/blob/main/boards/esp32-s3-devkitc-1/board.json
ALLOWED = {
    "wokwi-arduino-uno": {
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
        "13", "A0", "A1", "A2", "A3", "A4", "A5",
        "GND.1", "GND.2", "GND.3", "5V", "VIN",
    },
    "board-esp32-s3-devkitc-1": {
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
        "13", "14", "15", "16", "17", "18", "19", "20", "21",
        "35", "36", "37", "38", "39", "40", "41", "42", "45", "46", "47", "48",
        "3V3.1", "3V3.2", "5V", "GND.1", "GND.2", "GND.3", "GND.4",
        "RST", "RX", "TX",
    },
    "wokwi-pushbutton": {"1.l", "1.r", "2.l", "2.r"},
    "wokwi-potentiometer": {"GND", "SIG", "VCC"},
    "wokwi-led": {"A", "C"},
    "wokwi-resistor": {"1", "2"},
    "wokwi-mpu6050": {"VCC", "GND", "SCL", "SDA", "XDA", "XCL", "AD0", "INT"},
    "wokwi-logic-analyzer": {
        "D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "GND",
    },
}

SERIAL_MONITOR = {"TX", "RX"}
BOARD_TYPES = {"wokwi-arduino-uno", "board-esp32-s3-devkitc-1"}


def check_diagram(path):
    problems = []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"cannot parse JSON: {exc}"]

    if not isinstance(data, dict):
        return ["top level is not a JSON object"]

    version = data.get("version")
    if type(version) is not int or version != 1:
        problems.append(f"version is {version!r}, expected 1")

    parts = data.get("parts")
    if not isinstance(parts, list):
        problems.append("parts is not a list")
        parts = []

    declared = {}
    board_count = 0

    for index, part in enumerate(parts):
        where = f"parts[{index}]"
        if not isinstance(part, dict):
            problems.append(f"{where} is not an object")
            continue

        part_id = part.get("id")
        part_type = part.get("type")

        if not isinstance(part_id, str) or not part_id:
            problems.append(f"{where} has no string id")
        if not isinstance(part_type, str) or not part_type:
            problems.append(f"{where} has no string type")

        if isinstance(part_id, str):
            if part_id in declared:
                problems.append(f"duplicate part id {part_id!r}")
            else:
                declared[part_id] = part_type

        if isinstance(part_type, str):
            if part_type not in ALLOWED:
                problems.append(f"{where} has unsupported type {part_type!r}")
            elif part_type in BOARD_TYPES:
                board_count += 1

            if part_type == "wokwi-pushbutton":
                attrs = part.get("attrs", {})
                if not isinstance(attrs, dict):
                    problems.append(f"{where} attrs is not an object")
                elif "bounce" in attrs:
                    problems.append(
                        f"{where} sets attrs.bounce; keep Wokwi's default bounce"
                    )

    if board_count != 1:
        problems.append(
            f"expected exactly one Uno or ESP32-S3 board part, found {board_count}"
        )

    connections = data.get("connections")
    if not isinstance(connections, list):
        problems.append("connections is not a list")
        connections = []

    for index, connection in enumerate(connections):
        where = f"connections[{index}]"
        if not isinstance(connection, list) or len(connection) != 4:
            problems.append(f"{where} is not a list of 4 items")
            continue

        endpoints = connection[:2]
        for endpoint in endpoints:
            if not isinstance(endpoint, str) or ":" not in endpoint:
                problems.append(f"{where} endpoint {endpoint!r} is not 'id:pin'")
                continue

            part_id, pin = endpoint.split(":", 1)
            if part_id == "$serialMonitor":
                if pin not in SERIAL_MONITOR:
                    problems.append(
                        f"{where} has invalid serial monitor pin {pin!r}"
                    )
                continue

            if part_id not in declared:
                problems.append(
                    f"{where} references undeclared part id {part_id!r}"
                )
                continue

            part_type = declared[part_id]
            if part_type in ALLOWED and pin not in ALLOWED[part_type]:
                problems.append(
                    f"{where} pin {pin!r} is not valid for {part_type}"
                )

    if not any(path.parent.glob("*.ino")):
        problems.append("no .ino sketch in the same directory")

    return problems


def main():
    paths = sorted((ROOT / "examples").rglob("diagram.json"))

    total_problems = 0
    for path in paths:
        try:
            relative = path.relative_to(ROOT)
        except ValueError:
            relative = path

        problems = check_diagram(path)
        if problems:
            total_problems += len(problems)
            print(f"FAIL {relative}")
            for problem in problems:
                print(f"  {problem}")
        else:
            print(f"ok {relative}")

    print(f"{len(paths)} diagrams checked, {total_problems} problems")
    return 1 if total_problems else 0


if __name__ == "__main__":
    sys.exit(main())
