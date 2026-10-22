"""Recompute every number used in the Months 1-3 math quick-reference examples (src/lib/mathRef.ts)."""
import math

# hex
assert 0x68 == 0b01101000 == 64 + 32 + 8 == 104 and 0x69 == 0b01101001
# two's complement
assert (-262) & 0xFFFF == 0xFEFA == 65274 == 65536 - 262 and format(0xFEFA, "016b") == "1111111011111010"
print("gyro -262/131 =", round(-262 / 131, 2))
# bitwise: index = lastAB*4 + ab, 16 combinations
assert all((l << 2) | a == l * 4 + a for l in range(4) for a in range(4)) and len({(l << 2) | a for l in range(4) for a in range(4)}) == 16
# trig: P-only equilibrium 0.2*(60-q) = 0.4*cos q
f = lambda q: 0.2 * (60 - q) - 0.4 * math.cos(math.radians(q))
a, b = 50.0, 60.0
for _ in range(80):
    m = (a + b) / 2
    a, b = (m, b) if f(a) * f(m) > 0 else (a, m)
print(f"equilibrium {a:.2f} deg, motor {0.2*(60-a):.3f}, gravity {0.4*math.cos(math.radians(a)):.3f}, cos {math.cos(math.radians(a)):.4f}")
# radians
cnt = 12 * 120
d = math.radians(360 / cnt)
print(cnt, 360 / cnt, f"{d:.6f} rad", f"{35*d:.4f} mm", f"{math.pi*70:.2f} mm", f"{math.pi*70/cnt:.4f} mm")
# rate / accumulation
print("dt", 1 / 200, "I:", 60 * 0.1, 0.1 * 6, 0.4 * 6, "m/count", round(math.pi * 0.065 / 90, 5), "v", round(0.00227 / 0.04, 3), "window", 1 / 25)
# stddev / RMS
print("rms gyro", round(math.hypot(1.5, 0.3), 3), "mean of 100", 0.3 / math.sqrt(100), "rms err", round(math.hypot(0.72, 0.07), 2))
