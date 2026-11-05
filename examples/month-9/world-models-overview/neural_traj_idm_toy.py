#!/usr/bin/env python3
"""neural_traj_idm_toy.py: DreamGen-style neural trajectories on 2-D frames (stdlib).

DreamGen (arXiv 2505.12705) is a 4-stage recipe; this toy keeps the stages and
replaces video pixels with synthetic 2-D "frames" f = R s of a point robot:
  1. fine-tune WM  : fit the world model's frame-step map on a few real teleop
                     trajectories (OLS of df on (f_goal - f, 1))
  2. roll out WM   : from (initial frame, goal frame) pairs, generate frame
                     sequences -- no actions in them, like generated videos
  3. pseudo-label  : an inverse dynamics model (IDM), fitted on REAL labelled
                     pairs (df -> a), labels the GENERATED frames
  4. train policy  : behaviour cloning (OLS) on the neural trajectories
Two error sources are separate knobs, swept one at a time:
  WM_ERR   generated frames drift / jitter away from real physics
  IDM_ERR  the IDM sees noisy frames when it is fitted -> attenuated labels
Fair comparison: matched trajectory count (K_TRAJ real vs K_TRAJ neural, same
instruction list), the same shared evaluation starts and evaluation noise for
every arm. Measured knob effect is printed (wm_frame_rmse, idm_rmse, and
idm_gain = fitted IDM diagonal / exact inverse; below 1 = shrunk labels) next to
the policy outcome. No pixels, no video model, no GPU; WAN/Cosmos fine-tuning,
video generation and GR1 robots are not run on this page (本页未运行).
DreamGen Bench's correlation with policy success is a paper claim only; this
toy measures nothing about it.
usage: python3 neural_traj_idm_toy.py
"""
from __future__ import annotations

import math
import random

SEED = 2505
T_STEPS = 15            # steps per trajectory
K_TRAJ = 40             # matched count: real and neural policies each get 40
K_WM_FIT = 10           # real trajectories used to fine-tune the WM and fit the IDM
N_EVAL = 60             # shared evaluation starts
GAIN = 0.3              # expert: a = GAIN * (g - s) + noise
EXPERT_NOISE = 0.01
PROCESS_NOISE = 0.005
SUCCESS_R = 0.05        # success radius in state units
# Frame map (stand-in for "camera"): rotation + scale, frames are 2-D.
R = ((1.2, -0.5), (0.5, 1.2))
DRIFT_DIR = (0.6, -0.8)  # fixed direction of WM drift (lesson-chosen)
WM_SWEEP = (0.0, 0.005, 0.01, 0.02, 0.04)
IDM_SWEEP = (0.0, 0.02, 0.05, 0.1, 0.2)


def matvec(m, v):
    return (m[0][0] * v[0] + m[0][1] * v[1], m[1][0] * v[0] + m[1][1] * v[1])


def frame(s):
    return matvec(R, s)


def solve(a, b):
    """Gaussian elimination with partial pivoting; a is n x n, b is n x k."""
    n = len(a)
    m = [list(a[i]) + list(b[i]) for i in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(m[r][c]))
        m[c], m[p] = m[p], m[c]
        for r in range(n):
            if r != c:
                f = m[r][c] / m[c][c]
                m[r] = [x - f * y for x, y in zip(m[r], m[c])]
    return [[m[i][j] / m[i][i] for j in range(n, len(m[0]))] for i in range(n)]


def ols(xs, ys):
    """Least squares W (d_in x d_out) minimising sum ||x W - y||^2."""
    d, k = len(xs[0]), len(ys[0])
    xtx = [[sum(x[i] * x[j] for x in xs) for j in range(d)] for i in range(d)]
    xty = [[sum(x[i] * y[j] for x, y in zip(xs, ys)) for j in range(k)] for i in range(d)]
    return solve(xtx, xty)


def apply(w, x):
    return tuple(sum(x[i] * w[i][j] for i in range(len(x))) for j in range(len(w[0])))


