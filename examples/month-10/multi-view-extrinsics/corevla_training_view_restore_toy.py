#!/usr/bin/env python3
"""Synthetic CoRe-VLA training-view restore stand-in.

Stdlib only. Shared 3-D markers, shared training and shifted extrinsics,
and shared render-noise draws (common random numbers). Not a real RGB-D
or point-cloud renderer and not VLA weights.

This is not AX=ZB chain-closure, not SpatialVLA Ego3D / adaptive grids,
not hand-eye AX=XB, and not AnyCamVLA.

Arms:
  A_shifted -- use the shifted external view as if it were the training view.
  B_restore -- lift the shifted view with the correct shifted-camera
    extrinsics and reproject to the training viewpoint (a geometric
    stand-in for reconstruct-and-render). R2C Restoration is named on
    the page; this toy does not re-implement ETCA.
  C_wrong -- "restore" with a leaked identity that pretends the shift
    did not happen (wrong extrinsics).

A named alternative on the same seeds, not adopted, is a larger
camera shift of 0.4000 m instead of the official 0.2000 m.

Regimes and parameters were written before the first run.

Labels: tie = identical on every seed; numerically zero = |paired mean| and sd
both < 1e-9; |m| <= sd = near-tie; |m| > sd = consistent gap (small if |m| < 20 %
of the smaller arm mean, else clear), with a sign count. ROUND_HALF_UP output.

Paper figures such as 13.3 %, 83.3 % and 1.6 m stay 以论文为准 and are not
toy outputs. Real RGB-D / point-cloud renderer / VLA weights: 本页未运行.
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
SMALL_FRAC = 0.2000  # 20 % of the smaller-arm mean; printed as 0.2000

# Declared camera and official shift (not the paper's 1.6 m real-robot shift).
FX = 400.0000
FY = 400.0000
CX = 160.0000
CY = 160.0000
TRAIN_EYE = (0.0000, -0.8000, 0.6000)
LOOK_TARGET = (0.0000, 0.0000, 0.0500)
WORLD_UP = (0.0000, 0.0000, 1.0000)
# Official large shift: a translated mount that keeps the training orientation.
SHIFT_OFFICIAL = 0.2000
# Named alternative, same seeds, not adopted: a larger translation of 0.4000 m.
SHIFT_ALT = 0.4000
SHIFT_NONE = 0.0000
RENDER_SIGMA = 0.5000  # shared pixel noise, pixels
# Fixed table markers and two task objects (metres). Written before the first run.
POINTS = {
    "cup": (-0.0600, 0.0500, 0.0400),
    "bowl": (0.2200, 0.0500, 0.0400),
    "m0": (-0.2000, -0.1000, 0.0000),
    "m1": (0.2000, -0.1000, 0.0000),
    "m2": (-0.2000, 0.2000, 0.0000),
    "m3": (0.2000, 0.2000, 0.0000),
}
POINT_NAMES = ("cup", "bowl", "m0", "m1", "m2", "m3")
OBJECT_NAMES = ("cup", "bowl")

ARMS = ("A_shifted", "B_restore", "C_wrong")
METRICS = ("rmse_px", "order_acc")
PAIRS = (("B", "A"), ("B", "C"), ("C", "A"))
ARM_FROM_LETTER = {"A": "A_shifted", "B": "B_restore", "C": "C_wrong"}

# name: (shift_m, declared expectation); written before the first run
REGIMES = {
    "no_shift": (
        SHIFT_NONE,
        "A and B may near-tie on agreement with the training-view observation - keep",
    ),
    "large_shift": (
        SHIFT_OFFICIAL,
        "B consistent better agreement with the training-view observation than A - keep",
    ),
}


def vec_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vec_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vec_dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vec_cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def vec_norm(a):
    s = math.sqrt(vec_dot(a, a))
    return (a[0] / s, a[1] / s, a[2] / s)


def mat_vec(R, v):
    return (
        R[0][0] * v[0] + R[0][1] * v[1] + R[0][2] * v[2],
        R[1][0] * v[0] + R[1][1] * v[1] + R[1][2] * v[2],
        R[2][0] * v[0] + R[2][1] * v[1] + R[2][2] * v[2],
    )


def look_at(eye, target, up=WORLD_UP):
    z_axis = vec_norm(vec_sub(target, eye))
    x_axis = vec_norm(vec_cross(z_axis, up))
    y_axis = vec_cross(z_axis, x_axis)
    return (x_axis, y_axis, z_axis)


def rotate_inv(R, v):
    # R has rows equal to the camera axes in the world; p_world = eye + R^T p_cam.
    return (
        R[0][0] * v[0] + R[1][0] * v[1] + R[2][0] * v[2],
        R[0][1] * v[0] + R[1][1] * v[1] + R[2][1] * v[2],
        R[0][2] * v[0] + R[1][2] * v[1] + R[2][2] * v[2],
    )


TRAIN_R = look_at(TRAIN_EYE, LOOK_TARGET)


def shifted_eye(shift_m):
    return (TRAIN_EYE[0] + shift_m, TRAIN_EYE[1], TRAIN_EYE[2])


def project(point, eye, R):
    p_cam = mat_vec(R, vec_sub(point, eye))
    u = FX * p_cam[0] / p_cam[2] + CX
    v = FY * p_cam[1] / p_cam[2] + CY
    return (u, v, p_cam[2])


def unproject(u, v, depth, eye, R):
    p_cam = ((u - CX) / FX * depth, (v - CY) / FY * depth, depth)
    return vec_add(eye, rotate_inv(R, p_cam))


def closer_object(uvz):
    best_name, best_d = None, None
    for name in OBJECT_NAMES:
        u, v, _ = uvz[name]
        dist = math.hypot(u - CX, v - CY)
        if best_d is None or dist < best_d:
            best_name, best_d = name, dist
    return best_name


def mean_sd(xs):
    if all(x == xs[0] for x in xs):
        return xs[0], 0.0
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
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
    elif abs(m) < SMALL_FRAC * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def shared_noise(seed, shift_m):
    rng = random.Random(f"render/{seed}/{shift_m:.4f}")
    return {name: (rng.gauss(0.0, RENDER_SIGMA), rng.gauss(0.0, RENDER_SIGMA)) for name in POINT_NAMES}


def train_uvz():
    return {name: project(POINTS[name], TRAIN_EYE, TRAIN_R) for name in POINT_NAMES}


def observe(shift_m, noise):
    eye = shifted_eye(shift_m)
    # Fixed training orientation: the mount is translated, not re-aimed.
    out = {}
    for name in POINT_NAMES:
        u, v, z = project(POINTS[name], eye, TRAIN_R)
        du, dv = noise[name]
        out[name] = (u + du, v + dv, z)
    return out


def restore(obs, lift_shift_m):
    eye = shifted_eye(lift_shift_m)
    restored = {}
    for name in POINT_NAMES:
        u, v, z = obs[name]
        world = unproject(u, v, z, eye, TRAIN_R)
        ru, rv, rz = project(world, TRAIN_EYE, TRAIN_R)
        restored[name] = (ru, rv, rz)
    return restored


def rmse_against_train(uvz, train):
    acc = 0.0
    for name in POINT_NAMES:
        acc += (uvz[name][0] - train[name][0]) ** 2 + (uvz[name][1] - train[name][1]) ** 2
    return math.sqrt(acc / len(POINT_NAMES))


def run_seed(shift_m, seed):
    train = train_uvz()
    true_order = closer_object(train)
    noise = shared_noise(seed, shift_m)
    obs = observe(shift_m, noise)
    a_uvz = obs
    b_uvz = restore(obs, shift_m)
    c_uvz = restore(obs, SHIFT_NONE)
    rows = {}
    for arm, uvz in (("A_shifted", a_uvz), ("B_restore", b_uvz), ("C_wrong", c_uvz)):
        rows[arm] = {
            "rmse_px": rmse_against_train(uvz, train),
            "order_acc": 1.0 if closer_object(uvz) == true_order else 0.0,
        }
    rows["true_order"] = true_order
    return rows


def run_regime(shift_m):
    per_arm = {arm: {metric: [] for metric in METRICS} for arm in ARMS}
    for seed in SEEDS:
        row = run_seed(shift_m, seed)
        for arm in ARMS:
            for metric in METRICS:
                per_arm[arm][metric].append(row[arm][metric])
    return per_arm


def print_regime(label, shift_m, declared):
    res = run_regime(shift_m)
    print(f"declared expectation {label}: {declared}")
    print(f"regime {label}  shift_m={num(shift_m)}  (mean+-sd over seeds)")
    for arm in ARMS:
        parts = [f"{arm}"]
        for metric in METRICS:
            m, s = mean_sd(res[arm][metric])
            parts.append(f"{metric} {fmt_pair(m, s)}")
        print("  " + " ".join(parts))
    for left, right in PAIRS:
        la, ra = ARM_FROM_LETTER[left], ARM_FROM_LETTER[right]
        for metric in METRICS:
            print(f"  paired {left}-{right} {metric}: {verdict(res[la][metric], res[ra][metric])}")
    return res


def hand_calc_lines():
    train = train_uvz()
    true_order = closer_object(train)
    cup = train["cup"]
    bowl = train["bowl"]
    d_cup = math.hypot(cup[0] - CX, cup[1] - CY)
    d_bowl = math.hypot(bowl[0] - CX, bowl[1] - CY)
    # One official large-shift projection, noiseless, for the worked example.
    large = observe(SHIFT_OFFICIAL, {name: (0.0, 0.0) for name in POINT_NAMES})
    large_order = closer_object(large)
    large_rmse = rmse_against_train(large, train)
    print(f"hand_calc 20 percent small-vs-clear factor = {num(SMALL_FRAC)}")
    print(f"hand_calc FX=FY={num(FX)} CX=CY={num(CX)}")
    print(f"hand_calc TRAIN_EYE=({num(TRAIN_EYE[0])}, {num(TRAIN_EYE[1])}, {num(TRAIN_EYE[2])}) m")
    print(f"hand_calc official SHIFT={num(SHIFT_OFFICIAL)} m along +x, fixed training orientation")
    print(f"hand_calc alternative SHIFT={num(SHIFT_ALT)} m (not adopted)")
    print(f"hand_calc RENDER_SIGMA={num(RENDER_SIGMA)} px")
    print(
        "hand_calc noiseless training cup uv="
        f"({num(cup[0])}, {num(cup[1])}), bowl uv=({num(bowl[0])}, {num(bowl[1])})"
    )
    print(
        "hand_calc training principal-point distances cup="
        f"{num(d_cup)} px, bowl={num(d_bowl)} px, closer={true_order}"
    )
    print(
        "hand_calc noiseless official-shift RMSE vs training view = "
        f"{num(large_rmse)} px, closer={large_order}"
    )


def main():
    print("Synthetic CoRe-VLA training-view restore stand-in; not a real RGB-D or VLA run")
    print(
        "declared "
        f"SHIFT_OFFICIAL={num(SHIFT_OFFICIAL)} SHIFT_ALT={num(SHIFT_ALT)} "
        f"SHIFT_NONE={num(SHIFT_NONE)} RENDER_SIGMA={num(RENDER_SIGMA)} "
        f"FX={num(FX)} FY={num(FY)} CX={num(CX)} CY={num(CY)} "
        f"SMALL_FRAC={num(SMALL_FRAC)} seeds={','.join(str(s) for s in SEEDS)}"
    )
    hand_calc_lines()
    print("declared arms: A_shifted uses the shifted view as training; B_restore lifts with the correct shift and reprojects; C_wrong uses a leaked identity")
    print("paper_authors=Tianhang Pan, Xuanhao Wang, Yiwen Pang, Bo Zhou, Jun Yang, Min-Ling Zhang, Shimin Di (abs / title-page order; 以论文为准)")
    print("paper_title_page=emails {tianhang.pan,shimin.di}@seu.edu.cn; no corresponding-author dagger and no equal-contribution star (以论文为准)")
    print("paper_version=arXiv 2609.37150 v1, submitted 2026-09-29")
    print("paper_figures=pi0.5 success 13.3 % to 83.3 % at a 1.6 m real-robot camera shift (arXiv 2609.37150 v1; 以论文为准, not toy outputs)")
    print("Regimes and parameters were written before the first run")
    print("Common random numbers: the scene markers, training extrinsics, shifted extrinsics and render-noise draws are shared across arms at each regime and seed")
    print("Assumptions: pinhole stand-in with known depth; fixed training orientation under a lateral mount translation; leaked-identity C pretends the shift is zero; RMSE is against the noiseless training-view projection; order_acc is 1 when the object nearer the principal point matches the training view")
    print("R2C Restoration is named; this toy does not re-implement ETCA")
    print("Paper figures 以论文为准")
    print("Real RGB-D / point-cloud renderer / VLA weights: 本页未运行")
    print("declared no_shift: A and B may near-tie on agreement with the training-view observation - keep")
    print("declared large_shift: B consistent better agreement with the training-view observation than A - keep")
    print("declared C_wrong on large_shift: C loses or mis-reports because it pretends the shift did not happen - lose kept")
    for name, (shift_m, declared) in REGIMES.items():
        print_regime(name, shift_m, declared)
    print(f"alternative same seeds SHIFT={num(SHIFT_ALT)} m (not adopted)")
    print(f"hand_calc official SHIFT={num(SHIFT_OFFICIAL)} m vs alternative {num(SHIFT_ALT)} m")
    print_regime("large_shift_alt", SHIFT_ALT, "alternative larger shift, same seeds, not adopted")
    print("No real RGB-D, point-cloud renderer, or VLA weight was started")
    print("No winner is universal: with no shift the raw and restored views may near-tie; a large external-camera translation is where correct-extrinsic restore matters, and a leaked identity leaves that shift uncorrected")


if __name__ == "__main__":
    main()
