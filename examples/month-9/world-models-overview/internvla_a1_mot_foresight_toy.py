#!/usr/bin/env python3
"""InternVLA-A1-style foresight: action only vs understanding + foresight + action vs corrupted foresight.

Synthetic 1-D conveyor scenes, stdlib only.  Not InternVLA-A1, not a
Mixture-of-Transformers, not a COSMOS VAE and not a 2B / 3B model; no
weights, no GPU, no RoboTwin and no real robot: 本页未运行.  Paper statements
and numbers (arXiv 2601.02456, for example +26.7 % on dynamic tasks or 692M
frames) 以论文为准; nothing here reproduces them.

What the paper body says (and what this toy keeps): three experts share one
masked self-attention stack with a strict flow understanding -> generation
-> action.  The understanding expert encodes the instruction and the current
views; the generation expert takes the current frame and a historical frame
m steps back and predicts the latent of the frame m steps ahead; the action
expert conditions on both and outputs an action chunk.  Video-prediction
policies are described as brittle when the prediction is wrong.

Toy: each scene has two objects on a conveyor; the instruction names one of
them.  The shared "understanding" stand-in picks the named object (identical
for every arm).  The target moves at velocity v; the robot sees two noisy
position frames, at t - H and at t, and must aim at where the target will be
at t + H, when the gripper arrives.
Arms:
  A_action_only : aims at the current observed position obs_t (no foresight)
  B_foresight   : a stand-in generation expert predicts the future position
                  f = obs_t + (obs_t - obs_{t-H}) (same interval back and
                  ahead, constant velocity); the action expert aims at f
  C_corrupt     : B, but with probability P_CORRUPT the foresight is
                  corrupted by an offset of CORRUPT_CM with a random sign
                  (a wrong future frame), and the action expert still trusts it
aim_err = |aim - x(t + H)| in cm; success iff aim_err < TOL (strict).

Common random numbers: for each (regime, seed) the scenes (positions,
instruction, velocity), the two observation-noise draws and the corruption
draws are generated once and shared by every arm; arms differ only in how
they turn the same frames into an aim point.
No integration step: closed-form positions x(t) = x0 + v*t, no ODE, no
time-step criterion.

Regimes and parameters were written before the first run:
  static       : v = 0, SIGMA = SIGMA_LO
                 - A and B may near-tie on success; keep
  dynamic      : |v| in [V_LO, V_HI] with a random sign, SIGMA = SIGMA_LO
                 - B consistent better than A
  static_noisy : v = 0, SIGMA = SIGMA_HI
                 - extrapolating noisy frames amplifies noise; B may lose; keep
  in every regime C (corrupted foresight) consistent lose against B; keep
Alternatives, also written before the first run, on the same seeds:
  TOL = 3.0 cm instead of 2.0 cm (dynamic and static_noisy);
  P_CORRUPT = 0.1 instead of 0.3 (dynamic).
All lengths, speeds, noise levels and probabilities are declared toy parameters.
"""
from __future__ import annotations

import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
N_SCENES = 50
X_LO, X_HI = 0.0, 40.0   # cm, object positions at t (toy)
H = 0.5                  # s, foresight horizon = history interval (toy)
V_LO, V_HI = 10.0, 30.0  # cm/s, conveyor speed range in dynamic scenes (toy)
SIGMA_LO = 0.3           # cm, observation noise (toy)
SIGMA_HI = 1.2           # cm, noisy-frame observation noise (toy)
P_CORRUPT = 0.3          # probability that C's foresight frame is wrong (toy)
CORRUPT_CM = 6.0         # cm, size of the wrong-frame offset (toy)
TOL = 2.0                # cm, success iff aim_err < TOL
ARMS = ("A_action_only", "B_foresight", "C_corrupt")
REGIMES = {"static": (False, SIGMA_LO), "dynamic": (True, SIGMA_LO), "static_noisy": (False, SIGMA_HI)}
METRICS = ("aim_err", "success")


def scenes(regime, seed):
    moving, sigma = REGIMES[regime]
    rng = random.Random(f"internvla-a1|{regime}|{seed}")
    out = []
    for _ in range(N_SCENES):
        pos = (rng.uniform(X_LO, X_HI), rng.uniform(X_LO, X_HI))
        target = rng.randrange(2)
        speed = rng.uniform(V_LO, V_HI)
        sign = 1.0 if rng.random() < 0.5 else -1.0
        v = sign * speed if moving else 0.0
        n_past, n_now = rng.gauss(0.0, sigma), rng.gauss(0.0, sigma)
        u_corrupt, s_corrupt = rng.random(), (1.0 if rng.random() < 0.5 else -1.0)
        out.append((pos, target, v, n_past, n_now, u_corrupt, s_corrupt))
    return out


def understand(pos, target):
    """Shared understanding stand-in: the instruction names the target; identical for every arm."""
    return pos[target]


