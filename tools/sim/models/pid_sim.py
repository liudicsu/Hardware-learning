"""pid_sim.py: P, PI, PID and integral windup on one arm joint lifting against gravity.

Toy model of a single joint (think of an SO-101 shoulder with a short arm): the motor
torque is limited, gravity pulls the arm down by 0.4 N*m * cos(angle), and there is a
little friction. The controller runs at 200 Hz and is asked to move the joint from
0 degrees (horizontal) to 60 degrees at t = 0.
"""
import math

J = 0.004          # kg*m^2, arm inertia seen at the joint
B = 0.05           # N*m per rad/s, viscous friction
GRAV = 0.4         # N*m, gravity torque with the arm horizontal
MAX_TORQUE = 1.0   # N*m the motor can give
DT = 0.005         # 200 Hz control loop


def run(kp, ki=0.0, kd=0.0, anti_windup=True, target=60.0, seconds=3.0):
    q, w, integral, t = 0.0, 0.0, 0.0, 0.0       # angle (rad), speed (rad/s)
    peak, settle = 0.0, None
    prev = q
    while t < seconds:
        error = target - math.degrees(q)
        rate = (math.degrees(q) - math.degrees(prev)) / DT   # derivative of the measurement
        prev = q
        unclipped = kp * error + ki * integral - kd * rate
        torque = max(-MAX_TORQUE, min(MAX_TORQUE, unclipped))
        if not anti_windup or torque == unclipped:            # only integrate while not saturated
            integral += error * DT
        for _ in range(5):                                    # physics at 1 ms
            alpha = (torque - B * w - GRAV * math.cos(q)) / J
            w += alpha * 0.001
            q += w * 0.001
        t += DT
        deg = math.degrees(q)
        peak = max(peak, deg)
        if abs(deg - target) > 1.0:
            settle = None
        elif settle is None:
            settle = t
    over = max(0.0, peak - target)
    s = f"{settle:.2f} s" if settle is not None else "never"
    return f"final {math.degrees(q):5.1f} deg, overshoot {over:4.1f} deg, within 1 deg from {s}"


if __name__ == "__main__":
    print("P    kp 0.05                  ", run(0.05))
    print("P    kp 0.2                   ", run(0.2))
    print("PD   kp 0.05, kd 0.002        ", run(0.05, kd=0.002))
    print("PI   kp 0.05, ki 0.1          ", run(0.05, ki=0.1))
    print("PID  kp 0.05, ki 0.1, kd 0.002", run(0.05, ki=0.1, kd=0.002))
    print("  ...same, no anti-windup     ", run(0.05, ki=0.1, kd=0.002, anti_windup=False))
    print("PID  kp 0.05, ki 0.4, kd 0.002", run(0.05, ki=0.4, kd=0.002))
    print("  ...same, no anti-windup     ", run(0.05, ki=0.4, kd=0.002, anti_windup=False))
