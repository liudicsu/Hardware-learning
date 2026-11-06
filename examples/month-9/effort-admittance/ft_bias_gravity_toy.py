#!/usr/bin/env python3
"""Synthetic static F/T calibration; stdlib only, no sensor purchase.
R_BS maps sensor axes to base axes; gS=R_BS^T*(0,0,-9.81).
Positive wrench here is payload-on-sensor: fS=m*gS+bF+contactS;
tauS=(m*c) cross gS+bT+contactTorqueS, all at the sensor origin.
This sign is declared, not copied from ft_tools_ros2's opposite reaction sign.
Fit only measured free-space calibration rows. Mass, COM and both offsets are
ESTIMATED, never supplied to compensation. All arms share recorded eval data.
Real F/T hardware: 本页未运行. No safety or universal performance claim.
"""
from math import cos, sin, pi, sqrt
from random import Random
from statistics import mean, pstdev

SEEDS = (11, 23, 37, 53, 71)
G_BASE = (0., 0., -9.81)
SIGMA_F, SIGMA_T = .08, .003  # N, N m per independent sensor component
THRESHOLD = 1.2  # N; declared before evaluation, not tuned on held-out data
ARMS = ("raw", "one_pose_tare", "bias_only_ls", "ls_gravity")
ZERO = (0., 0., 0.)
TRUTH = (.72, (.035, -.018, .065), (.32, -.25, .42), (.018, -.012, .009))
CAL_POSES = ((0., 0., 0.), (pi, 0., 0.), (0., pi/2, 0.),
             (0., -pi/2, 0.), (pi/2, 0., 0.), (-pi/2, 0., 0.))
EVAL_POSES = tuple((-.9 + .17*k, .35*sin(.7*k) + .21, .13 + .29*k) for k in range(12))


