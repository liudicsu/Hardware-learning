#!/usr/bin/env python3
"""Smith predictor vs a PI that ignores the delay vs a Smith predictor with the wrong model.

Synthetic, stdlib only.  Not lead-lag (Month 3), not discrete LQR (Month 5
state-space lesson), not the PID anti-windup lesson.  A real delayed plant on
a bench: 本页未运行.  Smith-predictor statements are 以原文为准 (Wikipedia).

Plant: first-order lag with a pure input delay of L = k * TS seconds,
    tau * dx/dt = -x + K * u(t - L),      y = x + measurement noise,
integrated with explicit Euler at H inside each controller period TS.
Controller: one discrete PI designed on the delay-free model G = K / (tau s + 1)
(IMC-style: Ti = tau, Kp = tau / (K * LAMBDA_C), target closed loop 1 / (LAMBDA_C s + 1)).
    A_pi_ignore     that PI acting on the delayed plant directly
    B_smith         the same PI inside a Smith predictor with the true K, tau and k:
                    e = r - y - (y_model - y_model_delayed)   (C_bar = C / (1 + C G (1 - z^-k)))
    C_smith_wrong   the same Smith structure with a wrong model: delay k_hat and gain K_hat off
Common random numbers: per (regime, seed) the plant K and tau, the reference
step, the load disturbance, the noise sequence and the model errors for C are
drawn once and shared by all three arms.  Arms differ only in the controller.

Explicit Euler on tau * dx/dt = -x + ... is stable when H < 2 * tau; the toy
asserts H < 2 * tau on every run.
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
TS = 0.01                 # s, controller period
SUB = 10                  # Euler sub-steps per controller period
H = TS / SUB              # s, plant integration step
LAMBDA_C = 0.15           # s, target delay-free closed-loop time constant
T_END = 8.0               # s
T_STEP, T_LOAD = 0.5, 4.0 # s: reference step, then an input load step
U_MAX = 1e6               # no actuator limit in practice; only stops float overflow
DIVERGED = 1e3            # ISE above this is reported as divergence
NUM_ZERO = 1e-9           # |m| and sd both below this: floating-point residue, not a gap

# name: (delay k in samples, delay-model error ratio range for C, gain-model error range for C)
REGIMES = {
    "zero_delay": (0, (0.3, 0.5), (-0.2, 0.2)),
    "long_delay": (20, (0.3, 0.5), (-0.2, 0.2)),
    "short_delay": (4, (0.3, 0.5), (-0.2, 0.2)),
    "wrong_delay_big": (20, (0.9, 1.1), (-0.05, 0.05)),
}
ARMS = ("A_pi_ignore", "B_smith", "C_smith_wrong")


def shared_draws(regime, seed):
    """Common random numbers: one plant, one reference, one disturbance, one noise sequence, one model error."""
    k, derr, gerr = REGIMES[regime]
    rng = random.Random(f"{regime}/{seed}")
    gain, tau = rng.uniform(0.8, 1.2), rng.uniform(0.4, 0.6)
    ref, load = rng.uniform(0.8, 1.2), rng.uniform(-0.4, -0.2)
    noise = [rng.gauss(0.0, 0.005) for _ in range(int(round(T_END / TS)) + 1)]
    d_ratio = rng.uniform(*derr) * rng.choice((-1.0, 1.0))
    g_ratio = rng.uniform(*gerr)
    return {"K": gain, "tau": tau, "k": k, "ref": ref, "load": load, "noise": noise,
            "k_hat_wrong": max(0, int(round(k * (1.0 + d_ratio)))), "K_hat_wrong": gain * (1.0 + g_ratio)}


def euler_first_order(x, u, gain, tau, h, steps):
    for _ in range(steps):
        x += h * (-x + gain * u) / tau
    return x


def run(regime, seed, arm):
    d = shared_draws(regime, seed)
    gain, tau, k = d["K"], d["tau"], d["k"]
    assert H < 2.0 * tau, (regime, seed, H, tau)
    kp, ti = tau / (gain * LAMBDA_C), tau          # PI designed on the delay-free nominal model
    if arm == "C_smith_wrong":
        k_hat, gain_hat = d["k_hat_wrong"], d["K_hat_wrong"]
    else:
        k_hat, gain_hat = k, gain
    n = int(round(T_END / TS))
    u_hist = [0.0] * (max(k, k_hat) + 1)            # u_hist[-1 - j] = u from j periods ago
    x = xm = 0.0
    ym_hist = [0.0] * (k_hat + 1)
    integ, ise, peak, settle = 0.0, 0.0, -math.inf, None
    diverged = False
    for i in range(n):
        t = i * TS
        r = d["ref"] if t >= T_STEP else 0.0
        y = x + d["noise"][i]
        e = r - y
        if arm != "A_pi_ignore":
            e -= ym_hist[-1] - ym_hist[-1 - k_hat]  # Smith: undelayed model output minus delayed model output
        integ += e * TS / ti
        u = max(-U_MAX, min(U_MAX, kp * (e + integ)))
        u_hist.append(u)
        load = d["load"] if t >= T_LOAD else 0.0
        x = euler_first_order(x, u_hist[-1 - k] + load, gain, tau, H, SUB)
        xm = euler_first_order(xm, u, gain_hat, tau, H, SUB)
        ym_hist.append(xm)
        err = r - x
        ise += err * err * TS
        if t >= T_STEP and t < T_LOAD:
            peak = max(peak, x)
            if abs(err) > 0.02 * d["ref"]:
                settle = t - T_STEP
        if not math.isfinite(x) or ise > DIVERGED:
            diverged = True
            break
    if diverged:
        return {"ise": math.inf, "over": math.inf, "settle": math.inf, "div": True}
    return {"ise": ise, "over": 100.0 * max(0.0, peak - d["ref"]) / d["ref"],
            "settle": (settle if settle is not None else 0.0) + TS, "div": False}


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
    if any(math.isinf(v) for v in xa + xb):
        da, db = sum(math.isinf(v) for v in xa), sum(math.isinf(v) for v in xb)
        return f"diverged on {da} vs {db} of {len(xa)} seeds: no mean reported, the diverging arm loses"
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


def cell(xs):
    if any(math.isinf(v) for v in xs):
        return f"diverged({sum(math.isinf(v) for v in xs)}/{len(xs)})"
    mu, sd = mean_sd(xs)
    return f"{num(mu)}+-{num(sd)}"


def main():
    print("Synthetic first-order-plus-delay toy; one PI designed on the delay-free model; arms differ only in the controller; shared plant / reference / load / noise draws")
    print(f"TS={TS} s, Euler H={H:.4f} s ({SUB} sub-steps), LAMBDA_C={LAMBDA_C} s, step at {T_STEP} s, load at {T_LOAD} s, T={T_END} s; seeds={len(SEEDS)}")
    tau_min = min(shared_draws(r, s)["tau"] for r in REGIMES for s in SEEDS)
    print(f"Euler stability: need H < 2*tau_min = {2.0 * tau_min:.4f} s; H={H:.4f} s ok")
    for r in ("long_delay", "wrong_delay_big"):
        for seed in SEEDS:
            d = shared_draws(r, seed)
            print(f"  {r} seed {seed}: K={d['K']:.3f} tau={d['tau']:.3f} s k={d['k']} C model k_hat={d['k_hat_wrong']} K_hat={d['K_hat_wrong']:.3f}")
    res = {r: {a: [run(r, s, a) for s in SEEDS] for a in ARMS} for r in REGIMES}
    print(f"regime arm ISE overshoot_% settle_s  (mean+-sd over seeds; 2 % band; settle capped at {T_LOAD - T_STEP:.2f} s = not settled before the load step)")
    for r, (k, derr, gerr) in REGIMES.items():
        print(f"{r} (delay {k} samples = {k * TS:.2f} s; C delay model off by {derr[0]:.0%}-{derr[1]:.0%}, gain {gerr[0]:+.0%}..{gerr[1]:+.0%})")
        for a in ARMS:
            print(f"  {a} " + " ".join(cell([x[m] for x in res[r][a]]) for m in ("ise", "over", "settle")))
        for other in ("A_pi_ignore", "C_smith_wrong"):
            for m in ("ise", "over", "settle"):
                xa, xb = [x[m] for x in res[r][other]], [x[m] for x in res[r]["B_smith"]]
                print(f"  paired {other[0]}-B {m}: {verdict(xa, xb)}")
    # Seeds 0–1 of wrong_delay_big round k_hat to 0, so C≡A; also print the pure-mismatch subset.
    subset = (2, 3, 4)
    print("wrong_delay_big pure-mismatch subset (seeds 2-4 only; seeds 0-1 have k_hat=0 so C≡A and inflate the 5-seed mean and sd)")
    for a in ARMS:
        rows = [res["wrong_delay_big"][a][s] for s in subset]
        print(f"  {a} " + " ".join(cell([x[m] for x in rows]) for m in ("ise", "over", "settle")))
    for other in ("A_pi_ignore", "C_smith_wrong"):
        for m in ("ise", "over", "settle"):
            xa = [res["wrong_delay_big"][other][s][m] for s in subset]
            xb = [res["wrong_delay_big"]["B_smith"][s][m] for s in subset]
            print(f"  paired {other[0]}-B {m}: {verdict(xa, xb)}")
    print("No winner declared: with a true model the Smith predictor takes the delay out of the loop; with no delay it is the same PI; with the wrong delay it can lose")
    print("Real delayed plant / bench: 本页未运行; Smith-predictor statements 以原文为准")


if __name__ == "__main__":
    main()
