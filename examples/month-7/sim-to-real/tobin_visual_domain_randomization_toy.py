#!/usr/bin/env python3
"""Tobin-style visual domain randomisation: canonical texture vs random textures vs random textures + wrong tau.

Synthetic 1-D "camera row" and a k-nearest-neighbour detector, stdlib only.
Not a deep network, not MuJoCo rendering, not a real camera and not the
contact-DR or lag-sysid toys on this page.  GPU training / real camera /
robot: 本页未运行.  Tobin et al. (arXiv 1703.06907) statements and numbers
(for example their 1.5 cm) 以论文为准; nothing here reproduces them.

What the paper body says (and what this toy keeps): train a detector only on
simulated images whose rendering is randomised (non-realistic random
textures: a random RGB value, a gradient between two random values or a
checker between two random values; lights; noise), so that with enough
variability the real world may look like just another variation.  The
detector never sees the colour of the object, only its size and shape.  The
paper's ablation reports that fewer unique textures hurt transfer.

Toy: a W-pixel grey-scale row shows one object of width OBJ_W at a
continuous position x (anti-aliased coverage) on a background.  Each surface
has a texture: flat, gradient or checker between grey values.  A lighting
gain multiplies the row and Gaussian pixel noise is added.  The detector is
k-NN regression (K_NN neighbours, squared pixel distance) from the row to x.
Arms:
  A_canonical : trained on ONE canonical texture (bright flat object on a
                dark flat background, gain 1)
  B_random    : trained on PALETTE random textures (Tobin-style) and random
                gains; the held-out test textures are never in the palette
  C_rand_tau  : B's detector unchanged, but the grasp controller uses a wrong
                latency tau (TAU_SIM) instead of the real TAU_REAL
Grasp proxy: the object moves at U px/s on a conveyor; the gripper arrives
TAU_REAL after the frame and aims at x_hat + U * tau_model.  grasp_err =
|aim - true position at arrival|; success iff grasp_err < TOL (strict).
A and B use tau_model = TAU_REAL (dynamics-aware); C uses TAU_SIM.

Common random numbers: for each seed one training set of positions and
pixel noise is drawn once and shared by A and B (they differ only in
textures and gains); for each (regime, seed) one test set (positions,
textures, gains, noise) is shared by every arm.
No integration step: closed-form positions, no ODE, no time-step criterion.

Regimes and parameters were written before the first run:
  heldout   : held-out "real" textures, static object (U = 0)
              - B consistent better transfer than A; keep
              - C equals B (tau does not matter when nothing moves)
  canonical : test texture identical to A's training texture, U = 0
              - A and B may near-tie, or B may lose (over-randomisation); keep
  moving    : held-out textures, U = U_MOVE px/s
              - C consistent lose vs B even with visual DR (appearance does
                not fix a wrong tau); keep
Alternatives, also written before the first run, on the same seeds:
  PALETTE = 10 random textures instead of 200 (heldout);
  TOL = 2.0 px instead of 1.0 px (moving).
All sizes, colours, gains, U and tau values are declared toy parameters.
"""
from __future__ import annotations

import math
import random

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
W = 24                  # pixels in the camera row (toy)
OBJ_W = 4.0             # object width, px (toy)
X_LO, X_HI = 2.0, 18.0  # object left edge range, px
N_TRAIN = 600
N_TEST = 40
K_NN = 3
PIX_SIGMA = 0.02        # pixel noise (toy)
PALETTE = 200           # unique random texturizations for B (toy)
GAIN_LO, GAIN_HI = 0.6, 1.4
U_MOVE = 30.0           # conveyor speed, px/s (toy)
TAU_REAL = 0.10         # s, real camera-to-gripper latency (toy)
TAU_SIM = 0.05          # s, the wrong latency C's controller uses (toy)
TOL = 1.0               # px, grasp succeeds iff grasp_err < TOL
ARMS = ("A_canonical", "B_random", "C_rand_tau")
CANON = (("flat", 0.80, 0.80), ("flat", 0.20, 0.20))   # (object, background)
# Held-out "real" textures: fixed, never drawn into B's palette.
REAL = (
    (("flat", 0.35, 0.35), ("checker", 0.60, 0.75)),
    (("gradient", 0.90, 0.70), ("flat", 0.50, 0.50)),
    (("checker", 0.10, 0.30), ("gradient", 0.30, 0.60)),
    (("flat", 0.60, 0.60), ("flat", 0.85, 0.85)),
)
REGIMES = {"heldout": ("real", 0.0), "canonical": ("canon", 0.0), "moving": ("real", U_MOVE)}
KINDS = ("flat", "gradient", "checker")


