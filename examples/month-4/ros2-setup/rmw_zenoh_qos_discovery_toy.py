#!/usr/bin/env python3
"""Synthetic RMW discovery and QoS stand-in.

Stdlib only. Discrete event stand-in: not Fast DDS, not a real Zenoh session,
not a QoS compatibility matrix copied from an unread DDS specification, and
not a real rmw_* or rmw_zenohd process.

A shared publication timeline, a shared payload sequence and shared network
draws are generated once per (regime, seed) and then read by every arm
(common random numbers).

Arms:
  A_dds_like -- multicast discovery works without a router; in this stand-in
    a reliability mismatch (reliable publisher, best-effort subscriber)
    yields publishes-but-nothing-receives.
  B_zenoh_like -- discovery requires a router; QoS pairings that would be
    incompatible under A still deliver in this stand-in. The Kilted vendors
    wording "essentially no incompatible QoS" is 以文档为准 and is not a
    measured toy result.
  C_zenoh_no_router -- the same Zenoh-like stand-in with the router not
    started; multicast discovery is not available in this session config,
    so nodes do not discover each other.

Regimes and parameters were written before the first run.

Labels: tie = identical on every seed; numerically zero = |paired mean| and sd
both < 1e-9; |m| <= sd = near-tie; |m| > sd = consistent gap (small if |m| < 20 %
of the smaller arm mean, else clear), with a sign count. ROUND_HALF_UP output.

Real ros2 run / rmw_zenohd / multi-machine multicast: 本页未运行.
"""
import math
import random
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
SMALL_FRAC = 0.2000  # 20 % of the smaller-arm mean; printed as 0.2000

# Declared stand-in parameters (not a vendor default, not a DDS spec table).
N_PUB = 40
P_DROP = 0.0500  # shared Bernoulli drop after a successful discover+deliver path
RELIABLE = "reliable"
BEST_EFFORT = "best_effort"

ARMS = ("A_dds_like", "B_zenoh_like", "C_zenoh_no_router")
METRICS = ("received", "delivery_rate")
PAIRS = (("B", "A"), ("C", "B"), ("C", "A"))