def instructions(rng, n):
    """(start state, goal state) pairs = 'initial frame + language' stand-in."""
    out = []
    for _ in range(n):
        s = (rng.uniform(-1, 1), rng.uniform(-1, 1))
        g = (rng.uniform(-1, 1), rng.uniform(-1, 1))
        out.append((s, g))
    return out


def real_rollout(s, g, rng):
    """Teleop on the real robot: frames AND true action labels."""
    frames, acts = [frame(s)], []
    for _ in range(T_STEPS):
        a = (GAIN * (g[0] - s[0]) + rng.gauss(0, EXPERT_NOISE),
             GAIN * (g[1] - s[1]) + rng.gauss(0, EXPERT_NOISE))
        s = (s[0] + a[0] + rng.gauss(0, PROCESS_NOISE), s[1] + a[1] + rng.gauss(0, PROCESS_NOISE))
        acts.append(a)
        frames.append(frame(s))
    return frames, acts


def fit_wm(real):
    """Stage 1: frame-step map df = [f_goal - f, 1] W_wm, fitted on real data."""
    xs, ys = [], []
    for frames, _acts, fg in real:
        for t in range(T_STEPS):
            f, f2 = frames[t], frames[t + 1]
            xs.append((fg[0] - f[0], fg[1] - f[1], 1.0))
            ys.append((f2[0] - f[0], f2[1] - f[1]))
    return ols(xs, ys)


def wm_rollout(w_wm, f0, fg, wm_err, rng):
    """Stage 2: generated frames only (no actions), with drift + jitter."""
    frames, f = [f0], f0
    for _ in range(T_STEPS):
        df = apply(w_wm, (fg[0] - f[0], fg[1] - f[1], 1.0))
        f = (f[0] + df[0] + wm_err * DRIFT_DIR[0] + rng.gauss(0, wm_err),
             f[1] + df[1] + wm_err * DRIFT_DIR[1] + rng.gauss(0, wm_err))
        frames.append(f)
    return frames


def fit_idm(real, idm_err, rng):
    """Stage 3 model: IDM (df -> a) fitted on REAL labelled pairs; idm_err = frame noise it sees."""
    xs, ys = [], []
    for frames, acts, _fg in real:
        for t in range(T_STEPS):
            f = [(x + rng.gauss(0, idm_err), y + rng.gauss(0, idm_err)) for x, y in frames[t:t + 2]]
            xs.append((f[1][0] - f[0][0], f[1][1] - f[0][1], 1.0))
            ys.append(acts[t])
    return ols(xs, ys)


def idm_label(w_idm, frames):
    return [apply(w_idm, (frames[t + 1][0] - frames[t][0], frames[t + 1][1] - frames[t][1], 1.0))
            for t in range(T_STEPS)]


def fit_policy(trajs):
    """Stage 4: BC policy a = [f_goal - f, 1] W_pi (OLS)."""
    xs, ys = [], []
    for frames, acts, fg in trajs:
        for t in range(T_STEPS):
            xs.append((fg[0] - frames[t][0], fg[1] - frames[t][1], 1.0))
            ys.append(acts[t])
    return ols(xs, ys)


def evaluate(w_pi, evals):
    """Shared starts and a re-seeded noise stream for every arm."""
    rng = random.Random(SEED + 1)
    wins, dist = 0, 0.0
    for s, g in evals:
        fg = frame(g)
        for _ in range(T_STEPS):
            f = frame(s)
            a = apply(w_pi, (fg[0] - f[0], fg[1] - f[1], 1.0))
            s = (s[0] + a[0] + rng.gauss(0, PROCESS_NOISE), s[1] + a[1] + rng.gauss(0, PROCESS_NOISE))
        d = math.hypot(s[0] - g[0], s[1] - g[1])
        wins += d < SUCCESS_R
        dist += d
    return wins, dist / len(evals)


