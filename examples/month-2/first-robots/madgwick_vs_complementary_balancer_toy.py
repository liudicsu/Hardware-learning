#!/usr/bin/env python3
"""Madgwick (IMU, gradient descent) vs the lesson's complementary filter on a balancer pitch.

Synthetic IMU stream, stdlib only.  Not an MPU-6050, not the sensors-fusion
Kalman / bias-adaptive toys, not Mahony, not Allan variance and not the 109-
operation C implementation from the report.  A real IMU, an optical
reference and the report's Kalman comparison: 本页未运行.  Madgwick (2010)
internal report statements and figures 以报告为准.

What the report says (and what this toy keeps): the IMU filter integrates
the gyroscope as a quaternion derivative, q_dot_w = 0.5 q (x) (0, w), and
subtracts beta times the normalised gradient of an objective that compares
the measured accelerometer direction with gravity predicted from q:
  q_dot_est = q_dot_w - beta * grad_f / |grad_f|,  q_t = q_(t-1) + q_dot_est dt
beta is the divergence rate of the gyroscope measurement error (one tunable
gain for the IMU).  The derivation initially assumes the accelerometer
measures only gravity; the report's discussion says accelerations due to
motion corrupt the observed direction of gravity and that beta may be chosen
low enough to keep that divergence acceptable.  No magnetometer, no MARG
distortion or gyro-bias-drift blocks here.

The balancer moves in pitch only (rotation about the sensor y axis).  Truth:
the pitch theta(t) and the axle's horizontal acceleration a(t).  The gyro
reads (0, theta_dot + bias + noise, 0).  The accelerometer reads the specific
force a - g rotated into the sensor frame (so a steady lean theta =
atan(a/g) while accelerating at a makes the accelerometer point straight
"up" in the sensor frame), plus white noise, then normalised.

Common random numbers: for each (regime, seed) the initial pitch, the gyro
bias, every gyro noise sample and every accelerometer noise sample are drawn
once and shared by every arm.  Arms (all start at a level estimate, 200 Hz):
  A_gyro          : integrate the gyro only
  B_complementary : the lesson's filter, a = TAU/(TAU+dt), TAU = 0.5 s,
                    est = a (est + gyro dt) + (1 - a) accel_angle
  C_madgwick      : the report's IMU update at BETA_LOW (the report's IMU value)
  D_madgwick_big  : the same update at BETA_HIGH (top of the report's beta sweep)
Metrics: pitch RMSE in degrees over t >= WARMUP, and the mean |error| over
the last 5 s ("end error").  Time step dt = 1/200 s; the truth is a closed-
form function of time, so only the filters integrate (forward Euler on the
quaternion, normalised each step, as in the report's equation (42)).

Regimes and parameters were written before the first run:
  static     : constant pitch, a = 0, 60 s - A consistent loses on end
               error (bias drift); B vs C may near-tie
  slow_tilt  : 5 deg sine at 0.2 Hz, a = 0, 30 s - A loses; B vs C may
               near-tie
  accelerate : the axle accelerates at +-A_LIN for 3 s at a time and the
               robot leans to atan(a/g), 30 s - D (large beta) consistent
               loses to B on RMSE (pulled toward apparent gravity); keep.
               C vs B is not pre-declared, printed as it comes
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared parameters, written before the first run.
RATE = 200.0          # Hz, the lesson's balancer loop
DT = 1.0 / RATE
G = 9.81
TAU = 0.5             # s, the lesson's complementary time constant
BETA_LOW = 0.033      # rad/s, the report's IMU gain (以报告为准; not tuned here)
BETA_HIGH = 0.5       # rad/s, top of the report's beta sweep (0 to 0.5)
THETA0_DEG = 3.0      # initial pitch uniform in [-3, 3] deg (toy)
BIAS_DEG = 1.0        # gyro bias uniform in [-1, 1] deg/s (toy, not a datasheet)
GYRO_NOISE_DEG = 0.1  # deg/s white noise per sample (toy)
ACC_NOISE = 0.04      # g per axis white noise (toy; about the lesson's 2.5 deg accel-angle shake)
A_LIN = 2.0           # m/s^2, axle acceleration in "accelerate" (toy)
LEAN_TAU = 0.3        # s, the lean follows atan(a/g) with this lag (toy)
WARMUP = 2.0          # s excluded from RMSE
END_WINDOW = 5.0      # s

REGIMES = {"static": 60.0, "slow_tilt": 30.0, "accelerate": 30.0}
ARMS = ("A_gyro", "B_complementary", "C_madgwick", "D_madgwick_big")


def qmul(a, b):
    a0, a1, a2, a3 = a
    b0, b1, b2, b3 = b
    return (a0 * b0 - a1 * b1 - a2 * b2 - a3 * b3, a0 * b1 + a1 * b0 + a2 * b3 - a3 * b2,
            a0 * b2 - a1 * b3 + a2 * b0 + a3 * b1, a0 * b3 + a1 * b2 - a2 * b1 + a3 * b0)


def to_sensor(q, v):
    """Earth-frame vector into the sensor frame, q* (x) v (x) q (matches the report's gravity term)."""
    c = (q[0], -q[1], -q[2], -q[3])
    return qmul(qmul(c, (0.0, v[0], v[1], v[2])), q)[1:]


def a_lin(regime, t):
    if regime != "accelerate":
        return 0.0
    phase = t % 10.0  # 2 s still, 3 s at +A_LIN, 2 s still, 3 s at -A_LIN
    return A_LIN if 2.0 <= phase < 5.0 else (-A_LIN if 7.0 <= phase < 10.0 else 0.0)


def truth(regime, seed):
    """Common random numbers: initial pitch, bias and every noise sample, shared by all arms."""
    rng = random.Random(f"{regime}/{seed}")
    th0 = math.radians(rng.uniform(-THETA0_DEG, THETA0_DEG))
    bias = math.radians(rng.uniform(-BIAS_DEG, BIAS_DEG))
    n = int(round(REGIMES[regime] * RATE))
    th, rows = th0, []
    for k in range(n + 1):
        t = k * DT
        a = a_lin(regime, t)
        if regime == "slow_tilt":
            th_new = th0 + math.radians(5.0) * math.sin(2 * math.pi * 0.2 * t)
        elif regime == "accelerate":
            lean = math.atan2(a, G)
            th_new = th + (th0 + lean - th) * (1.0 - math.exp(-DT / LEAN_TAU)) if k else th0
        else:
            th_new = th0
        rate = (th_new - th) / DT if k else 0.0
        th = th_new
        q = (math.cos(th / 2), 0.0, math.sin(th / 2), 0.0)
        f = to_sensor(q, (a / G, 0.0, 1.0))
        acc = [f[i] + rng.gauss(0.0, ACC_NOISE) for i in range(3)]
        gyro = rate + bias + rng.gauss(0.0, math.radians(GYRO_NOISE_DEG))
        rows.append((t, th, gyro, acc))
    return rows, bias


def madgwick_step(q, gy, acc, beta):
    """Report IMU update: q_dot = 0.5 q (x) (0, w) - beta * grad/|grad|; Euler step; normalise."""
    q0, q1, q2, q3 = q
    qd = [0.5 * x for x in qmul(q, (0.0, 0.0, gy, 0.0))]
    norm = math.sqrt(sum(x * x for x in acc))
    if norm > 0.0:
        ax, ay, az = (x / norm for x in acc)
        f1 = 2 * (q1 * q3 - q0 * q2) - ax
        f2 = 2 * (q0 * q1 + q2 * q3) - ay
        f3 = 2 * (0.5 - q1 * q1 - q2 * q2) - az
        g0 = -2 * q2 * f1 + 2 * q1 * f2
        g1 = 2 * q3 * f1 + 2 * q0 * f2 - 4 * q1 * f3
        g2 = -2 * q0 * f1 + 2 * q3 * f2 - 4 * q2 * f3
        g3 = 2 * q1 * f1 + 2 * q2 * f2
        gn = math.sqrt(g0 * g0 + g1 * g1 + g2 * g2 + g3 * g3)
        if gn > 0.0:
            qd = [qd[0] - beta * g0 / gn, qd[1] - beta * g1 / gn, qd[2] - beta * g2 / gn, qd[3] - beta * g3 / gn]
    q = [q[i] + qd[i] * DT for i in range(4)]
    n = math.sqrt(sum(x * x for x in q))
    return tuple(x / n for x in q)


def run_arm(arm, regime, seed, tau=TAU, beta_low=BETA_LOW, beta_high=BETA_HIGH):
    rows, _ = truth(regime, seed)
    est, q = 0.0, (1.0, 0.0, 0.0, 0.0)
    alpha = tau / (tau + DT)
    errs = []
    for k, (t, th, gy, acc) in enumerate(rows):
        if k:
            if arm == "A_gyro":
                est += gy * DT
            elif arm == "B_complementary":
                est = alpha * (est + gy * DT) + (1 - alpha) * math.atan2(-acc[0], acc[2])
            else:
                q = madgwick_step(q, gy, acc, beta_low if arm == "C_madgwick" else beta_high)
                est = 2.0 * math.atan2(q[2], q[0])
        errs.append((t, math.degrees(est - th)))
    dur = REGIMES[regime]
    body = [e for t, e in errs if t >= WARMUP]
    end = [abs(e) for t, e in errs if t > dur - END_WINDOW]
    return {"rmse": math.sqrt(sum(e * e for e in body) / len(body)), "end_err": sum(end) / len(end)}


def mean_sd(xs):
    if all(x == xs[0] for x in xs):
        return xs[0], 0.0  # identical values: no floating residue in mean or sd
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    """Half-up rounding on the shortest decimal repr; tiny non-zero values in scientific form."""
    if x != 0.0 and abs(x) < 5e-4:
        return format(Decimal(repr(x)), ".3e")
    s = format(Decimal(repr(x)), ".4f")
    return "0.0000" if s == "-0.0000" else s


def sign_note(diffs, m):
    n, opp, zero = len(diffs), sum(1 for d in diffs if d * m < 0), sum(1 for d in diffs if d == 0)
    if opp == 0 and zero == 0:
        return f"same sign on all {n} seeds"
    if opp == 0:
        return f"no seed has the opposite sign, {zero} of {n} equal"
    note = f"{opp} of {n} seeds {'has' if opp == 1 else 'have'} the opposite sign"
    return note + (f", {zero} of {n} equal" if zero else "")


def fmt_pair(m, s):
    return f"{num(m)}+-{num(s)}"


def verdict(xa, xb):
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return f"{fmt_pair(m, s)}: numerically zero (floating-point residue), effectively a tie"
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < 0.2 * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


METRICS = ("rmse", "end_err")
PAIRS = (("A_gyro", "B_complementary"), ("C_madgwick", "B_complementary"), ("D_madgwick_big", "B_complementary"),
         ("D_madgwick_big", "C_madgwick"))


def collect(regime, **kw):
    return {arm: [run_arm(arm, regime, s, **kw) for s in SEEDS] for arm in ARMS}


def col(rows, key):
    return [x[key] for x in rows]


def report(regime):
    res = collect(regime)
    biases = [math.degrees(truth(regime, s)[1]) for s in SEEDS]
    print(f"{regime} ({num(REGIMES[regime])} s at {num(RATE)} Hz; axle acceleration "
          f"{'+-' + num(A_LIN) + ' m/s^2 for 3 s at a time' if regime == 'accelerate' else 'none'}):")
    print("  gyro bias per seed (deg/s): " + " ".join(num(b) for b in biases))
    for arm in ARMS:
        print(f"  {arm} " + " ".join(f"{key} {fmt_pair(*mean_sd(col(res[arm], key)))} deg" for key in METRICS))
    for a, b in PAIRS:
        for key in METRICS:
            print(f"  paired {a[0]}-{b[0]} {key}: {verdict(col(res[a], key), col(res[b], key))}")
    return res


def main():
    print("Synthetic balancer IMU toy; shared pitch, bias and noise draws; Madgwick IMU update vs the lesson's complementary filter; not an MPU-6050")
    print(f"seeds={len(SEEDS)} rate={num(RATE)} Hz TAU={num(TAU)} s BETA_LOW={num(BETA_LOW)} BETA_HIGH={num(BETA_HIGH)} rad/s "
          f"theta0 U[-{num(THETA0_DEG)}, {num(THETA0_DEG)}] deg bias U[-{num(BIAS_DEG)}, {num(BIAS_DEG)}] deg/s gyro_noise={num(GYRO_NOISE_DEG)} deg/s "
          f"acc_noise={num(ACC_NOISE)} g A_LIN={num(A_LIN)} m/s^2 LEAN_TAU={num(LEAN_TAU)} s WARMUP={num(WARMUP)} s (declared toy parameters, not a datasheet)")
    print(f"Integration step: dt=1/{num(RATE)} s forward Euler on the filters only (the report's equation (42) form); the truth is closed form")
    print("Regimes and parameters were written before the first run")
    # Labelled hand calculations.
    lean = math.degrees(math.atan2(A_LIN, G))
    print(f"hand_calc lean while accelerating: atan(A_LIN/g)=atan({num(A_LIN)}/{num(G)})={num(lean)} deg; "
          f"the accelerometer then reads straight up, accel angle {num(math.degrees(math.atan2(-0.0, 1.0)))} deg")
    print(f"hand_calc complementary: a=TAU/(TAU+dt)=0.5/(0.5+0.005)={num(TAU / (TAU + DT))}; steady error from a bias b is b*TAU, "
          f"for b=1.0 deg/s {num(1.0 * TAU)} deg")
    print(f"hand_calc gyro only: a bias of 1.0 deg/s drifts 1.0*60={num(60.0)} deg in 60 s")
    print(f"hand_calc report beta=sqrt(3/4)*w_beta: BETA_LOW={num(BETA_LOW)} rad/s <-> w_beta={num(math.degrees(BETA_LOW / math.sqrt(0.75)))} deg/s")
    for regime in REGIMES:
        report(regime)
    print("alternatives (post-hoc check of the declared TAU and beta; same seeds):")
    for kw in ({"tau": 0.25}, {"tau": 1.0}):
        alt = collect("accelerate", **kw)
        print(f"  accelerate TAU={num(kw['tau'])} s: paired D-B rmse@alt: {verdict(col(alt['D_madgwick_big'], 'rmse'), col(alt['B_complementary'], 'rmse'))}")
    for beta in (0.1, 0.2):
        alt = collect("accelerate", beta_high=beta)
        print(f"  accelerate BETA_HIGH={num(beta)}: paired D-B rmse@alt: {verdict(col(alt['D_madgwick_big'], 'rmse'), col(alt['B_complementary'], 'rmse'))}")
    alt = collect("static", beta_low=0.1)
    print(f"  static BETA_LOW=0.1000: paired C-B rmse@alt: {verdict(col(alt['C_madgwick'], 'rmse'), col(alt['B_complementary'], 'rmse'))}")
    print("No universal winner: both fusion filters remove the gyro's drift; a large beta follows apparent gravity while the axle accelerates")
    print("Real IMU / optical reference / the report's Kalman comparison: 本页未运行; Madgwick (2010) report figures 以报告为准")


if __name__ == "__main__":
    main()
