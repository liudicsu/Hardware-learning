#!/usr/bin/env python3
"""Synthetic Reward-DAgger two-timescale progress-gate stand-in.

Stdlib only. Shared synthetic progress traces, not a VLM reward model and
not a LIBERO run. No real VLA, GPU reward model, or human-in-the-loop arm
is started. The existing corridor DAgger toy on this page is not redone,
and this is not HG-DAgger, HAMSTER, MAP-VLA, HIL-SERL, or BlenDAgger.

A shared task stream of progress traces is generated once per (regime,
seed) and then read by every arm (common random numbers). The expert
correction budget is the remaining steps after a takeover.

Arms:
  A_always -- human-gated / always-label stand-in: the expert is available
    on every policy state and watches the whole rollout.
  B_reward_gate -- two-timescale progress gate (Spearman, not Pearson);
    the expert is called only when the gate fires, then takes over the
    rest of that episode, and those states are aggregated.
  C_never -- a disabled / never-fire gate: no interventions.

A named alternative on the same seeds, not adopted, is the same gate with
tau_l = 1.0000, which fires the long window on uneventful traces.

Regimes and parameters were written before the first run.

Labels: tie = identical on every seed; numerically zero = |paired mean| and sd
both < 1e-9; |m| <= sd = near-tie; |m| > sd = consistent gap (small if |m| < 20 %
of the smaller arm mean, else clear), with a sign count. ROUND_HALF_UP output.

Gating equations, paper success / ROHE figures, and authorship stay 以论文为准.
Real VLA / GPU reward model / human-in-the-loop arm: 本页未运行.
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
SMALL_FRAC = 0.2000  # 20 % of the smaller-arm mean; printed as 0.2000

# Declared trace and official gate stand-in (not the paper's LIBERO grid).
T = 80  # steps per episode
N_EPS = 8  # episodes per seed
L_S = 8  # short window
L_L = 24  # long window
TAU_S = -0.5000
TAU_L = 0.2000
DELTA_MIN = 0.0800
SIG_PHI = 0.0150  # shared progress-trace noise
# Named alternative, same seeds, not adopted: a long-window threshold of 1.0000
# fires as soon as the long window is full on noisy uneventful traces.
TAU_L_ALT = 1.0000

# Drop + stall shape, written before the first run.
DROP_T = 32  # first index of the dropped-object step
RISE_TO = 0.7000
DROP_TO = 0.2500

ARMS = ("A_always", "B_reward_gate", "C_never")
METRICS = ("success", "calls", "effort_return")
PAIRS = (("B", "A"), ("B", "C"), ("C", "A"))

# name: (kind, declared expectation); written before the first run
REGIMES = {
    "uneventful": (
        "uneventful",
        "A and B may near-tie on autonomous success, with B using fewer expert calls - keep",
    ),
    "drop_stall": (
        "drop_stall",
        "B consistent better effort return than never-fire C, and more selective than A - keep",
    ),
}


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


def rng_for(*parts):
    h = 261004054
    for part in parts:
        if isinstance(part, str):
            for ch in part:
                h = (h * 131 + ord(ch)) & 0xFFFFFFFFFFFFFFFF
        else:
            h = (h * 131 + int(part)) & 0xFFFFFFFFFFFFFFFF
    return random.Random(h)


def average_ranks(values):
    n = len(values)
    order = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        # ranks are 1-based; ties take the average rank
        avg = 0.5 * ((i + 1) + (j + 1))
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def pearson(xs, ys):
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    nume = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    den = math.sqrt(vx * vy)
    if den < 1e-18:
        return 0.0
    return nume / den


def spearman(values):
    """Spearman rho: Pearson correlation of value ranks with time indices."""
    n = len(values)
    if n < 2:
        return 0.0
    ranks = average_ranks(values)
    times = list(range(1, n + 1))
    return pearson(ranks, times)


def clip01(x):
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def clean_progress(kind, t):
    if kind == "uneventful":
        return t / (T - 1)
    if kind == "drop_stall":
        if t < DROP_T:
            return RISE_TO * (t / DROP_T)
        return DROP_TO
    raise ValueError(kind)


def shared_traces(seed, kind):
    """Common random numbers: one noise field per regime and seed, all arms."""
    rng = rng_for("phi", kind, seed)
    traces = []
    needs = []
    for _ep in range(N_EPS):
        phi = []
        for t in range(T):
            phi.append(clip01(clean_progress(kind, t) + rng.gauss(0.0, SIG_PHI)))
        traces.append(phi)
        needs.append(kind == "drop_stall")
    return traces, needs


def gate_fires(phi, t, tau_s=TAU_S, tau_l=TAU_L, delta_min=DELTA_MIN, short_only=False):
    """Eq. 4 stand-in: g = g^s OR g^l, Spearman windows, short-window drop."""
    g_s = False
    if t + 1 >= L_S:
        window = phi[t + 1 - L_S : t + 1]
        rho_s = spearman(window)
        delta = max(window) - window[-1]
        g_s = (rho_s < tau_s) and (delta >= delta_min)
    g_l = False
    if not short_only and t + 1 >= L_L:
        rho_l = spearman(phi[t + 1 - L_L : t + 1])
        g_l = rho_l < tau_l
    return g_s or g_l


def first_fire(phi, **gate_kw):
    for t in range(T):
        if gate_fires(phi, t, **gate_kw):
            return t
    return None


def evaluate(arm, traces, needs, gate_kw=None):
    successes = []
    calls = []
    for phi, need in zip(traces, needs):
        if arm == "A_always":
            t_fire = 0
        elif arm == "C_never":
            t_fire = None
        elif arm == "B_reward_gate":
            t_fire = first_fire(phi, **(gate_kw or {}))
        else:
            raise ValueError(arm)
        if t_fire is None:
            calls.append(0.0)
            successes.append(0.0 if need else 1.0)
        else:
            calls.append(float(T - t_fire))
            successes.append(1.0)
    n = float(len(traces))
    success = sum(successes) / n
    mean_calls = sum(calls) / n
    effort_return = success / (1.0 + mean_calls / float(T))
    return {
        "success": success,
        "calls": mean_calls,
        "effort_return": effort_return,
    }


def run_regime(name, seed, gate_kw=None):
    kind, _decl = REGIMES[name]
    traces, needs = shared_traces(seed, kind)
    row = {}
    for arm in ARMS:
        if arm == "B_reward_gate":
            row[arm] = evaluate(arm, traces, needs, gate_kw=gate_kw)
        else:
            row[arm] = evaluate(arm, traces, needs)
    return row


def official_rows(name, gate_kw=None):
    return [run_regime(name, seed, gate_kw=gate_kw) for seed in SEEDS]


def print_regime(title, rows):
    print(f"regime {title}  (mean+-sd over seeds)")
    for arm in ARMS:
        suc = [r[arm]["success"] for r in rows]
        cal = [r[arm]["calls"] for r in rows]
        eff = [r[arm]["effort_return"] for r in rows]
        print(
            f"  {arm} success {num(mean_sd(suc)[0])}+-{num(mean_sd(suc)[1])} "
            f"calls {num(mean_sd(cal)[0])}+-{num(mean_sd(cal)[1])} "
            f"effort_return {num(mean_sd(eff)[0])}+-{num(mean_sd(eff)[1])}"
        )
    for left, right in PAIRS:
        la = [a for a in ARMS if a.startswith(left + "_") or a.startswith(left)][0]
        ra = [a for a in ARMS if a.startswith(right + "_") or a.startswith(right)][0]
        for key in METRICS:
            xa = [r[la][key] for r in rows]
            xb = [r[ra][key] for r in rows]
            print(f"  paired {left}-{right} {key}: {verdict(xa, xb)}")


def alt_rows(name):
    # Same gate with tau_l = 1.0000, same traces / seeds; not adopted.
    kw = {"tau_s": TAU_S, "tau_l": TAU_L_ALT, "delta_min": DELTA_MIN, "short_only": False}
    return official_rows(name, gate_kw=kw)


def main():
    print("Synthetic Reward-DAgger progress-gate stand-in; not a VLM or LIBERO run")
    print(
        f"declared T={T} N_EPS={N_EPS} L_S={L_S} L_L={L_L} "
        f"TAU_S={num(TAU_S)} TAU_L={num(TAU_L)} DELTA_MIN={num(DELTA_MIN)} "
        f"SIG_PHI={num(SIG_PHI)} SMALL_FRAC={num(SMALL_FRAC)} "
        f"seeds={','.join(str(s) for s in SEEDS)}"
    )
    print(f"hand_calc 20 percent small-vs-clear factor = {num(SMALL_FRAC)}")
    print(f"hand_calc episode length T = {T}")
    print(f"hand_calc short window L_S = {L_S}")
    print(f"hand_calc long window L_L = {L_L}")
    print(f"hand_calc DROP_T = {DROP_T}, RISE_TO = {num(RISE_TO)}, DROP_TO = {num(DROP_TO)}")
    print(
        "declared arms: A_always labels every state; B_reward_gate two-timescale "
        "Spearman gate then takeover; C_never never fires"
    )
    print(
        "paper_authors=Ryan Li, Yigit Korkmaz, Erdem Bıyık "
        "(abs / title-page order; 以论文为准)"
    )
    print(
        "paper_title_page=Ryan Li* and Yigit Korkmaz* equal contribution "
        "(PDF footnote star Equal Contribution; no corresponding-author typography; 以论文为准)"
    )
    print("paper_version=arXiv 2610.04054 v1, submitted 2026-10-02")
    print(
        "paper_gate=(L_s, tau_s, delta_min, L_l, tau_l)=(75, -0.9, 0.05, 225, 0.0) "
        "(arXiv 2610.04054 v1; 以论文为准, not a toy output)"
    )
    print(
        "paper_rohe=P(S_tau=1)/(1+H/T) Eq. 7, and paper success / ROHE figures "
        "(arXiv 2610.04054 v1; 以论文为准, not toy outputs)"
    )
    print("Regimes and parameters were written before the first run")
    print(
        "Common random numbers: the progress traces are shared across arms "
        "at each regime and seed"
    )
    print(
        "Assumptions: synthetic progress stand-in, not a VLM; Spearman windows "
        "as in Eqs. 2-4; takeover uses the remaining steps in that episode; "
        "effort_return is a toy ratio and is not paper ROHE"
    )
    print("Gating equations and paper figures 以论文为准")
    print("Real VLA / GPU reward model / human-in-the-loop arm: 本页未运行")
    print(
        "declared uneventful: A and B may near-tie on autonomous success, "
        "with B using fewer expert calls - keep"
    )
    print(
        "declared drop_stall: B consistent better effort return than never-fire C, "
        "and more selective than A - keep"
    )
    print(
        "declared C_never on drop_stall: C loses because it makes no corrections - lose kept"
    )

    official = {name: official_rows(name) for name in REGIMES}
    for name, (_kind, decl) in REGIMES.items():
        print(f"declared expectation {name}: {decl}")
        print_regime(name, official[name])

    print(
        f"alternative same seeds TAU_L={num(TAU_L_ALT)} (not adopted)"
    )
    print(
        f"hand_calc official TAU_L={num(TAU_L)} vs alternative {num(TAU_L_ALT)}"
    )
    for name in REGIMES:
        print_regime(
            f"{name} alt_tau_l={num(TAU_L_ALT)}",
            alt_rows(name),
        )

    print("No real VLA, GPU reward model, or human-in-the-loop arm was started")
    print(
        "No winner is universal: uneventful traces may near-tie on success while "
        "the gate still uses fewer calls; the two-timescale gate matters on a "
        "drop plus stall, and a never-fire gate leaves those failures uncorrected"
    )


if __name__ == "__main__":
    main()
