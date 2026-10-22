"""encoder_sim.py: a 6-pole magnetic disc read by two Hall sensors, decoded x1, x2 and x4.

Hardware (Pololu Romi encoder, item #3542): a 6-pole magnetic disc on the motor's rear shaft,
two Hall sensors on the encoder board, 12 counts per motor-shaft revolution when both edges of
both channels are counted. Gearbox: Pololu item #1520, 120:1 nominal, 119.76:1 exact.
The sensor offset of a quarter magnetic period is the standard quadrature layout.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from one_rev_sim import COUNTS_PER_REV, K_SPEED, closed_loop  # noqa: E402
from cascade_sim import COUNTS_PER_TURN as CASCADE_COUNTS  # noqa: E402

POLES = 6                          # magnetic poles on the disc (N, S, N, S, N, S)
PERIOD_DEG = 360 / (POLES // 2)    # one N+S pair = one full square-wave period: 120 deg
OFFSET_DEG = PERIOD_DEG / 4        # sensor B sits a quarter period (30 deg) behind sensor A
GEAR_NOMINAL = 120
GEAR_EXACT = (22 * 38 * 44 * 26 * 30) / (10 * 11 * 11 * 22 * 9)
WHEEL_D_MM = 70.0                  # Romi chassis: 70 x 8 mm wheels
# Same table as QDEC[] in one_rev.ino: index = previous AB (2 bits) then new AB (2 bits)
QDEC = [0, -1, +1, 0, +1, 0, 0, -1, -1, 0, 0, +1, 0, +1, -1, 0]


def hall(angle_deg):
    """A Hall sensor output: 1 over a north pole, 0 over a south pole."""
    return 1 if (angle_deg % PERIOD_DEG) < PERIOD_DEG / 2 else 0


def ab(angle_deg):
    """The two-bit state AB for a given motor-shaft angle."""
    return (hall(angle_deg) << 1) | hall(angle_deg - OFFSET_DEG)


def bits(s):
    return f"{s >> 1}{s & 1}"


def run(angles):
    """Feed successive shaft angles to the decoder; return (count, illegal jumps, rows)."""
    count, illegal, rows = 0, 0, []
    last = ab(angles[0])
    for a in angles[1:]:
        s = ab(a)
        if s != last:
            if (s ^ last) == 0b11:
                illegal += 1
            count += QDEC[(last << 2) | s]
            rows.append((a, bits(last), bits(s), QDEC[(last << 2) | s], count))
        last = s
    return count, illegal, rows


def edges_per_rev():
    """Count x1 (rising A), x2 (both A edges) and x4 (both edges of A and B) per motor turn."""
    x1 = x2 = x4 = 0
    prev = ab(0.5)
    for i in range(1, 3601):
        s = ab(0.5 + i * 0.1)
        a0, a1, b0, b1 = prev >> 1, s >> 1, prev & 1, s & 1
        x1 += a0 == 0 and a1 == 1
        x2 += a0 != a1
        x4 += (a0 != a1) + (b0 != b1)
        prev = s
    return x1, x2, x4


if __name__ == "__main__":
    print(f"disc: {POLES} poles -> {POLES // 2} square-wave periods per motor turn, "
          f"{PERIOD_DEG:.0f} deg each; sensor B offset {OFFSET_DEG:.0f} deg = 1/4 period = 90 deg phase")
    fwd = [0.5 + i * 0.5 for i in range(721)]
    count, bad, rows = run(fwd)
    print("forward, first period:")
    for a, p, s, d, c in rows[:4]:
        print(f"  {a:6.1f} deg  AB {p} -> {s}  {d:+d}  count {c}")
    print(f"forward, one motor turn: count {count:+d}, illegal jumps {bad}")
    count, bad, rows = run(fwd[::-1])
    print("reverse, first period:")
    for a, p, s, d, c in rows[:4]:
        print(f"  {a + 0.5:6.1f} deg  AB {p} -> {s}  {d:+d}  count {c}")
    print(f"reverse, one motor turn: count {count:+d}, illegal jumps {bad}")
    slow = [0.5 + i * 60 for i in range(7)]
    count, bad, _ = run(slow)
    print(f"sampled every 60 deg (too slow): count {count:+d}, illegal jumps {bad} (should be +12)")
    x1, x2, x4 = edges_per_rev()
    print(f"counts per motor turn: x1 {x1}, x2 {x2}, x4 {x4}  "
          f"({POLES // 2} pulses x 2 edges x 2 channels = {POLES // 2 * 2 * 2})")
    print(f"counts per output-shaft turn: x1 {x1 * GEAR_NOMINAL}, x2 {x2 * GEAR_NOMINAL}, "
          f"x4 {x4 * GEAR_NOMINAL} (gear {GEAR_NOMINAL}:1, one_rev uses {COUNTS_PER_REV})")
    exact = x4 * GEAR_EXACT
    circ = math.pi * WHEEL_D_MM
    print(f"exact gear {GEAR_EXACT:.2f}:1 -> {exact:.1f} counts per wheel turn; "
          f"1440 counts = {COUNTS_PER_REV / exact:.4f} turn, {(COUNTS_PER_REV - exact) / exact * circ:.2f} mm too far")
    print(f"wheel {WHEEL_D_MM:.0f} mm: circumference {circ:.2f} mm, {circ / COUNTS_PER_REV:.4f} mm per count")
    v = K_SPEED * 8.4 * 0.6
    window = 0.05
    n = round(v * window)
    print(f"one_rev model at 8.4 V, duty 0.6: {v:.1f} counts/s; in a {window * 1000:.0f} ms window "
          f"{v * window:.2f} -> {n} counts")
    rev_s = n / window / COUNTS_PER_REV
    print(f"  {n} counts / {window:.2f} s / {COUNTS_PER_REV} = {rev_s:.4f} wheel rev/s = {rev_s * 60:.1f} rpm "
          f"(motor {rev_s * 60 * GEAR_NOMINAL:.0f} rpm) = {rev_s * circ:.1f} mm/s; "
          f"1 count per window = {circ / COUNTS_PER_REV / window:.2f} mm/s")
    final = closed_loop(8.4, min_duty=0.15)
    print(f"one_rev P + min 0.15 at 8.4 V stops at {final} counts = {final / COUNTS_PER_REV:.4f} turn "
          f"= {final * circ / COUNTS_PER_REV:.2f} mm")
    print(f"balancer cascade: x1 only, {x1} x 30:1 = {x1 * 30} counts per wheel turn "
          f"(cascade_sim uses {CASCADE_COUNTS}); 65 mm wheel -> {math.pi * 65 / (x1 * 30):.2f} mm per count")