def aim(arm, scene, p_corrupt):
    pos, target, v, n_past, n_now, u_corrupt, s_corrupt = scene
    x_now = understand(pos, target)
    obs_past = x_now - v * H + n_past
    obs_now = x_now + n_now
    if arm == "A_action_only":
        return obs_now
    foresight = obs_now + (obs_now - obs_past)
    if arm == "C_corrupt" and u_corrupt < p_corrupt:
        foresight += s_corrupt * CORRUPT_CM
    return foresight


def evaluate(arm, regime, seed, tol=TOL, p_corrupt=P_CORRUPT):
    errs, ok = [], 0
    for scene in scenes(regime, seed):
        pos, target, v = scene[0], scene[1], scene[2]
        truth = pos[target] + v * H
        e = abs(aim(arm, scene, p_corrupt) - truth)
        errs.append(e)
        ok += 1 if e < tol else 0
    return {"aim_err": sum(errs) / len(errs), "success": ok / N_SCENES}


def mean_sd(xs):
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


def collect(regime, tol=TOL, p_corrupt=P_CORRUPT):
    return {arm: [evaluate(arm, regime, s, tol, p_corrupt) for s in SEEDS] for arm in ARMS}


def col(rows, key):
    return [r[key] for r in rows]


def report(regime):
    res = collect(regime)
    moving, sigma = REGIMES[regime]
    print(f"{regime} (moving={moving}, SIGMA={sigma:.1f} cm):")
    for arm in ARMS:
        parts = [f"{key} {fmt_pair(*mean_sd(col(res[arm], key)))}" for key in METRICS]
        print(f"  {arm} " + " ".join(parts))
    for key in METRICS:
        print(f"  paired B-A {key}: {verdict(col(res['B_foresight'], key), col(res['A_action_only'], key))}")
    for key in METRICS:
        print(f"  paired C-B {key}: {verdict(col(res['C_corrupt'], key), col(res['B_foresight'], key))}")
    print(f"  paired C-A success: {verdict(col(res['C_corrupt'], 'success'), col(res['A_action_only'], 'success'))}")


def main():
    print("Synthetic 1-D conveyor toy; action only vs understanding + foresight + action vs corrupted foresight; not InternVLA-A1")
    print(f"seeds={len(SEEDS)} N_SCENES={N_SCENES} H={H:.1f} s V=[{V_LO:.1f}, {V_HI:.1f}] cm/s "
          f"SIGMA_LO={SIGMA_LO:.1f} cm SIGMA_HI={SIGMA_HI:.1f} cm (declared toy parameters)")
    print(f"P_CORRUPT={P_CORRUPT:.1f} CORRUPT_CM={CORRUPT_CM:.1f} cm TOL={TOL:.1f} cm "
          f"(success iff aim_err < TOL, strict; declared toy parameters)")
    print("No integration step: closed-form positions x(t) = x0 + v*t, no time-step criterion")
    print("Regimes and parameters were written before the first run")
    print(f"hand_calc target travel during H: |v|*H from {V_LO:.1f}*{H:.1f} = {V_LO * H:.4f} cm "
          f"to {V_HI:.1f}*{H:.1f} = {V_HI * H:.4f} cm, never < TOL={TOL:.1f} cm")
    print(f"hand_calc foresight noise sd = sqrt(5)*SIGMA: {num(math.sqrt(5) * SIGMA_LO)} cm at SIGMA_LO, "
          f"{num(math.sqrt(5) * SIGMA_HI)} cm at SIGMA_HI (A's sd is SIGMA)")
    for regime in REGIMES:
        report(regime)
    for regime in ("dynamic", "static_noisy"):
        print(f"alternative TOL=3.0 cm on {regime} (same seeds):")
        alt = collect(regime, tol=3.0)
        for arm in ARMS:
            print(f"  {arm}@alt success {fmt_pair(*mean_sd(col(alt[arm], 'success')))}")
        print(f"  paired B-A success@alt: {verdict(col(alt['B_foresight'], 'success'), col(alt['A_action_only'], 'success'))}")
        print(f"  paired C-B success@alt: {verdict(col(alt['C_corrupt'], 'success'), col(alt['B_foresight'], 'success'))}")
    print("alternative P_CORRUPT=0.1 on dynamic (same seeds, same corruption draws):")
    alt = collect("dynamic", p_corrupt=0.1)
    print(f"  C_corrupt@alt success {fmt_pair(*mean_sd(col(alt['C_corrupt'], 'success')))}")
    print(f"  paired C-B success@alt: {verdict(col(alt['C_corrupt'], 'success'), col(alt['B_foresight'], 'success'))}")
    print("No winner declared: foresight pays when the target moves, costs precision on still noisy frames, and a wrong foresight frame is trusted blindly")
    print("GPU / weights / RoboTwin / real robot: 本页未运行; InternVLA-A1 arXiv 2601.02456 statements and numbers 以论文为准")


if __name__ == "__main__":
    main()