# name: (pub QoS, sub QoS, router_for_B, declared expectation); written before the first run
REGIMES = {
    "compatible_qos": (
        RELIABLE,
        RELIABLE,
        True,
        "A and B may near-tie on delivery (including an exact tie if the shared network draws apply equally after discovery) - keep",
    ),
    "incompatible_qos": (
        RELIABLE,
        BEST_EFFORT,
        True,
        "B consistent delivery, A loses (classic reliable-vs-best-effort mismatch under the DDS-like arm) - keep",
    ),
    "no_router": (
        RELIABLE,
        RELIABLE,
        True,
        "C loses discovery (Zenoh-like session has no multicast fallback; the router is not started for C) - keep",
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


def qos_compatible_dds(pub_qos, sub_qos):
    """Stand-in rule, not a DDS specification table.

    This toy treats a reliable publisher with a best-effort subscriber as
    incompatible under the DDS-like arm (the classic mismatch that can yield
    publishes-but-nothing-receives). Other pairings in this toy are treated
    as compatible.
    """
    return not (pub_qos == RELIABLE and sub_qos == BEST_EFFORT)


def rng_for(*parts):
    h = 20261119
    for p in parts:
        if isinstance(p, str):
            for ch in p:
                h = (h * 131 + ord(ch)) & 0xFFFFFFFFFFFFFFFF
        else:
            h = (h * 131 + int(p)) & 0xFFFFFFFFFFFFFFFF
    return random.Random(h)


def shared_draws(seed, p_drop=P_DROP, tag="official"):
    """Common random numbers: payload and drop sequence shared across arms."""
    rng = rng_for("rmw-draws", tag, seed, int(round(p_drop * 1e6)))
    payloads = [rng.randrange(1, 10 ** 6) for _ in range(N_PUB)]
    drops = [rng.random() < p_drop for _ in range(N_PUB)]
    return payloads, drops


def evaluate(arm, pub_qos, sub_qos, router_for_b, draws):
    payloads, drops = draws
    if arm == "A_dds_like":
        discovered = True  # multicast on the same LAN, no router required
        qos_ok = qos_compatible_dds(pub_qos, sub_qos)
    elif arm == "B_zenoh_like":
        discovered = bool(router_for_b)
        qos_ok = True  # stand-in: pairings that fail under A still deliver
    elif arm == "C_zenoh_no_router":
        discovered = False  # router not started; no multicast in this session
        qos_ok = True
    else:
        raise ValueError(arm)
    received = 0
    for payload, dropped in zip(payloads, drops):
        del payload  # shared payload is part of the CRN record, not a filter
        if discovered and qos_ok and not dropped:
            received += 1
    return {
        "discovered": 1.0 if discovered else 0.0,
        "received": float(received),
        "delivery_rate": received / float(N_PUB),
        "published": float(N_PUB),
    }


def run_regime(name, seed, p_drop=P_DROP, pub_qos=None, sub_qos=None, router_for_b=None):
    pub, sub, router, _decl = REGIMES[name]
    if pub_qos is None:
        pub_qos = pub
    if sub_qos is None:
        sub_qos = sub
    if router_for_b is None:
        router_for_b = router
    draws = shared_draws(seed, p_drop, tag=name)
    return {arm: evaluate(arm, pub_qos, sub_qos, router_for_b, draws) for arm in ARMS}


def print_regime(title, rows):
    print(f"regime {title}  (mean+-sd over seeds)")
    for arm in ARMS:
        rec = [r[arm]["received"] for r in rows]
        rate = [r[arm]["delivery_rate"] for r in rows]
        disc = [r[arm]["discovered"] for r in rows]
        print(
            f"  {arm} received {num(mean_sd(rec)[0])}+-{num(mean_sd(rec)[1])} "
            f"delivery_rate {num(mean_sd(rate)[0])}+-{num(mean_sd(rate)[1])} "
            f"discovered {num(mean_sd(disc)[0])}+-{num(mean_sd(disc)[1])}"
        )
    for left, right in PAIRS:
        la = [a for a in ARMS if a.startswith(left)][0]
        ra = [a for a in ARMS if a.startswith(right)][0]
        for key in METRICS:
            xa = [r[la][key] for r in rows]
            xb = [r[ra][key] for r in rows]
            print(f"  paired {left}-{right} {key}: {verdict(xa, xb)}")


def official_rows(name, p_drop=P_DROP, **kwargs):
    return [run_regime(name, seed, p_drop=p_drop, **kwargs) for seed in SEEDS]


def main():
    print("Synthetic RMW discovery and QoS stand-in; not Fast DDS, not a real Zenoh session")
    print(
        f"declared N_PUB={N_PUB} P_DROP={num(P_DROP)} SMALL_FRAC={num(SMALL_FRAC)} "
        f"seeds={','.join(str(s) for s in SEEDS)}"
    )
    print("declared arms: A_dds_like multicast no-router; B_zenoh_like router required; C_zenoh_no_router no router and no multicast")
    print("declared stand-in QoS rule: reliable publisher + best-effort subscriber is incompatible under A only")
    print("hand_calc full-delivery count if discovered and delivered with P_DROP=0 = 40.0000")
    print(f"hand_calc expected received if discovered and P_DROP={num(P_DROP)} = {num(N_PUB * (1.0 - P_DROP))}")
    print(f"hand_calc 20 percent small-vs-clear factor = {num(SMALL_FRAC)}")
    print("Regimes and parameters were written before the first run")
    print("Common random numbers: the payload and drop sequence is shared across arms at each regime and seed")
    print("Assumptions: discrete event stand-in, not Fast DDS, not a real Zenoh session, not a QoS matrix from an unread DDS spec")
    print("Documentation claims (router, default Fast DDS, Kilted packaging, no incompatible QoS wording) 以文档为准")
    print("Real ros2 run / rmw_zenohd / multi-machine multicast: 本页未运行")
    print("declared compatible_qos: A and B may near-tie on delivery - keep")
    print("declared incompatible_qos: B consistent delivery, A loses - keep")
    print("declared no_router: C loses discovery - keep")

    official = {name: official_rows(name) for name in REGIMES}
    for name, (_pub, _sub, _router, decl) in REGIMES.items():
        print(f"declared expectation {name}: {decl}")
        print_regime(name, official[name])

    # Alternatives on the same seeds; not adopted.
    print("alternative same seeds P_DROP=0.2000 (not adopted)")
    print(f"hand_calc expected received if discovered and P_DROP=0.2000 = {num(N_PUB * (1.0 - 0.2000))}")
    for name in REGIMES:
        print_regime(f"{name} alt_p_drop=0.2000", official_rows(name, p_drop=0.2000))

    print("alternative same seeds incompatible_qos with publisher best_effort and subscriber reliable (not adopted)")
    print_regime(
        "incompatible_qos alt_qos=best_effort_pub_reliable_sub",
        official_rows("incompatible_qos", pub_qos=BEST_EFFORT, sub_qos=RELIABLE),
    )

    print("No real rmw_* process was started")
    print("No winner is universal: compatible same-LAN delivery can tie; the stand-in difference is the mismatch and the router")


if __name__ == "__main__":
    main()
