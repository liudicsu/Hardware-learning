#!/usr/bin/env python3
"""Synthetic RS-485 line toy: lossy transmission-line bounce lattice + UART
(8N1) receiver. NOT a TDR measurement, NOT Modbus, NOT a CAN error counter.
Stdlib only.

Every arm sends the SAME 16 bytes at the SAME baud through the SAME Thevenin
driver (+-5 V open-circuit, 20 ohm, 100 ns linear edge), the same 120 m trunk
(Z0 = 120 ohm, velocity 0.78 c, 0.95 amplitude per pass) and the same per-seed
noise streams (common-mode and differential). Arms differ only in line
arrangement / receiver type:
  A_term_diff     120 ohm at both trunk ends, differential receiver (+-200 mV)
  B_unterm_diff   no termination, differential receiver
  B2_stub_diff    both ends terminated, receiver on a 15 m unterminated stub
  C_term_single   same terminated trunk, but one wire against ground: the
                  receiver sees the full common-mode noise (threshold at
                  half swing +- 200 mV hysteresis)
Differential receivers see 1 % of the common-mode noise (synthetic mismatch).
A 0 -> 1 noise glitch can create a false start bit: this is how ringing and
noise turn into byte errors in a UART receiver that samples mid-bit.
"""
import math
import random

Z0 = 120.0
RS = 20.0
VOPEN = 5.0
EDGE_NS = 100.0
VEL = 0.78 * 299_792_458.0
TRUNK_M = 120.0
STUB_M = 15.0
LOSS = 0.95
RIN = 12_000.0           # one unit load, receiver input
VTH = 0.2
CM_SIGMA = 2.0       # V, within the -7..+12 V common-mode range
CM_TAU_NS = 200.0
DIFF_SIGMA = 0.08
CM_LEAK = 0.01
PAYLOAD = bytes(b"RS485\x00\xff\x55\xaa\x0f\xf0 A/B!\n")
SEEDS = (0, 1, 2, 3, 4)
SCENARIOS = (("1Mbps", 1_000_000, 5.0), ("125kbps", 125_000, 20.0))
ARMS = ("A_term_diff", "B_unterm_diff", "B2_stub_diff", "C_term_single")


def par(a, b):
    return a * b / (a + b)


def bits_of(payload):
    out = [1] * 12                     # idle
    for byte in payload:
        out.append(0)                  # start
        out += [(byte >> k) & 1 for k in range(8)]   # LSB first
        out.append(1)                  # stop
    return out + [1] * 12


def drive(bits, spb, dt):
    """Thevenin open-circuit voltage with a linear edge of EDGE_NS."""
    edge = max(1, int(round(EDGE_NS / dt)))
    v = []
    level = VOPEN if bits[0] else -VOPEN
    for b in bits:
        target = VOPEN if b else -VOPEN
        start = level
        for k in range(spb):
            v.append(start + (target - start) * min(1.0, (k + 1) / edge))
        level = target
    return v


def lattice(vs, dt, arm):
    """Bounce-diagram simulation. Returns receiver differential voltage."""
    single = arm == "C_term_single"
    term = arm != "B_unterm_diff"
    stub = arm == "B2_stub_diff"
    rt_near = Z0 if term else None
    rth = par(RS, rt_near) if rt_near else RS
    gain = rt_near / (rt_near + RS) if rt_near else 1.0
    gs = (rth - Z0) / (rth + Z0)
    t1 = max(1, int(round(TRUNK_M / VEL / (dt * 1e-9))))
    t2 = max(1, int(round(STUB_M / VEL / (dt * 1e-9)))) if stub else 0
    r_tap = Z0 if term else RIN
    n = len(vs)
    fwd = [0.0] * n        # launched forward on trunk at source
    back = [0.0] * n       # launched backward on trunk at tap
    s_fwd = [0.0] * n      # launched forward into stub at tap
    rx = [0.0] * n
    g_rx = (RIN - Z0) / (RIN + Z0)
    for k in range(n):
        b_arr = LOSS * back[k - t1] if k >= t1 else 0.0
        fwd[k] = vs[k] * gain * Z0 / (rth + Z0) + gs * b_arr
        a = LOSS * fwd[k - t1] if k >= t1 else 0.0
        if stub:
            c = g_rx * s_fwd[k - t2] if k >= t2 else 0.0
            ytot = 2 / Z0 + 1 / r_tap
            v = 2 * (a / Z0 + c / Z0) / ytot
            back[k] = v - a
            s_fwd[k] = v - c
            rx[k] = (1 + g_rx) * s_fwd[k - t2] if k >= t2 else 0.0
        else:
            ytot = 1 / Z0 + 1 / r_tap
            v = 2 * (a / Z0) / ytot
            back[k] = v - a
            rx[k] = v
    return rx, t1 + t2


def noise(n, dt, seed):
    rng_cm = random.Random(10_000 + seed)
    rng_d = random.Random(20_000 + seed)
    a = math.exp(-dt / CM_TAU_NS)
    scale = CM_SIGMA * math.sqrt(1 - a * a)
    cm, d, x = [], [], rng_cm.gauss(0, CM_SIGMA)
    for _ in range(n):
        x = a * x + scale * rng_cm.gauss(0, 1)
        cm.append(x)
        d.append(rng_d.gauss(0, DIFF_SIGMA))
    return cm, d


