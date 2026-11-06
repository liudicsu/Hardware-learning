#!/usr/bin/env python3
"""Independent invariants for batch-6 PR1; synthetic physics, not hardware validation."""
import ast
import math
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent.parent
PATHS = (
    "examples/month-2/motors-drivers/winding_thermal_rc_toy.py",
    "examples/month-2/arduino-io/i2c_risetime_toy.py",
    "examples/month-1/components/supply_dip_decoupling_toy.py",
)
for path in PATHS:
    for node in ast.walk(ast.parse((ROOT / path).read_text())):
        if isinstance(node, ast.Import):
            assert all(item.name in {"math", "typing"} for item in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module in {"math", "typing"} and node.level == 0
w, i, d = [runpy.run_path(str(ROOT / path)) for path in PATHS]

# Shared demand: monitoring alone changes neither current nor physical temperature.
requests = w["current_profile"]()
assert len(requests) == 4800 and set(requests) == {1.0, 5.0}
assert [requests[k] for k in (0, 300, 340, 1500, 2400, 3600, 4200)] == [1, 5, 1, 5, 1, 5, 1]
a, b, c = [w["run"](arm, requests) for arm in w["ARMS"]]
assert a == b and a["peak"] > 150
assert c["trips"] == 2 and c["derate_samples"] > 0 and 0 < c["copper_j"] < a["copper_j"]
assert w["TRIP_C"] <= c["peak"] < w["TRIP_C"] + .1 and c["above_trip_s"] > 0
for r in (a, b, c):
    assert abs(w["CTH"] * (r["final"] - w["AMBIENT"]) - (r["copper_j"] - r["cooling_j"])) < 1e-8
zero = w["run"]("derate_trip", (0.,) * 4800)
assert zero["peak"] == w["AMBIENT"] and zero["copper_j"] == zero["trips"] == 0
errors = []
for dt in (.1, .05):
    temp = w["AMBIENT"]
    for _ in range(round(60 / dt)):
        temp = w["advance"](temp, 2., dt)[0]
    errors.append(abs(temp - w["constant_current_exact"](2., 60.)))
assert errors[1] < errors[0] < .02, errors
fine = w["run"]("derate_trip", w["current_profile"](.05), .05)
assert fine["trips"] == 2 and abs(fine["peak"] - c["peak"]) < .05

# Independent bisection on the waveform, rather than repeating the rise formula.
slots = i["scl_slots"](i["MESSAGE"])
assert len(slots) == 36 and slots.count(None) == 4
assert i["LOW_S"] >= 1300e-9
rows = []
for _, rp, wire_pf in i["ARMS"]:
    cbus = i["capacitance"](wire_pf)
    tau = rp * cbus
    def crossing(level):
        lo, hi = 0., 20 * tau
        for _ in range(60):
            mid = (lo + hi) / 2
            if 1 - math.exp(-mid / tau) < level:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2
    r = i["evaluate"](rp, cbus, slots)
    assert abs(r["tr"] - (crossing(.7) - crossing(.3))) < 1e-15
    assert math.isclose(r["fraction"], r["tr"] * i["F_HZ"])
    rows.append(r)
assert [r["flags"] for r in rows] == [36, 0, 36]
assert all(r["sink_ok"] for r in rows)
assert rows[1]["high"] > i["MIN_HIGH_S"] and rows[0]["high"] == rows[2]["high"] == 0
assert rows[2]["rp_max"] < rows[2]["rp_min"]
assert not i["evaluate"](100., i["capacitance"](40), slots)["sink_ok"]
# Longer bit time does not silently relax a fixed device-mode rise-time bound.
assert i["evaluate"](10000., i["capacitance"](40), slots, 100000.)["flags"] == 36

# Only L*di/dt; identical edges for all loops, include idle and falling-edge overshoot.
edges = d["pulse_train"]()
assert len(edges) == 18 and sum(e.di_dt > 0 for e in edges) == 9
assert sum(e.di_dt < 0 for e in edges) == 9
assert tuple(sorted(e.time_s for e in edges)) == tuple(e.time_s for e in edges)
assert d["evaluate"](0., edges) == (3.3, 0.)
for _, loop in d["LOOPS_NH"]:
    minimum, dip = d["evaluate"](loop, edges)
    assert math.isclose(dip, loop * 1e-9 * 8e6)
    assert math.isclose(minimum + dip, d["VRAIL"])
    assert math.isclose(d["evaluate"](2 * loop, edges)[1], 2 * dip)
    steeper = tuple(d["Edge"](e.time_s, 2 * e.di_dt) for e in edges)
    assert math.isclose(d["evaluate"](loop, steeper)[1], 2 * dip)
    assert max(d["VRAIL"] - loop * 1e-9 * e.di_dt for e in edges) > d["VRAIL"]
print("b6 PR1: stdlib, shared inputs, physical blind/monitor equivalence, real derate trips, energy/analytic/refinement checks, independent RC crossings, sink/budget separation, signed L-only edges passed")
