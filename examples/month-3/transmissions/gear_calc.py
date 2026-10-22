"""gear_calc.py: the arithmetic behind a gearbox, before you print one.

1. Planetary stage (ring fixed, sun in, carrier out): ratio = 1 + ring / sun.
   It only assembles if planet = (ring - sun) / 2 is a whole number of teeth and
   (sun + ring) / planets is a whole number (equally spaced planets), and neighbouring
   planets do not touch: (sun + planet) x sin(180 deg / planets) > planet + 2.
2. Cycloidal stage with N ring pins and N - 1 lobes: ratio N - 1, output turns backwards.
3. What a ratio n does: torque x n (minus losses), speed / n, and what you feel when you
   turn the output by hand: friction x n and rotor inertia x n^2.
4. Backlash at the joint becomes a position error at the tip: arc = reach x angle.
"""
import math


def planetary(sun, ring, planets):
    gap = ring - sun
    if gap % 2:
        return f"sun {sun:2d}, ring {ring:2d}: no whole planet size ({gap / 2} teeth) -> will not mesh"
    planet = gap // 2
    if (sun + ring) % planets:
        return (f"sun {sun:2d}, ring {ring:2d}, planet {planet:2d}: {planets} planets cannot be spaced "
                f"evenly ((sun + ring) / {planets} = {(sun + ring) / planets:.2f})")
    spacing = (sun + planet) * math.sin(math.pi / planets)   # planet centre to centre, in modules
    if spacing <= planet + 2:                                # planet tip diameter, in modules
        return (f"sun {sun:2d}, ring {ring:2d}, planet {planet:2d}: {planets} planets collide "
                f"(centre spacing {spacing:.2f} <= tip diameter {planet + 2})")
    return f"sun {sun:2d}, ring {ring:2d}, planet {planet:2d}, {planets} planets: ratio {1 + ring / sun:.3f} : 1"


def cycloidal(pins):
    lobes = pins - 1
    return f"{pins} ring pins, {lobes} lobes: ratio {lobes / (pins - lobes):.0f} : 1, output turns the opposite way"


def stack(ratios, efficiency_per_stage=0.9):
    total = math.prod(ratios)
    eff = efficiency_per_stage ** len(ratios)
    return total, eff


if __name__ == "__main__":
    print("-- planetary stages")
    print(planetary(12, 48, 3))
    print(planetary(12, 46, 3))
    print(planetary(13, 47, 3))
    print(planetary(14, 46, 4))
    print(planetary(12, 45, 3))

    print("-- cycloidal stages")
    print(cycloidal(10))
    print(cycloidal(16))

    print("-- two 5:1 planetary stages, 90 % per stage (a guess for printed gears; measure yours)")
    total, eff = stack([5, 5])
    motor_torque, motor_rpm = 0.05, 6000           # N*m and rpm of a small brushless motor
    print(f"ratio {total}:1, efficiency {eff * 100:.0f} %: output {motor_torque * total * eff:.2f} N*m "
          f"at {motor_rpm / total:.0f} rpm (motor: {motor_torque} N*m at {motor_rpm} rpm)")

    print("-- turning the output by hand (backdriving), relative to a 147:1 gearbox")
    for n in (147, 191, 345):                      # the STS3215 ratios in the SO-101 leader arm
        print(f"{n:3d}:1  friction felt x{n / 147:4.2f}   rotor inertia felt x{(n / 147) ** 2:4.2f}")

    print("-- backlash at the joint -> error at the tip of a 0.30 m arm")
    for deg in (0.5, 1.0, 2.0):
        print(f"{deg:3.1f} deg -> {0.30 * math.radians(deg) * 1000:4.1f} mm")