def rmse(pairs):
    return math.sqrt(sum((a - b) ** 2 for a, b in pairs) / len(pairs))


def main() -> None:
    rng = random.Random(SEED)
    instr = instructions(rng, K_TRAJ)
    evals = instructions(random.Random(SEED + 2), N_EVAL)
    real = []
    for s, g in instr:
        frames, acts = real_rollout(s, g, rng)
        real.append((frames, acts, frame(g)))
    fit_set = real[:K_WM_FIT]
    w_wm = fit_wm(fit_set)
    held = real[K_WM_FIT:]

    print(f"seed={SEED} T={T_STEPS} K_TRAJ={K_TRAJ} (matched) K_WM_FIT={K_WM_FIT} "
          f"N_EVAL={N_EVAL} success_r={SUCCESS_R}")
    print("stages: 1 fit WM on real -> 2 WM rollout frames -> 3 IDM pseudo-labels -> 4 BC policy")
    print(f"stage1 WM step gain diag={w_wm[0][0]:.3f},{w_wm[1][1]:.3f} (expert in frames: {GAIN})")
    k, d = evaluate(fit_policy(real), evals)
    print(f"real_traj  policy (true labels, K={K_TRAJ})   success={k}/{N_EVAL} mean_final_dist={d:.4f}")

    def neural(wm_err, idm_err):
        r = random.Random(SEED + 3)  # same generation noise stream for every grid point
        w_idm = fit_idm(fit_set, idm_err, random.Random(SEED + 4))
        idm_pairs = []
        for frames, acts, _fg in held:  # IDM error measured on held-out REAL pairs
            idm_pairs += [(p, q) for pa, ta in zip(idm_label(w_idm, frames), acts) for p, q in zip(pa, ta)]
        wm_pairs, trajs = [], []
        for (s, g), (rframes, _a, fg) in zip(instr, real):
            gen = wm_rollout(w_wm, frame(s), fg, wm_err, r)
            wm_pairs += [(p, q) for gf, rf in zip(gen, rframes) for p, q in zip(gf, rf)]
            trajs.append((gen, idm_label(w_idm, gen), fg))
        k, d = evaluate(fit_policy(trajs), evals)
        ideal = R[0][0] / (R[0][0] * R[1][1] - R[0][1] * R[1][0])  # diag of the exact inverse map
        gain = (w_idm[0][0] + w_idm[1][1]) / 2 / ideal
        return rmse(wm_pairs), rmse(idm_pairs), gain, k, d

    curves = {}
    for name, sweep in (("wm_sweep", WM_SWEEP), ("idm_sweep", IDM_SWEEP)):
        knob = "WM_ERR" if name == "wm_sweep" else "IDM_ERR"
        print(f"{name}: {knob} varies, other knob = 0, same eval starts")
        print(f"  {'knob':>6} {'wm_frame_rmse':>13} {'idm_rmse':>9} {'idm_gain':>8} {'success':>8} {'mean_final_dist':>15}")
        rows = []
        for v in sweep:
            wm_r, idm_r, gain, k, d = neural(v, 0.0) if name == "wm_sweep" else neural(0.0, v)
            rows.append(k)
            print(f"  {v:6.3f} {wm_r:13.4f} {idm_r:9.4f} {gain:8.3f} {k:5d}/{N_EVAL} {d:15.4f}")
        curves[name] = rows
    for name, rows in curves.items():
        assert rows[0] >= rows[-1] and rows[-1] < rows[0], f"{name}: error must cost success"
    print(f"ok: two separate drop curves (wm {curves['wm_sweep'][0]}->{curves['wm_sweep'][-1]}, "
          f"idm {curves['idm_sweep'][0]}->{curves['idm_sweep'][-1]} of {N_EVAL}); "
          "IDM fitted on real pairs, applied to WM frames; DreamGen Bench correlation = paper claim only; "
          "video WM / GPU 本页未运行")


if __name__ == "__main__":
    main()
