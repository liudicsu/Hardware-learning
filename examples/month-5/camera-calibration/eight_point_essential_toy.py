#!/usr/bin/env python3
"""Synthetic two-view eight-point estimate of the essential matrix E. Stdlib only.

Model assumptions (also stated in the lesson prose):
  pinhole cameras with the same known K (f = 800 px, principal point (640, 360),
  1280 x 720 image), no lens distortion, no outliers, static rigid scene;
  x2 = R x1 + t (camera-1 frame to camera-2 frame), E = [t]x R, and
  y2^T E y1 = 0 for calibrated coordinates y = K^-1 (u, v, 1).
  Pixel noise is i.i.d. Gaussian on both images; correspondences are known.

Arms (same noisy pixel correspondences for all three, common random numbers):
  A_raw_px      basic eight-point on raw pixel coordinates -> F, then E = K^T F K
  B_hartley_px  Hartley-normalised eight-point on pixels (per image: move the
                centroid to the origin, scale so the mean distance is sqrt(2)),
                F = T2^T Fbar T1, then E = K^T F K
  C_calib       basic eight-point on calibrated coordinates K^-1 x, no Hartley
                step (already roughly unit-scale, but not re-centred)
Every arm then gets the same internal-constraint step: SVD, replace the singular
values by (s, s, 0) with s = (s1 + s2) / 2, and scale to unit Frobenius norm.
Linear algebra: one-sided Jacobi SVD (Hestenes), no squaring of the design
matrix, so its condition number s1/s8 is reported as computed.

Metrics per seed (means over points):
  e_err   min over sign of ||E_hat - E_true||_F, both unit Frobenius norm
  epi_px  symmetric epipolar distance on 40 held-out clean points, pixels
  rot_deg rotation error after SVD pose recovery + cheirality vote
  t_deg   angle between recovered and true translation direction

Labels: tie = identical on every seed; |m| < 1e-9 and sd < 1e-9 = numerically
zero (floating-point residue), effectively a tie, no sign count; |paired mean| <= sd = near-tie / small
gap within seed noise; |m| > sd = consistent gap (small if |m| < 20 % of the
smaller arm mean, else clear), always with a sign count.
Real camera / OpenCV: 本页未运行. Wikipedia definitions: 以原文为准.
"""
from __future__ import annotations

import math
import random

F_PX, CX, CY, W_IMG, H_IMG = 800.0, 640.0, 360.0, 1280.0, 720.0
N_PTS, N_TEST = 40, 40
SEEDS = (0, 1, 2, 3, 4)
ARMS = ("A_raw_px", "B_hartley_px", "C_calib")
ROT_DEG = 8.0
# name, pixel noise sd, baseline (m), image patch (u0, v0, half-width) or None = whole image
REGIMES = (
    ("noise_free", 0.0, 0.5, None),
    ("pixel_noise", 1.0, 0.5, None),
    ("clustered", 0.5, 0.5, (900.0, 500.0, 100.0)),
    ("tiny_baseline", 1.0, 0.01, None),
)
METRICS = ("e_err", "epi_px", "rot_deg", "t_deg")
PAIRED = ("e_err", "epi_px", "t_deg")


# ---------- small dense linear algebra (lists of rows) ----------
def matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]


def transpose(a):
    return [list(r) for r in zip(*a)]


def matvec(a, v):
    return [sum(x * y for x, y in zip(r, v)) for r in a]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def det3(m):
    return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))


def skew(t):
    return [[0.0, -t[2], t[1]], [t[2], 0.0, -t[0]], [-t[1], t[0], 0.0]]


def fro(a):
    return math.sqrt(sum(x * x for r in a for x in r))