def receive(v, single, swing):
    """Comparator with hysteresis -> logic stream."""
    hi, lo = (swing / 2 + VTH, swing / 2 - VTH) if single else (VTH, -VTH)
    state, out = 1, []
    for x in v:
        if x >= hi:
            state = 1
        elif x <= lo:
            state = 0
        out.append(state)
    return out


def uart_decode(logic, spb):
    out, framing, k = [], 0, 0
    n = len(logic)
    while k < n - 10 * spb:
        if logic[k] == 0 and logic[k - 1] == 1:
            if logic[k + spb // 2] != 0:
                k += 1
                continue              # glitch rejected by half-bit check
            byte = 0
            for j in range(8):
                byte |= logic[k + spb // 2 + (j + 1) * spb] << j
            if logic[k + spb // 2 + 9 * spb] != 1:
                framing += 1
            out.append(byte)
            k += spb // 2 + 9 * spb
        else:
            k += 1
    return out, framing


def byte_errors(sent, got):
    errs = sum(a != b for a, b in zip(sent, got)) + abs(len(sent) - len(got))
    first = next((j for j, (a, b) in enumerate(zip(sent, got)) if a != b), None)
    if first is None and len(sent) != len(got):
        first = min(len(sent), len(got))
    return errs, first


def run(arm, baud, dt, seed):
    spb = int(round(1e9 / baud / dt))
    bits = bits_of(PAYLOAD)
    vs = drive(bits, spb, dt)
    line, delay = lattice(vs, dt, arm)
    n = len(line)
    skip = 6 * spb   # ignore the power-up charging of the line during idle
    dc = line[skip - 1]   # settled idle (logic 1) level at the receiver
    cm, dn = noise(n, dt, seed)
    single = arm == "C_term_single"
    if single:
        # one wire swings 0..2*level, referenced to ground; same driver
        sig = [x + abs(dc) for x in line]
        rxv = [s + c for s, c in zip(sig, cm)]
        swing = 2 * abs(dc)
    else:
        rxv = [x + CM_LEAK * c + d for x, c, d in zip(line, cm, dn)]
        swing = 0.0
    logic = receive(rxv[skip:], single, swing)
    got, framing = uart_decode([1] + logic, spb)
    errs, first = byte_errors(PAYLOAD, bytes(got))
    sent_edges = sum(1 for a, b in zip(bits, bits[1:]) if a != b)
    rx_edges = sum(1 for a, b in zip(logic, logic[1:]) if a != b)
    # eye margin at the bit centres as seen by the receiver (after the line delay)
    edge = int(round(EDGE_NS / dt))
    centres = [(j * spb + spb // 2 + delay + edge // 2, bits[j]) for j in range(6, len(bits))]
    margin = min((rxv[c] - swing / 2) * (1 if b else -1) for c, b in centres if c < n) - VTH
    overshoot = max(abs(x) for x in line[skip:]) / max(abs(dc), 1e-9)
    idle_ma = 1000 * VOPEN / (RS + (Z0 / 2 if arm != "B_unterm_diff" else RIN))
    return errs, first, framing, rx_edges - sent_edges, margin, overshoot, idle_ma


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def main():
    print("Synthetic RS-485 bounce-lattice + UART 8N1 toy; driver/cable values are lesson values, not a datasheet")
    print(f"Z0={Z0:.0f}ohm Rs={RS:.0f}ohm Voc=+-{VOPEN:.0f}V edge={EDGE_NS:.0f}ns trunk={TRUNK_M:.0f}m stub={STUB_M:.0f}m "
          f"v=0.78c one_way_ns={TRUNK_M / VEL * 1e9:.0f} loss/pass={LOSS} Rx_threshold=+-{VTH * 1000:.0f}mV")
    print(f"shared payload={len(PAYLOAD)} bytes ({PAYLOAD.hex()}) noise: cm_sigma={CM_SIGMA}V tau={CM_TAU_NS:.0f}ns "
          f"diff_sigma={DIFF_SIGMA}V cm_leak={CM_LEAK:.0%} seeds={len(SEEDS)}")
    print("scenario arm byte_errors framing_errors extra_edges eye_margin_V overshoot_x idle_drive_mA first_error_byte (mean+-sd)")
    for name, baud, dt in SCENARIOS:
        for arm in ARMS:
            rows = [run(arm, baud, dt, s) for s in SEEDS]
            firsts = [r[1] for r in rows]
            cols = [mean_sd([r[j] for r in rows]) for j in (0, 2, 3, 4, 5, 6)]
            fe = ",".join("-" if f is None else str(f) for f in firsts)
            print(f"{name} {arm} " + " ".join(f"{m:.2f}+-{s:.2f}" for m, s in cols) + f" [{fe}]")
    print("No winner is declared: termination costs idle drive current; low baud hides reflections")
    print("Real transceiver, cable and TDR: 本页未运行; SLLA272 numbers 以原文为准")


if __name__ == "__main__":
    main()
