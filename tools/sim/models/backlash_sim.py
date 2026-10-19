"""backlash_sim.py: what gear backlash does to a position loop, and why gravity hides it.

Toy model of one joint: motor -> gearbox -> arm. The gearbox has a dead zone (backlash)
of BACKLASH degrees at the output: inside it the motor turns without moving the arm.
A PID loop at 200 Hz moves the arm to a target. We read either the motor's encoder
(angle seen before the gears) or an encoder on the arm itself (after the gears).
"""
import math

DT = 0.005               # 200 Hz control loop
JM, BM = 0.002, 0.03     # motor side (referred to the output): inertia, friction
JA, BA = 0.004, 0.02     # arm side: inertia, friction
STIFF, DAMP = 40.0, 0.2  # gear teeth once in contact: N*m/rad, N*m*s/rad
GRAV = 0.4               # N*m of gravity with the arm horizontal (0 deg)
MAX_TORQUE = 1.0
STICTION = 0.03         # N*m of dry friction in the motor and first gear stage


def run(backlash_deg, sensor, target, preload=0.0, kp=0.1, ki=0.2, kd=0.004, seconds=4.0):
    """preload: N*m from a spring that always pulls the arm the same way."""
    half = math.radians(backlash_deg) / 2
    qm = wm = qa = wa = 0.0
    integral, prev, t = 0.0, None, 0.0
    tail = []
    while t < seconds:
        meas = math.degrees(qm if sensor == "motor" else qa)
        prev = meas if prev is None else prev
        error = target - meas
        unclipped = kp * error + ki * integral - kd * (meas - prev) / DT
        prev = meas
        torque = max(-MAX_TORQUE, min(MAX_TORQUE, unclipped))
        if torque == unclipped:
            integral += error * DT
        for _ in range(10):                                  # physics at 0.5 ms
            gap = qm - qa
            if abs(gap) > half:                              # teeth touching
                push = STIFF * (gap - math.copysign(half, gap)) + DAMP * (wm - wa)
            else:
                push = 0.0
            wm += (torque - BM * wm - STICTION * math.tanh(wm / 0.02) - push) / JM * 0.0005
            wa += (push - BA * wa - GRAV * math.cos(qa) - preload) / JA * 0.0005
            qm += wm * 0.0005
            qa += wa * 0.0005
        t += DT
        if t > seconds - 1.0:
            tail.append(math.degrees(qa))
    swing = max(tail) - min(tail)
    return f"arm at {math.degrees(qa):6.2f} deg (target {target}), swinging {swing:4.2f} deg peak to peak in the last second"


if __name__ == "__main__":
    for target in (20, 90):
        where = "gravity loads the teeth" if target == 20 else "arm straight up, no gravity load"
        print(f"target {target} deg ({where}):")
        print("  no backlash, arm encoder:       ", run(0.0, "arm", target))
        print("  2 deg backlash, motor encoder:  ", run(2.0, "motor", target))
        print("  2 deg backlash, arm encoder:    ", run(2.0, "arm", target))
    print("  ...same, plus a spring preload: ", run(2.0, "arm", 90, preload=0.1))