def svd(a, sweeps: int = 60):
    """One-sided Jacobi SVD of an m x n matrix (m >= n): returns U (m x n), s (desc), V (n x n)."""
    m, n = len(a), len(a[0])
    u = [list(r) for r in a]
    v = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for _ in range(sweeps):
        rotated = False
        for p in range(n - 1):
            for q in range(p + 1, n):
                al = sum(u[i][p] ** 2 for i in range(m))
                be = sum(u[i][q] ** 2 for i in range(m))
                ga = sum(u[i][p] * u[i][q] for i in range(m))
                if abs(ga) <= 1e-15 * math.sqrt(al * be) or ga == 0.0:
                    continue
                rotated = True
                zeta = (be - al) / (2.0 * ga)
                t = math.copysign(1.0, zeta) / (abs(zeta) + math.sqrt(1.0 + zeta * zeta))
                c = 1.0 / math.sqrt(1.0 + t * t)
                s = c * t
                for row in u:
                    row[p], row[q] = c * row[p] - s * row[q], s * row[p] + c * row[q]
                for row in v:
                    row[p], row[q] = c * row[p] - s * row[q], s * row[p] + c * row[q]
        if not rotated:
            break
    sig = [math.sqrt(sum(u[i][j] ** 2 for i in range(m))) for j in range(n)]
    order = sorted(range(n), key=lambda j: -sig[j])
    s_out = [sig[j] for j in order]
    u_out = [[(u[i][j] / sig[j]) if sig[j] > 0 else 0.0 for j in order] for i in range(m)]
    v_out = [[v[i][j] for j in order] for i in range(n)]
    return u_out, s_out, v_out


def svd3(e):
    """3x3 SVD with a proper orthonormal U even when s3 = 0 (u3 = u1 x u2)."""
    u, s, v = svd(e)
    u1, u2 = [r[0] for r in u], [r[1] for r in u]
    u3 = cross(u1, u2)
    return [[u1[i], u2[i], u3[i]] for i in range(3)], s, v


# ---------- geometry ----------
K = [[F_PX, 0.0, CX], [0.0, F_PX, CY], [0.0, 0.0, 1.0]]
KINV = [[1 / F_PX, 0.0, -CX / F_PX], [0.0, 1 / F_PX, -CY / F_PX], [0.0, 0.0, 1.0]]


