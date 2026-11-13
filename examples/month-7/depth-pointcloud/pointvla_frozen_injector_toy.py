#!/usr/bin/env python3
"""PointVLA frozen-injector toy: a frozen 2D VLA head with a lightweight
additive point-cloud injection at one declared block.

Synthetic stand-in and a scalar grasp-height model; not DexVLA; not a
GPU / RealSense / UR5e run (本页未运行); not OctoMap / TSDF / 3DGS /
SpatialVLA.  PointVLA (arXiv 2503.07511) keeps a pre-trained 2D VLA,
FREEZES its action expert, and injects point-cloud features additively
through a lightweight block into a few later, less critical blocks found
by a skip-block analysis (the paper: skipping any of the early blocks
breaks the task and the gripper fails to close tightly).  The paper
reports that 2D VLAs fail a table-height shift and a grasp at photos on
a screen; those are paper statements (以论文为准), NOT toy outputs.
Paper scores are not reproduced here.

Model (declared): N_BLOCKS = 8 blocks with importance
W_BLOCK = (0.30, 0.22, 0.16, 0.08, 0.06, 0.06, 0.06, 0.06) (sums to 1; a
declared stand-in for the skip-block profile).  Injection at block k
displaces a fraction ETA = 0.5 of that block's contribution, so grip
quality is q = 1 - ETA * W_BLOCK[k] (no injection: q = 1.0); the gripper
closes when q + SIG_GRIP * g > GRIP_THR with SIG_GRIP = 0.04,
GRIP_THR = 0.90.  LATE_BLOCK = 6, EARLY_BLOCK = 0.  Heights in metres:
H_TRAIN = 0.003 (training foam), H_SHIFT = 0.052, foam jitter sd 0.001,
object height OBJ_H ~ uniform(0.04, 0.06), object top
z_true = table + OBJ_H.  2D estimate
z2d = H_TRAIN + RGB_CUE * (table - H_TRAIN) + OBJ_H + SIG_RGB * g with
RGB_CUE = 0.1, SIG_RGB = 0.003.  Point cloud: N_PTS = 32 points on the
object top (z_true + SIG_PC * g, SIG_PC = 0.004) plus N_PTS table
points (table + SIG_PC * g); z3d = mean of the object-top points,
table_est = mean of the table points; injector gain G = 1.0 gives
z_cmd = z2d + G * (z3d - z2d).  Presence check (arms with a cloud):
grasp only if z3d - table_est > PRES_THR = 0.02.  Photo scene: the RGB
sees the object (z2d computed as if present) but the object-top points
lie on a flat screen at table + 0.005.  TOL = 0.010, N_SCENES = 40 per
seed.

Arms: A_2d (frozen 2D head only, no cloud, always grasps, z_cmd = z2d,
q = 1.0); B_late (frozen 2D head + injection at LATE_BLOCK, uses the
cloud and the presence check); C_early (same injection and presence
check but at EARLY_BLOCK).

Per scene success: real object -> attempted grasp with
|z_cmd - z_true| < TOL AND the gripper closes; photo scene -> success
only if the arm does NOT grasp.  Metrics per seed: success (fraction of
scenes), height_err_mm (mean |z_cmd - z_true| in mm over real scenes
where a grasp was attempted; 0.0 if none), false_grasp (fraction of
photo scenes grasped; 0.0 when the regime has no photo scenes).

Common random numbers: for each (regime, seed), random.Random draws,
per scene in this fixed order: photo flag u (uniform), foam jitter,
OBJ_H, RGB noise g, grip noise g, N_PTS object-point noises, N_PTS
table-point noises, N_PTS outlier uniforms and N_PTS outlier heights
(drawn in every regime even if unused); all arms use the same draws.

Regimes: "train_height" (table = H_TRAIN + jitter, no photos);
"height_shift" (table = H_SHIFT + jitter, no photos); "real_vs_photo"
(table = H_TRAIN + jitter, a photo when u < 0.5); "corrupted_cloud"
(table = H_TRAIN + jitter, no photos; each object-top point is
replaced, when its outlier uniform < P_OUT = 0.3, by
table + 0.15 * outlier height).

Pairs, every metric in every regime: B-A, C-B, C-A.

Regimes and parameters were written before the first run.  Declared
expectations (not tuned; print whatever comes):
  train_height    : A vs B may near-tie - keep; C consistently below B
                    on success - keep
  height_shift    : B consistently above A on success; C below B - keep
  real_vs_photo   : B consistently above A on success (A grasps at
                    photos); C below B - keep
  corrupted_cloud : B may lose to A - keep as it comes

The arm ordering follows from the declared block-importance profile and
noise levels; the toy shows magnitudes and seed scatter, not evidence
that one arm always wins.

Alternatives (same seeds, declared before the run, not adopted):
  height_shift with injection at block 3 (paired X-B success, X the
  block-3 arm);
  corrupted_cloud with a median instead of a mean for z3d in B (paired
  B_median-A success);
  train_height with TOL = 0.02 (paired B-A success);
  height_shift with RGB_CUE = 0.3 (paired B-A success).
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared parameters, written before the first run.
N_BLOCKS = 8
W_BLOCK = (0.30, 0.22, 0.16, 0.08, 0.06, 0.06, 0.06, 0.06)  # sums to 1
ETA = 0.5
SIG_GRIP = 0.04
GRIP_THR = 0.90
LATE_BLOCK = 6
EARLY_BLOCK = 0
H_TRAIN = 0.003                # m, training foam
H_SHIFT = 0.052                # m
FOAM_SD = 0.001                # m, jitter sd on the table height
OBJ_LO, OBJ_HI = 0.04, 0.06    # m, OBJ_H ~ uniform(OBJ_LO, OBJ_HI)
RGB_CUE = 0.1
SIG_RGB = 0.003
N_PTS = 32
SIG_PC = 0.004                 # m, per-point cloud noise
G = 1.0                        # injector gain
PRES_THR = 0.02                # m, presence check
SCREEN_H = 0.005               # m, photo scene: flat screen above the table
TOL = 0.010                    # m
N_SCENES = 40
P_OUT = 0.3                    # corrupted_cloud outlier fraction
OUT_SCALE = 0.15               # outlier height = table + OUT_SCALE * uniform(0, 1)

ARMS = ("A_2d", "B_late", "C_early")
METRICS = ("success", "height_err_mm", "false_grasp")
PAIRS = (("B_late", "A_2d"), ("C_early", "B_late"), ("C_early", "A_2d"))
DECLARED = {
    "train_height": "A vs B may near-tie - keep; C consistently below B on "
                    "success - keep",
    "height_shift": "B consistently above A on success; C below B - keep",
    "real_vs_photo": "B consistently above A on success (A grasps at photos); "
                     "C below B - keep",
    "corrupted_cloud": "B may lose to A - keep as it comes",
}


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


def median_of(xs):
    s = sorted(xs)
    n = len(s)
    return 0.5 * (s[n // 2 - 1] + s[n // 2]) if n % 2 == 0 else s[n // 2]


def q_of(block):
    return 1.0 if block is None else 1.0 - ETA * W_BLOCK[block]


def run_seed(regime, seed, late_block=LATE_BLOCK, median=False, tol=TOL,
             rgb_cue=RGB_CUE):
    """One seed of one regime: shared draws, all arms scored on the same scenes."""
    rng = random.Random(f"{regime}/{seed}")
    blocks = {"A_2d": None, "B_late": late_block, "C_early": EARLY_BLOCK}
    acc = {arm: {"succ": 0, "err_sum": 0.0, "err_n": 0, "photo": 0, "fg": 0}
           for arm in ARMS}
    base = {"train_height": H_TRAIN, "height_shift": H_SHIFT,
            "real_vs_photo": H_TRAIN, "corrupted_cloud": H_TRAIN}[regime]
    for _ in range(N_SCENES):
        u = rng.random()
        jitter = rng.gauss(0.0, FOAM_SD)
        obj_h = rng.uniform(OBJ_LO, OBJ_HI)
        g_rgb = rng.gauss(0.0, 1.0)
        g_grip = rng.gauss(0.0, 1.0)
        obj_n = [rng.gauss(0.0, 1.0) for _ in range(N_PTS)]
        tab_n = [rng.gauss(0.0, 1.0) for _ in range(N_PTS)]
        out_u = [rng.random() for _ in range(N_PTS)]
        out_h = [rng.uniform(0.0, 1.0) for _ in range(N_PTS)]
        is_photo = regime == "real_vs_photo" and u < 0.5
        table = base + jitter
        z_true = table + obj_h
        z2d = H_TRAIN + rgb_cue * (table - H_TRAIN) + obj_h + SIG_RGB * g_rgb
        if is_photo:
            obj_pts = [table + SCREEN_H + SIG_PC * n for n in obj_n]
        else:
            obj_pts = [z_true + SIG_PC * n for n in obj_n]
        if regime == "corrupted_cloud":
            obj_pts = [table + OUT_SCALE * h if ou < P_OUT else p
                       for p, ou, h in zip(obj_pts, out_u, out_h)]
        tab_pts = [table + SIG_PC * n for n in tab_n]
        table_est = sum(tab_pts) / N_PTS
        z3d = sum(obj_pts) / N_PTS
        z3d_med = median_of(obj_pts)
        for arm in ARMS:
            q = q_of(blocks[arm])
            if arm == "A_2d":
                z_cmd = z2d
                grasp = True
            else:
                z = z3d_med if (median and arm == "B_late") else z3d
                z_cmd = z2d + G * (z - z2d)
                grasp = (z - table_est) > PRES_THR
            closes = q + SIG_GRIP * g_grip > GRIP_THR
            if is_photo:
                acc[arm]["photo"] += 1
                if grasp:
                    acc[arm]["fg"] += 1
                ok = not grasp
            else:
                if grasp:
                    acc[arm]["err_sum"] += abs(z_cmd - z_true) * 1000.0
                    acc[arm]["err_n"] += 1
                ok = grasp and abs(z_cmd - z_true) < tol and closes
            if ok:
                acc[arm]["succ"] += 1
    out = {}
    for arm in ARMS:
        a = acc[arm]
        out[arm] = {"success": a["succ"] / N_SCENES,
                    "height_err_mm": a["err_sum"] / a["err_n"] if a["err_n"] else 0.0,
                    "false_grasp": a["fg"] / a["photo"] if a["photo"] else 0.0}
    return out


def collect(regime, **kw):
    rows = [run_seed(regime, s, **kw) for s in SEEDS]
    return {arm: [row[arm] for row in rows] for arm in ARMS}


def col(rows, key):
    return [x[key] for x in rows]


def report(regime):
    res = collect(regime)
    print(f"{regime}:")
    print(f"  declared: {DECLARED[regime]}")
    for arm in ARMS:
        print(f"  {arm} " + " ".join(
            f"{key} {fmt_pair(*mean_sd(col(res[arm], key)))}" for key in METRICS))
    for a, b in PAIRS:
        for key in METRICS:
            print(f"  paired {a[0]}-{b[0]} {key}: "
                  f"{verdict(col(res[a], key), col(res[b], key))}")
    return res


def main():
    print("PointVLA frozen-injector toy: frozen 2D VLA head plus a lightweight "
          "additive point-cloud injection at one declared block")
    print("synthetic stand-in, scalar grasp-height model, not DexVLA; not a "
          "GPU / RealSense / UR5e run (本页未运行); not OctoMap / TSDF / 3DGS / "
          "SpatialVLA; PointVLA paper scores are not reproduced; paper "
          "statements 以论文为准")
    print(f"seeds={len(SEEDS)} n_blocks={N_BLOCKS} eta={num(ETA)} "
          f"sig_grip={num(SIG_GRIP)} grip_thr={num(GRIP_THR)} tol={num(TOL)} "
          f"n_pts={N_PTS} n_scenes={N_SCENES} (declared)")
    print("arm ordering follows from the declared block-importance profile and "
          "noise levels")
    print("Regimes and parameters were written before the first run")
    print("rule: real scene grasp needs |z_cmd - z_true| < TOL and a closed "
          "gripper; photo scene success = no grasp; presence check "
          "z3d - table_est > PRES_THR")
    print(f"hand_calc A systematic height error under the shift: "
          f"(1-rgb_cue)*(H_SHIFT-H_TRAIN) = "
          f"{num((1.0 - RGB_CUE) * (H_SHIFT - H_TRAIN))} m vs TOL {num(TOL)}")
    print(f"hand_calc sd of cloud mean = SIG_PC/sqrt(N_PTS) = "
          f"{num(SIG_PC / math.sqrt(N_PTS))} m")
    for name, blk in (("no injection", None), ("LATE_BLOCK", LATE_BLOCK),
                      ("EARLY_BLOCK", EARLY_BLOCK)):
        q = q_of(blk)
        phi = 0.5 * (1.0 + math.erf((q - GRIP_THR) / SIG_GRIP / math.sqrt(2.0)))
        print(f"hand_calc q ({name}) = {num(q)}, closing probability "
              f"Phi((q-{num(GRIP_THR)})/{num(SIG_GRIP)}) = {num(phi)}")
    print("hand_calc skip-block proxy 1-W_BLOCK[j]: " +
          " ".join(num(1.0 - w) for w in W_BLOCK))
    base = {}
    for regime in ("train_height", "height_shift", "real_vs_photo",
                   "corrupted_cloud"):
        base[regime] = report(regime)
    print("alternative parameters (declared before the run, same seeds, not "
          "adopted):")
    alt = collect("height_shift", late_block=3)
    q3 = q_of(3)
    print(f"  height_shift injection at block 3 (q={num(q3)}): "
          f"paired X-B success: "
          f"{verdict(col(alt['B_late'], 'success'),
                     col(base['height_shift']['B_late'], 'success'))}")
    alt = collect("corrupted_cloud", median=True)
    print(f"  corrupted_cloud z3d as median in B: paired B_median-A success: "
          f"{verdict(col(alt['B_late'], 'success'),
                     col(base['corrupted_cloud']['A_2d'], 'success'))}")
    alt = collect("train_height", tol=0.02)
    print(f"  train_height TOL=0.02: paired B-A success: "
          f"{verdict(col(alt['B_late'], 'success'),
                     col(alt['A_2d'], 'success'))}")
    alt = collect("height_shift", rgb_cue=0.3)
    print(f"  height_shift RGB_CUE=0.3: paired B-A success: "
          f"{verdict(col(alt['B_late'], 'success'),
                     col(alt['A_2d'], 'success'))}")
    print("No winner beyond the declared block profile: late injection keeps "
          "the frozen 2D grip and adds height and presence from the cloud; "
          "early injection or a corrupted cloud can hurt")
    print("DexVLA / GPU / RealSense / UR5e: 本页未运行; PointVLA paper results "
          "以论文为准")


if __name__ == "__main__":
    main()
