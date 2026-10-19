"""log.py — append a measurement to measurements.json and check tolerance."""

import json
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path("measurements.json")


def load_measurements() -> list[dict]:
    """Read the log if it exists, else start with an empty list."""
    if LOG_FILE.exists():
        text = LOG_FILE.read_text(encoding="utf-8")
        return json.loads(text)
    return []


def save_measurements(measurements: list[dict]) -> None:
    """Write the whole list back, pretty-printed."""
    LOG_FILE.write_text(
        json.dumps(measurements, indent=2), encoding="utf-8"
    )


def record(part: str, expected_ohms: float, measured_ohms: float) -> dict:
    """Append one measurement and return that entry."""
    entry = {
        "part": part,
        "expected_ohms": expected_ohms,
        "measured_ohms": measured_ohms,
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    measurements = load_measurements()
    measurements.append(entry)
    save_measurements(measurements)
    return entry


def report_out_of_tolerance(measurements: list[dict], limit: float = 0.05) -> None:
    """Print every measurement that misses its nominal value by more than limit."""
    bad = 0
    for m in measurements:
        expected = m["expected_ohms"]
        measured = m["measured_ohms"]
        if expected == 0:
            continue
        error = abs(measured - expected) / expected
        if error > limit:
            bad += 1
            print(
                f"{m['part']}: expected {expected:.0f} Ω, "
                f"measured {measured:.0f} Ω → off by {error * 100:.1f} %"
            )
    print(f"{bad} of {len(measurements)} measurements out of {limit * 100:.0f} % tolerance")


if __name__ == "__main__":
    record("R1", 4700, 4688)
    print("Logged 1 measurement.")
    report_out_of_tolerance(load_measurements())