def texture_value(tex, i):
    kind, a, b = tex
    if kind == "flat":
        return a
    if kind == "gradient":
        return a + (b - a) * i / (W - 1)
    return a if i % 2 == 0 else b


def render(x, obj, bg, gain, noise):
    row = []
    for i in range(W):
        cover = max(0.0, min(i + 1.0, x + OBJ_W) - max(float(i), x))
        v = cover * texture_value(obj, i) + (1.0 - cover) * texture_value(bg, i)
        row.append(gain * v + noise[i])
    return row


def random_texture(rng):
    kind = KINDS[rng.randrange(3)]
    a = rng.random()
    b = a if kind == "flat" else rng.random()
    return (kind, a, b)


def palette(seed, size):
    rng = random.Random(f"tobin-palette|{seed}|{size}")
    return [(random_texture(rng), random_texture(rng)) for _ in range(size)]


def train_draws(seed):
    """Shared by A and B: positions, pixel noise, palette picks, gains."""
    rng = random.Random(f"tobin-train|{seed}")
    xs = [rng.uniform(X_LO, X_HI) for _ in range(N_TRAIN)]
    noise = [[rng.gauss(0.0, PIX_SIGMA) for _ in range(W)] for _ in range(N_TRAIN)]
    picks = [rng.random() for _ in range(N_TRAIN)]
    gains = [rng.uniform(GAIN_LO, GAIN_HI) for _ in range(N_TRAIN)]
    return xs, noise, picks, gains


def train_set(arm, seed, size=PALETTE):
    xs, noise, picks, gains = train_draws(seed)
    if arm == "A_canonical":
        return [(render(x, CANON[0], CANON[1], 1.0, n), x) for x, n in zip(xs, noise)]
    pal = palette(seed, size)
    return [(render(x, *pal[int(p * size)], g, n), x) for x, n, p, g in zip(xs, noise, picks, gains)]


def test_draws(regime, seed):
    rng = random.Random(f"tobin-test|{regime}|{seed}")
    which = REGIMES[regime][0]
    out = []
    for _ in range(N_TEST):
        x = rng.uniform(X_LO, X_HI)
        if which == "canon":
            obj, bg, gain = CANON[0], CANON[1], 1.0
        else:
            obj, bg = REAL[rng.randrange(len(REAL))]
            gain = rng.uniform(0.8, 1.2)
        noise = [rng.gauss(0.0, PIX_SIGMA) for _ in range(W)]
        out.append((render(x, obj, bg, gain, noise), x))
    return out


def knn(train, row):
    best = sorted((sum((a - b) ** 2 for a, b in zip(img, row)), x) for img, x in train)[:K_NN]
    return sum(x for _, x in best) / K_NN


def evaluate(arm, regime, seed, train, tol=TOL):
    u = REGIMES[regime][1]
    tau_model = TAU_SIM if arm == "C_rand_tau" else TAU_REAL
    loc, grasp, ok = [], [], 0
    for row, x in test_draws(regime, seed):
        xh = knn(train, row)
        aim = xh + u * tau_model
        err = abs(aim - (x + u * TAU_REAL))
        loc.append(abs(xh - x))
        grasp.append(err)
        ok += 1 if err < tol else 0
    return {"loc_err": sum(loc) / len(loc), "grasp_err": sum(grasp) / len(grasp), "success": ok / N_TEST}


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
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


METRICS = ("loc_err", "grasp_err", "success")
_TRAIN = {}


def trained(arm, seed, size=PALETTE):
    key = ("A_canonical" if arm == "A_canonical" else "B_random", seed, size)
    if key not in _TRAIN:
        _TRAIN[key] = train_set(key[0], seed, size)
    return _TRAIN[key]