def rodrigues(axis, ang):
    n = math.sqrt(sum(x * x for x in axis))
    x, y, z = (c / n for c in axis)
    c, s, C = math.cos(ang), math.sin(ang), 1 - math.cos(ang)
    return [[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
            [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
            [z * x * C - y * s, z * y * C + x * s, c + z * z * C]]


def project(p):
    return [F_PX * p[0] / p[2] + CX, F_PX * p[1] / p[2] + CY]


def scene(regime: tuple, seed: int) -> dict:
    """Common random numbers: pose, 3D points, held-out points and pixel noise are
    drawn once per (regime, seed) and every arm reads the same lists."""
    name, sigma, base, patch = regime
    rng = random.Random(1000 * [r[0] for r in REGIMES].index(name) + seed)
    rot = rodrigues([rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)], math.radians(ROT_DEG))
    tdir = [1.0, 0.2 * rng.uniform(-1, 1), 0.2 * rng.uniform(-1, 1)]
    nt = math.sqrt(sum(x * x for x in tdir))
    t = [base * x / nt for x in tdir]

    def draw():
        while True:
            if patch:
                u, v = rng.uniform(patch[0] - patch[2], patch[0] + patch[2]), rng.uniform(patch[1] - patch[2], patch[1] + patch[2])
            else:
                u, v = rng.uniform(0, W_IMG), rng.uniform(0, H_IMG)
            z = rng.uniform(4.0, 8.0)
            p1 = [(u - CX) / F_PX * z, (v - CY) / F_PX * z, z]
            p2 = [a + b for a, b in zip(matvec(rot, p1), t)]
            x2 = project(p2) if p2[2] > 0.5 else [-1.0, -1.0]
            if 0 <= x2[0] <= W_IMG and 0 <= x2[1] <= H_IMG:
                return project(p1), x2

    train = [draw() for _ in range(N_PTS)]
    test = [draw() for _ in range(N_TEST)]
    noisy = [([a + rng.gauss(0, sigma) for a in x1], [a + rng.gauss(0, sigma) for a in x2]) for x1, x2 in train] \
        if sigma > 0 else [(list(x1), list(x2)) for x1, x2 in train]
    e_true = matmul(skew(t), rot)
    nrm = fro(e_true)
    return {"R": rot, "t": t, "E": [[x / nrm for x in r] for r in e_true], "train": noisy, "test": test}


def hartley(pts):
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    md = sum(math.hypot(p[0] - cx, p[1] - cy) for p in pts) / len(pts)
    s = math.sqrt(2.0) / md
    return [[s, 0.0, -s * cx], [0.0, s, -s * cy], [0.0, 0.0, 1.0]]


def apply_h(h, p):
    q = matvec(h, [p[0], p[1], 1.0])
    return [q[0] / q[2], q[1] / q[2]]


def eight_point(p1, p2):
    """Rows (x2 x1, x2 y1, x2, y2 x1, y2 y1, y2, x1, y1, 1); e = right singular
    vector of the smallest singular value. Returns (3x3, condition s1/s8)."""
    rows = [[b[0] * a[0], b[0] * a[1], b[0], b[1] * a[0], b[1] * a[1], b[1], a[0], a[1], 1.0] for a, b in zip(p1, p2)]
    _, s, v = svd(rows)
    e = [r[8] for r in v]
    return [e[0:3], e[3:6], e[6:9]], s[0] / s[7]


def enforce_essential(e):
    u, s, v = svd3(e)
    m = (s[0] + s[1]) / 2.0
    out = matmul(matmul(u, [[m, 0, 0], [0, m, 0], [0, 0, 0]]), transpose(v))
    n = fro(out)
    return [[x / n for x in r] for r in out]


def estimate(arm: str, train) -> tuple[list, float]:
    x1 = [a for a, _ in train]
    x2 = [b for _, b in train]
    if arm == "A_raw_px":
        f, cond = eight_point(x1, x2)
    elif arm == "B_hartley_px":
        h1, h2 = hartley(x1), hartley(x2)
        fbar, cond = eight_point([apply_h(h1, p) for p in x1], [apply_h(h2, p) for p in x2])
        f = matmul(matmul(transpose(h2), fbar), h1)
    else:
        e, cond = eight_point([apply_h(KINV, p) for p in x1], [apply_h(KINV, p) for p in x2])
        return enforce_essential(e), cond
    return enforce_essential(matmul(matmul(transpose(K), f), K)), cond


def triangulate_depths(rot, t, y1, y2):
    """Least-squares depths (l1, l2) with l2 y2 = l1 R y1 + t."""
    a = matvec(rot, y1)
    b = [-x for x in y2]
    aa, ab, bb = sum(x * x for x in a), sum(x * y for x, y in zip(a, b)), sum(x * x for x in b)
    ra, rb = -sum(x * y for x, y in zip(a, t)), -sum(x * y for x, y in zip(b, t))
    det = aa * bb - ab * ab
    return (ra * bb - ab * rb) / det, (aa * rb - ab * ra) / det


def recover_pose(e, train):
    """Four (R, t) candidates from E = U diag(1,1,0) V^T; keep the one with the most
    points in front of both cameras (cheirality vote on the training points)."""
    u, _, v = svd3(e)
    if det3(u) < 0:
        u = [[-x for x in r] for r in u]
    if det3(v) < 0:
        v = [[-x for x in r] for r in v]
    w = [[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]
    u3 = [r[2] for r in u]
    ys = [(apply_h(KINV, a) + [1.0], apply_h(KINV, b) + [1.0]) for a, b in train]
    best = None
    for rr in (matmul(matmul(u, w), transpose(v)), matmul(matmul(u, transpose(w)), transpose(v))):
        for sgn in (1.0, -1.0):
            tt = [sgn * x for x in u3]
            front = 0
            for y1, y2 in ys:
                l1, l2 = triangulate_depths(rr, tt, y1, y2)
                front += (l1 > 0 and l2 > 0)
            if best is None or front > best[0]:
                best = (front, rr, tt)
    return best[1], best[2]


def angle_deg(a, b):
    c = sum(x * y for x, y in zip(a, b)) / math.sqrt(sum(x * x for x in a) * sum(x * x for x in b))
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def rot_err_deg(ra, rb):
    m = matmul(ra, transpose(rb))
    return math.degrees(math.acos(max(-1.0, min(1.0, (m[0][0] + m[1][1] + m[2][2] - 1) / 2))))


def epi_px(e, pts):
    f = matmul(matmul(transpose(KINV), e), KINV)
    tot = 0.0
    for x1, x2 in pts:
        p1, p2 = [x1[0], x1[1], 1.0], [x2[0], x2[1], 1.0]
        l2, l1 = matvec(f, p1), matvec(transpose(f), p2)
        r = sum(a * b for a, b in zip(p2, l2))
        tot += 0.5 * (abs(r) / math.hypot(l2[0], l2[1]) + abs(r) / math.hypot(l1[0], l1[1]))
    return tot / len(pts)


def evaluate(arm: str, sc: dict) -> dict:
    e, cond = estimate(arm, sc["train"])
    err = min(fro([[a - b for a, b in zip(ra, rb)] for ra, rb in zip(e, sc["E"])]),
              fro([[a + b for a, b in zip(ra, rb)] for ra, rb in zip(e, sc["E"])]))
    rot, t = recover_pose(e, sc["train"])
    return {"e_err": err, "epi_px": epi_px(e, sc["test"]), "rot_deg": rot_err_deg(rot, sc["R"]),
            "t_deg": angle_deg(t, sc["t"]), "log10_cond": math.log10(cond)}


# ---------- reporting (same label rules as the batch-13 lead-lag toy) ----------
def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x: float) -> str:
    """4 decimals, or 3 significant digits in e-notation when 4 decimals would hide it."""
    if x != 0.0 and abs(x) < 5e-4:
        return f"{x:.3e}"
    return f"{x:.4f}"


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


NUM_ZERO = 1e-9  # |m| and sd both below this: floating-point residue, not a gap


def verdict(xa, xb):
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return f"{fmt_pair(m, s)}: numerically zero (floating-point residue), effectively a tie"
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < 0.2 * min(mean_sd(xa)[0], mean_sd(xb)[0]):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def main() -> None:
    print("Synthetic two-view eight-point E; shared scenes / correspondences / pixel noise; not a real camera")
    print(f"K: f={F_PX:.0f} px c=({CX:.0f},{CY:.0f}) image {W_IMG:.0f}x{H_IMG:.0f}; points={N_PTS} held-out={N_TEST} "
          f"rotation={ROT_DEG:.0f} deg depth 4-8 m seeds={len(SEEDS)}")
    print("regime arm e_err epi_px rot_deg t_deg log10_cond(s1/s8)  (mean+-sd over seeds)")
    for regime in REGIMES:
        name = regime[0]
        scenes = [scene(regime, sd) for sd in SEEDS]
        res = {arm: [evaluate(arm, sc) for sc in scenes] for arm in ARMS}
        print(f"{name} (sigma={regime[1]} px, baseline={regime[2]} m, "
              f"{'patch ' + str(int(regime[3][0])) + ',' + str(int(regime[3][1])) + '+-' + str(int(regime[3][2])) + ' px' if regime[3] else 'whole image'})")
        for arm in ARMS:
            cells = []
            for k in METRICS + ("log10_cond",):
                mu, sd = mean_sd([r[k] for r in res[arm]])
                cells.append(f"{num(mu)}+-{num(sd)}")
            print(f"{name} {arm} " + " ".join(cells))
        for a, b in (("B_hartley_px", "A_raw_px"), ("C_calib", "B_hartley_px")):
            for k in PAIRED:
                print(f"{name} paired {a[0]}-{b[0]} {k}: {verdict([r[k] for r in res[a]], [r[k] for r in res[b]])}")
    print("noise_free: every arm recovers E to round-off; normalisation changes only digits far below any pixel")
    print("pixel_noise / clustered: raw pixels make s1/s8 huge, so the noise is weighted by coordinate size; Hartley fixes the scale")
    print("C_calib: K^-1 already gives unit-scale coordinates, so C stays within seed noise of B here; it skips only the re-centring")
    print("tiny_baseline: every arm loses the translation direction; epi_px stays small because it is blind to t when t is tiny")
    print("No winner declared; epi_px is blind to the translation direction when the baseline is tiny")
    print("Real camera / OpenCV: 本页未运行; Wikipedia definitions 以原文为准")


if __name__ == "__main__":
    main()
