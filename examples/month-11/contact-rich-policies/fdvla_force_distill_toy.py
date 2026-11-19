#!/usr/bin/env python3
"""Synthetic force-distillation stand-in without a test-time force sensor.

Stdlib only. Shared contact-rich scenes, vision and state features, and the
true latent force are drawn once per (regime, seed) and then read by every
arm (common random numbers).

Arm A uses vision only. Arm B uses a predicted / distilled force token from
vision and state, with no true force channel at test time. Arm C injects a
noisy, biased, drop-out raw-sensor force. An unofficial clean oracle-force
arm is printed for comparison and is not a retuning target.

This is a linear lookup stand-in, not FD-VLA weights and not a real F/T
sensor. It is not a gated-insertion toy, not a slip-residual toy, not an
F/T-bias lesson, and not a measured-force hybrid MoE. Paper physical-
experiment success rates and the claim that a distilled token can
outperform direct sensor force are 以论文为准 and are not toy outputs.
GPU / F/T hardware: 本页未运行.

Regimes and parameters were written before the first run.

Labels: tie = identical on every seed; numerically zero = |paired mean| and sd
both < 1e-9; |m| <= sd = near-tie; |m| > sd = consistent gap (small if |m| < 20 %
of the smaller arm mean, else clear), with a sign count. ROUND_HALF_UP output.
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
SMALL_FRAC = 0.2000

N_SCENES = 25
BIAS = 0.0000
K_ERR = 1.0000
CLIP_LO = 0.0000
CLIP_HI = 1.0000
MU_Z = 0.4000
SIG_Z = 0.0800
W_V = 0.3000
W_S = 0.7000
EASY_V_SIG = 0.0200
EASY_S_SIG = 0.0200
EASY_V_COEF = 1.0000
EASY_V_OFF = 0.0000
OCC_V_SIG = 0.1500
OCC_S_SIG = 0.0600
OCC_V_COEF = 0.0000
OCC_V_OFF = 0.5000
SENSOR_BIAS = 0.5500
SENSOR_SIG = 0.0800
DROPOUT_P = 0.2500

ALT_OCC_V_SIG = 0.2000
ALT_W_V = 0.5000
ALT_W_S = 0.5000

METRICS = ("success",)
ARMS = ("A_vision_only", "B_distilled", "C_broken_sensor")
PAIRS = (("B", "A"), ("C", "B"), ("C", "A"))

REGIMES = {
    "easy_observed": "A and B may near-tie on success (easy, well-observed contact) - keep",
    "occluded_subtle": "B consistently above A on success (occluded / subtle contact) - keep",
}
C_EXPECT = "C loses to B on success (biased / drop-out raw sensor injection) - keep"
REGIME_IDS = {"easy_observed": 0, "occluded_subtle": 1}


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


def clip(x, lo=CLIP_LO, hi=CLIP_HI):
    return lo if x < lo else hi if x > hi else x


def regime_params(regime, occ_v_sig=OCC_V_SIG):
    if regime == "easy_observed":
        return EASY_V_COEF, EASY_V_OFF, EASY_V_SIG, EASY_S_SIG
    return OCC_V_COEF, OCC_V_OFF, occ_v_sig, OCC_S_SIG


def draw_scenes(regime, seed, occ_v_sig=OCC_V_SIG):
    rid = REGIME_IDS[regime]
    extra = 0 if occ_v_sig == OCC_V_SIG else 17
    rng = random.Random(seed + 1000 * rid + extra)
    v_coef, v_off, v_sig, s_sig = regime_params(regime, occ_v_sig=occ_v_sig)
    scenes = []
    for _ in range(N_SCENES):
        z = clip(rng.gauss(MU_Z, SIG_Z))
        v = clip(v_coef * z + v_off + rng.gauss(0.0, v_sig))
        s = clip(z + rng.gauss(0.0, s_sig))
        raw_noise = rng.gauss(0.0, SENSOR_SIG)
        drop = rng.random() < DROPOUT_P
        scenes.append((z, v, s, raw_noise, drop))
    return scenes


def success_of(f_hat, z):
    return clip(BIAS + (1.0000 - K_ERR * abs(f_hat - z)))


def tokens_of(scene, w_v, w_s):
    z, v, s, raw_noise, drop = scene
    f_a = v
    f_b = clip(w_v * v + w_s * s)
    f_c = 0.0000 if drop else clip(z + SENSOR_BIAS + raw_noise)
    f_o = z
    return f_a, f_b, f_c, f_o


def run_regime(regime, seed, occ_v_sig=OCC_V_SIG, w_v=W_V, w_s=W_S):
    scenes = draw_scenes(regime, seed, occ_v_sig=occ_v_sig)
    acc = {arm: 0.0 for arm in ARMS}
    acc["oracle_force"] = 0.0
    for scene in scenes:
        f_a, f_b, f_c, f_o = tokens_of(scene, w_v, w_s)
        z = scene[0]
        acc["A_vision_only"] += success_of(f_a, z)
        acc["B_distilled"] += success_of(f_b, z)
        acc["C_broken_sensor"] += success_of(f_c, z)
        acc["oracle_force"] += success_of(f_o, z)
    n = float(N_SCENES)
    return {k: {"success": acc[k] / n} for k in acc}


def main():
    w_sum = W_V + W_S
    print(
        "Force distillation toy: shared contact-rich scenes / vision / state / "
        "true force under common random numbers (linear lookup stand-in, not "
        "FD-VLA weights, not a real F/T sensor)"
    )
    print(
        "Paper physical-experiment success rates and the claim that a distilled "
        "token can outperform direct sensor force 以论文为准 and are not toy "
        "outputs; GPU / F/T hardware: 本页未运行"
    )
    print(
        f"seeds={len(SEEDS)} n_scenes={num(float(N_SCENES))} bias={num(BIAS)} "
        f"k_err={num(K_ERR)} clip_lo={num(CLIP_LO)} clip_hi={num(CLIP_HI)} "
        f"mu_z={num(MU_Z)} sig_z={num(SIG_Z)} w_v={num(W_V)} w_s={num(W_S)} "
        f"w_sum={num(w_sum)} easy_v_coef={num(EASY_V_COEF)} "
        f"easy_v_off={num(EASY_V_OFF)} easy_v_sig={num(EASY_V_SIG)} "
        f"easy_s_sig={num(EASY_S_SIG)} occ_v_coef={num(OCC_V_COEF)} "
        f"occ_v_off={num(OCC_V_OFF)} occ_v_sig={num(OCC_V_SIG)} "
        f"occ_s_sig={num(OCC_S_SIG)} sensor_bias={num(SENSOR_BIAS)} "
        f"sensor_sig={num(SENSOR_SIG)} dropout_p={num(DROPOUT_P)} "
        f"small_frac={num(SMALL_FRAC)}"
    )
    print("Regimes and parameters were written before the first run")
    print(
        "Common random numbers: the scene / vision / state / true-force draws "
        "are shared across arms at each regime and seed"
    )
    print(f"hand_calc n_scenes = {num(float(N_SCENES))}")
    print(f"hand_calc B weights {num(W_V)} + {num(W_S)} = {num(w_sum)}")
    print(
        f"hand_calc bias = {num(BIAS)} k_err = {num(K_ERR)} clip = "
        f"{num(CLIP_LO)} to {num(CLIP_HI)}"
    )
    print(f"hand_calc mu_z = {num(MU_Z)} sig_z = {num(SIG_Z)}")
    print(
        f"hand_calc easy: v = {num(EASY_V_COEF)} * z + {num(EASY_V_OFF)} + "
        f"N(0, {num(EASY_V_SIG)}), s = z + N(0, {num(EASY_S_SIG)})"
    )
    print(
        f"hand_calc occluded: v = {num(OCC_V_COEF)} * z + {num(OCC_V_OFF)} + "
        f"N(0, {num(OCC_V_SIG)}), s = z + N(0, {num(OCC_S_SIG)})"
    )
    print(
        f"hand_calc C sensor_bias = {num(SENSOR_BIAS)} sensor_sig = "
        f"{num(SENSOR_SIG)} dropout_p = {num(DROPOUT_P)}"
    )
    print(f"hand_calc small-gap threshold = {num(SMALL_FRAC)} of the smaller arm mean")
    print(
        f"hand_calc easy expected |A error| roughly {num(EASY_V_SIG)} "
        f"(formula, not a measured result)"
    )

    for r, exp in REGIMES.items():
        print(f"declared {r}: {exp}")
        print(f"declared {r} C: {C_EXPECT}")

    store = {r: {arm: {m: [] for m in METRICS} for arm in list(ARMS) + ["oracle_force"]} for r in REGIMES}
    alt_sig = {r: {arm: {m: [] for m in METRICS} for arm in ARMS} for r in REGIMES}
    alt_w = {r: {arm: {m: [] for m in METRICS} for arm in ARMS} for r in REGIMES}
    for seed in SEEDS:
        for r in REGIMES:
            official = run_regime(r, seed)
            sig_run = run_regime(r, seed, occ_v_sig=ALT_OCC_V_SIG)
            w_run = run_regime(r, seed, w_v=ALT_W_V, w_s=ALT_W_S)
            for arm in list(ARMS) + ["oracle_force"]:
                for m in METRICS:
                    store[r][arm][m].append(official[arm][m])
            for arm in ARMS:
                for m in METRICS:
                    alt_sig[r][arm][m].append(sig_run[arm][m])
                    alt_w[r][arm][m].append(w_run[arm][m])

    def arm_of(letter, arms=ARMS):
        return [a for a in arms if a.startswith(letter + "_")][0]

    for r in REGIMES:
        print(f"regime {r}")
        for arm in ARMS:
            mu, sd = mean_sd(store[r][arm]["success"])
            print(f"  {arm} success: {num(mu)}+-{num(sd)}")
        for left, right in PAIRS:
            print(
                f"  paired {left}-{right} success: "
                f"{verdict(store[r][arm_of(left)]['success'], store[r][arm_of(right)]['success'])}"
            )
        mu, sd = mean_sd(store[r]["oracle_force"]["success"])
        print(f"  oracle_force success: {num(mu)}+-{num(sd)}")
        print(
            f"  paired B-oracle success: "
            f"{verdict(store[r]['B_distilled']['success'], store[r]['oracle_force']['success'])}"
        )
        print(
            f"  paired oracle-A success: "
            f"{verdict(store[r]['oracle_force']['success'], store[r]['A_vision_only']['success'])}"
        )

    print("alternatives on the same seeds (not adopted):")
    print(f"  alternative occ_v_sig={num(ALT_OCC_V_SIG)}")
    for r in REGIMES:
        print(f"  regime {r}")
        for left, right in (("B", "A"), ("C", "B")):
            print(
                f"    paired {left}-{right} success: "
                f"{verdict(alt_sig[r][arm_of(left)]['success'], alt_sig[r][arm_of(right)]['success'])}"
            )
    print(f"  alternative B weights w_v={num(ALT_W_V)} w_s={num(ALT_W_S)}")
    for r in REGIMES:
        print(f"  regime {r}")
        for left, right in (("B", "A"), ("C", "B")):
            print(
                f"    paired {left}-{right} success: "
                f"{verdict(alt_w[r][arm_of(left)]['success'], alt_w[r][arm_of(right)]['success'])}"
            )


if __name__ == "__main__":
    main()