def collect(regime, size=PALETTE, tol=TOL):
    return {arm: [evaluate(arm, regime, s, trained(arm, s, size), tol) for s in SEEDS] for arm in ARMS}


def col(rows, key):
    return [r[key] for r in rows]


def report(regime):
    res = collect(regime)
    which, u = REGIMES[regime]
    print(f"{regime} (test textures={which}, U={u:.1f} px/s):")
    for arm in ARMS:
        parts = [f"{key} {fmt_pair(*mean_sd(col(res[arm], key)))}" for key in METRICS]
        print(f"  {arm} " + " ".join(parts))
    for key in METRICS:
        print(f"  paired B-A {key}: {verdict(col(res['B_random'], key), col(res['A_canonical'], key))}")
    for key in METRICS:
        print(f"  paired C-B {key}: {verdict(col(res['C_rand_tau'], key), col(res['B_random'], key))}")
    return res


def main():
    print("Synthetic 1-D camera-row toy with a k-NN detector; canonical vs random textures vs random textures + wrong tau; not a DNN")
    print(f"seeds={len(SEEDS)} W={W} px OBJ_W={OBJ_W:.1f} px N_TRAIN={N_TRAIN} N_TEST={N_TEST} K_NN={K_NN} "
          f"PIX_SIGMA={PIX_SIGMA:.2f} PALETTE={PALETTE} GAIN=[{GAIN_LO:.1f}, {GAIN_HI:.1f}] (declared toy parameters)")
    print(f"U_MOVE={U_MOVE:.1f} px/s TAU_REAL={TAU_REAL:.2f} s TAU_SIM={TAU_SIM:.2f} s TOL={TOL:.1f} px "
          f"(success iff grasp_err < TOL, strict; declared toy parameters)")
    print("No integration step: closed-form positions, no time-step criterion")
    print("Regimes and parameters were written before the first run")
    leaked = any(p in REAL or p == CANON for s in SEEDS for p in palette(s, PALETTE))
    print(f"peek_check: any held-out real texture or the canonical texture inside B's palette on any seed: {leaked}")
    bias = U_MOVE * (TAU_REAL - TAU_SIM)
    print(f"hand_calc wrong tau: aim error = U*(TAU_REAL - TAU_SIM) = {U_MOVE:.1f}*({TAU_REAL:.2f} - {TAU_SIM:.2f}) "
          f"= {bias:.4f} px, which is not < TOL={TOL:.1f} px even with a perfect detector")
    print(f"hand_calc object travel during TAU_REAL: U*TAU_REAL = {U_MOVE * TAU_REAL:.4f} px")
    for regime in REGIMES:
        report(regime)
    print("alternative PALETTE=10 on heldout (same seeds, same training positions and noise):")
    alt = collect("heldout", size=10)
    base = collect("heldout")
    print(f"  B_random@alt loc_err {fmt_pair(*mean_sd(col(alt['B_random'], 'loc_err')))} "
          f"(PALETTE={PALETTE}: {fmt_pair(*mean_sd(col(base['B_random'], 'loc_err')))})")
    print(f"  paired B-A loc_err@alt: {verdict(col(alt['B_random'], 'loc_err'), col(alt['A_canonical'], 'loc_err'))}")
    print(f"  paired B200-B10 loc_err: {verdict(col(base['B_random'], 'loc_err'), col(alt['B_random'], 'loc_err'))}")
    print("alternative TOL=2.0 px on moving (same seeds):")
    alt = collect("moving", tol=2.0)
    for arm in ARMS:
        print(f"  {arm}@alt success {fmt_pair(*mean_sd(col(alt[arm], 'success')))}")
    print(f"  paired C-B success@alt: {verdict(col(alt['C_rand_tau'], 'success'), col(alt['B_random'], 'success'))}")
    print("No winner declared: random textures buy transfer to unseen appearance, cost accuracy on the one texture A was trained on, and do nothing for a wrong tau")
    print("GPU training / real camera / robot: 本页未运行; Tobin et al. arXiv 1703.06907 statements and numbers 以论文为准")


if __name__ == "__main__":
    main()