def add(a, b):
    return tuple(x+y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def scale(k, a):
    return tuple(k*x for x in a)


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def norm(a):
    return sqrt(dot(a, a))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def rotation(pose):
    """R_BS = Rz(yaw) Ry(pitch) Rx(roll), right-handed."""
    r, p, y = pose
    cr, sr, cp, sp, cy, sy = cos(r), sin(r), cos(p), sin(p), cos(y), sin(y)
    return ((cy*cp, cy*sp*sr-sy*cr, cy*sp*cr+sy*sr),
            (sy*cp, sy*sp*sr+cy*cr, sy*sp*cr-cy*sr), (-sp, cp*sr, cp*cr))


def to_sensor(r, base):
    return tuple(dot(column, base) for column in zip(*r))


def to_base(r, sensor):
    return tuple(dot(row, sensor) for row in r)


def least_squares(rows, targets):
    """Reorthogonalized modified Gram-Schmidt QR; reject rank-deficient poses.
    Educational small matrices, not a substitute for production pivoted QR/SVD.
    """
    columns = [tuple(c) for c in zip(*rows)]
    n = len(columns)
    q, upper = [], [[0.]*n for _ in range(n)]
    for j, column in enumerate(columns):
        v = column
        for _ in range(2):
            for k, basis in enumerate(q):
                coefficient = dot(basis, v)
                upper[k][j] += coefficient
                v = sub(v, scale(coefficient, basis))
        upper[j][j] = norm(v)
        if upper[j][j] < 1e-10:
            raise ValueError("insufficient orientation excitation / rank deficient")
        q.append(scale(1/upper[j][j], v))
    rhs, solution = [dot(basis, targets) for basis in q], [0.]*n
    for j in range(n-1, -1, -1):
        solution[j] = (rhs[j]-sum(upper[j][k]*solution[k] for k in range(j+1, n)))/upper[j][j]
    return tuple(solution)


def fit(calibration):
    """Receives only (gS, measured_fS, measured_tauS); no true mass/COM/bias."""
    frows, trows, fy, ty = [], [], [], []
    for g, f, tau in calibration:
        h_design = ((0., g[2], -g[1]), (-g[2], 0., g[0]), (g[1], -g[0], 0.))
        for axis in range(3):
            unit = tuple(float(axis == j) for j in range(3))
            frows.append((g[axis],) + unit)
            trows.append(h_design[axis] + unit)
            fy.append(f[axis]); ty.append(tau[axis])
    mass_bias = least_squares(frows, fy)
    h_bias = least_squares(trows, ty)
    mass = mass_bias[0]
    if mass <= 0:
        raise ValueError("unphysical fitted mass")
    return mass, scale(1/mass, h_bias[:3]), mass_bias[1:], h_bias[3:]


def measurement(pose, contact_f, contact_t, rng, sigma_f=SIGMA_F, sigma_t=SIGMA_T):
    """Truth is used ONLY by synthetic data generator and error scorer."""
    mass, com, bf, bt = TRUTH
    r = rotation(pose)
    g = to_sensor(r, G_BASE)
    f_true, t_true = to_sensor(r, contact_f), to_sensor(r, contact_t)
    f = add(add(f_true, scale(mass, g)), bf)
    tau = add(add(t_true, cross(scale(mass, com), g)), bt)
    return g, add(f, tuple(rng.gauss(0, sigma_f) for _ in range(3))), add(tau, tuple(rng.gauss(0, sigma_t) for _ in range(3)))


def datasets(seed, sigma_f=SIGMA_F, sigma_t=SIGMA_T):
    cal_rng, eval_rng = Random(seed), Random(10000+seed)
    calibration = [measurement(pose, ZERO, ZERO, cal_rng, sigma_f, sigma_t)
                   for pose in CAL_POSES for _ in range(16)]
    evaluation = []
    for pose in EVAL_POSES:
        r = rotation(pose)
        for k in range(10):
            contact = k >= 5
            f, t = ((1.2, .4, .2), (.045, -.025, .020)) if contact else (ZERO, ZERO)
            g, fm, tm = measurement(pose, f, t, eval_rng, sigma_f, sigma_t)
            evaluation.append((g, fm, tm, to_sensor(r, f), to_sensor(r, t), contact))
    return calibration, evaluation


def tare(calibration):
    """Constant one-pose zero uses first 16 rows only; it includes gravity."""
    return tuple(tuple(mean(row[index][axis] for row in calibration[:16]) for axis in range(3)) for index in (1, 2))


def compensate(arm, sample, estimated, zero):
    g, fm, tm = sample[:3]
    mass, com, bf, bt = estimated
    if arm == "raw":
        return fm, tm
    if arm == "one_pose_tare":
        return sub(fm, zero[0]), sub(tm, zero[1])
    if arm == "bias_only_ls":
        return sub(fm, bf), sub(tm, bt)
    if arm != "ls_gravity":
        raise ValueError("unknown arm")
    return sub(sub(fm, bf), scale(mass, g)), sub(sub(tm, bt), cross(scale(mass, com), g))


def score(arm, evaluation, estimated, zero):
    f2 = t2 = 0.
    tp = fp = fn = 0
    for sample in evaluation:
        f, t = compensate(arm, sample, estimated, zero)
        f2 += norm(sub(f, sample[3]))**2
        t2 += norm(sub(t, sample[4]))**2
        detected, contact = norm(f) > THRESHOLD, sample[5]
        tp += int(detected and contact)
        fp += int(detected and not contact)
        fn += int(not detected and contact)
    f1 = 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.
    return sqrt(f2/len(evaluation)), sqrt(t2/len(evaluation)), f1, fp


def main():
    print("Synthetic static sensor-origin wrench; R_BS sensor->base, gS=R_BS^T gB, gB=(0,0,-9.81)")
    print("6 orientations x16=96 contact-free calibration rows; 12 held-out poses x10=120 eval rows")
    print("Same recorded data for all arms; one_pose_tare deliberately uses only first-pose 16/96 rows")
    print("sigma_F_N=0.080 sigma_tau_Nm=0.003 threshold_N=1.200; 60 free/60 contact per seed")
    print("seed mass_hat_kg COM_error_mm force_bias_error_N torque_bias_error_Nm")
    results = {arm: [] for arm in ARMS}
    traces = []
    for seed in SEEDS:
        calibration, evaluation = datasets(seed)
        estimated, zero = fit(calibration), tare(calibration)
        m, c, bf, bt = estimated
        print(f"{seed} {m:.6f} {1000*norm(sub(c, TRUTH[1])):.6f} {norm(sub(bf, TRUTH[2])):.6f} {norm(sub(bt, TRUTH[3])):.6f}")
        for arm in ARMS:
            metrics = score(arm, evaluation, estimated, zero)
            results[arm].append(metrics)
            traces.append((seed, arm, metrics))
    print("seed arm force_RMSE_N torque_RMSE_Nm contact_F1 false_triggers_out_of_60_free")
    for seed, arm, (f, t, f1, fp) in traces:
        print(f"{seed} {arm} {f:.6f} {t:.6f} {f1:.6f} {fp}")
    print("five-seed spread: arm metric mean population_std min max")
    for arm in ARMS:
        for j, metric in enumerate(("force_N", "torque_Nm", "F1", "false_triggers")):
            values = [row[j] for row in results[arm]]
            print(f"{arm} {metric} {mean(values):.6f} {pstdev(values):.6f} {min(values):.6f} {max(values):.6f}")
    print("Estimated mass/COM/offsets only; single-pose zero is not bias identification across orientations")
    print("Static model excludes inertia, temperature drift, sensor misalignment, crosstalk and controller safety")
    print("Present Load remains a proxy, not N; real F/T hardware: 本页未运行")


if __name__ == "__main__":
    main()
