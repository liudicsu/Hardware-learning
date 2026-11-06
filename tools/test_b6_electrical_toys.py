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

# Reference-temperature consistency, positive feedback, steady vs short heating.
assert w["R20"] == 1.0 and w["ALPHA20"] == .00393
assert w["resistance"](20.) == w["R20"]
assert math.isclose(w["resistance"](25.), 1.01965)
assert w["resistance"](70.) > w["resistance"](25.)
assert math.isclose(w["constant_power_rise"](10., 10000.), 10. * w["RTH"])
assert math.isclose(w["constant_power_rise"](10., .01), 10. * .01 / w["CTH"], rel_tol=.001)
steady = 4 * w["resistance"](w["AMBIENT"]) / (1 / w["RTH"] - 4 * w["R20"] * w["ALPHA20"])
assert math.isclose(w["constant_current_exact"](2., 10000.) - w["AMBIENT"], steady)

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

# Every physical RC edge is screened against ALL THREE published mode rise limits.
assert [mode for mode, _ in i["MODE_RISE_LIMITS"]] == ["Sm", "Fm", "Fm+"]
assert [round(limit * 1e9) for _, limit in i["MODE_RISE_LIMITS"]] == [1000, 300, 120]
assert [[r[3] for r in i["rise_screens"](row["tr"], slots)] for row in rows] == [
    [0, 36, 36], [0, 0, 36], [0, 36, 36]]
assert rows[0]["flags"] == 36  # Generic Sm rise-pass does NOT erase Fm waveform failure.

# Equal total C, series parasitics and SHARED placement inductance.
banks = d["BANKS"]
assert len({d["equivalent"](bank)[0] for bank in banks}) == 1
assert all(math.isclose(d["equivalent"](bank)[0], d["TOTAL_C"]) for bank in banks)
by_name = {bank.name: bank for bank in banks}
assert by_name["local_split"][1:5] == by_name["long_trace"][1:5]
assert by_name["local_single"].loop_nh == by_name["local_split"].loop_nh
assert by_name["local_single"].each_uf != by_name["local_split"].each_uf
segments = d["pulse_segments"]()
assert sum(end > start for _, start, end, _ in segments) == 9
assert sum(end < start for _, start, end, _ in segments) == 9
for bank in banks:
    cap, esr, inductance = d["equivalent"](bank)
    assert math.isclose(esr * bank.count, bank.each_esr)
    assert math.isclose(inductance, (bank.loop_nh + bank.each_esl_nh / bank.count) * 1e-9)
    assert d["component_srf"](bank) > d["srf"](bank)
    assert d["HF_HZ"] > d["component_srf"](bank)
    resonance = d["srf"](bank)
    assert abs(d["impedance"](bank, resonance).imag) < 1e-12
    assert math.isclose(abs(d["impedance"](bank, resonance)), esr)
    assert d["impedance"](bank, resonance / 10).imag < 0 < d["impedance"](bank, 10 * resonance).imag
    omega = 2 * math.pi * 10 * resonance
    assert math.isclose(omega * inductance / (1 / (omega * cap)), 100.)
    high_omega = 2 * math.pi * d["HF_HZ"]
    assert d["HF_HZ"] > 10 * resonance
    assert high_omega * bank.loop_nh * 1e-9 > esr + high_omega * bank.each_esl_nh / bank.count * 1e-9 + 1 / (high_omega * cap)
    # Discrete KCL/KVL residuals independently check signs, units and all RLC terms.
    u0, i0, load0, load1, dt = -.02, .05, .12, .13, .25e-9
    u1, i1 = d["step"](bank, u0, i0, load0, load1, dt)
    assert abs(cap * (u1 - u0) / dt + (i0 + i1) / 2) < 1e-8
    assert abs(inductance * (i1 - i0) / dt - ((u0 + u1) / 2 - (d["RFEED"] + esr) * (i0 + i1) / 2 + d["RFEED"] * (load0 + load1) / 2)) < 1e-8
    # Unforced shifted stored energy decreases by series/source dissipation.
    u1, i1 = d["step"](bank, u0, i0, 0., 0., dt)
    energy0 = .5 * cap * u0**2 + .5 * inductance * i0**2
    energy1 = .5 * cap * u1**2 + .5 * inductance * i1**2
    assert abs(energy1 - energy0 + dt * (d["RFEED"] + esr) * ((i0 + i1) / 2)**2) < 1e-20
    assert d["simulate"](bank, ((1e-6, 0., 0., 5e-9),)) == (3.3, 0., 3.3)
    minima = [d["simulate"](bank, segments, refine)[0] for refine in (1, 2, 4)]
    assert abs(minima[2] - minima[1]) < .3 * abs(minima[1] - minima[0])
    assert abs(minima[2] - minima[0]) < 4.1e-6
# A constant plateau discharges C even though di/dt=0: not the old L-only model.
def plateau(width):
    return ((20e-9, 0., .1, .5e-9), (width, .1, .1, .5e-9),
            (20e-9, .1, 0., .5e-9), (10e-6, 0., 0., 50e-9))
assert d["simulate"](by_name["local_split"], plateau(5e-6))[0] < d["simulate"](by_name["local_split"], plateau(500e-9))[0]
print("b6 reviewed: R20/alpha20 feedback, steady/short heat, real trips, three I2C rise limits, equal-C series RLC, SRF/loop dominance, KCL/KVL/passivity and grid convergence passed")
