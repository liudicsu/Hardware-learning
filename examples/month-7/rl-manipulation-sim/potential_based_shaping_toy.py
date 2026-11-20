#!/usr/bin/env python3
"""Potential-based reward shaping stand-in (Ng, Harada, Russell Theorem 1).

A shared tabular MDP compares an unshaped sparse reward, a potential-based
shaping term F(s,a,s') = gamma * Phi(s') - Phi(s), and a non-potential
bonus that can lock onto a distractor cycle.  Optimal policies come from
value iteration, not a noisy learner.  Synthetic; not ManiSkill, SB3, or
a real arm.

Common random numbers: transitions are deterministic and shared across
arms.  Five seeds repeat the same MDP so exact-tie cells can be printed
as identical on every seed.  Seeds do not add jitter.

Metrics per seed: success (greedy path from the start reaches the goal),
original_return (the arm's greedy policy evaluated on the unshaped R),
policy_agree_A (greedy action agrees with A in every non-goal state),
uses_cycle (the greedy path from the start visits the distractor cell).

Regimes and expectations, written before the first run:
  acyclic_corridor   no return edge, so a mild illegal forward bonus
                     cannot form a cycle: B and C may near-tie A on
                     success (keep)
  distractor_cycle   B preserves the unshaped optimum (policy agreement
                     with A; reaches the goal); C consistently prefers
                     the cycle (keep)
  constant_phi       B with a constant Phi exact-ties A (keep); C loses
                     on original-task return when the illegal cycle is
                     attractive (keep)

Named alternative, same MDPs, not adopted: Phi_alt = -2 * distance, still
potential-based.

Paper identities, theorem wording, and the introduction's shaping bugs
are 以论文为准.  ManiSkill / SB3 / a real arm: 本页未运行.
"""
from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().rounding = ROUND_HALF_UP

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9
SMALL_FRAC = 0.2000  # 20 % of the smaller-arm mean; printed as 0.2000
VI_TOL = 1e-14
VI_MAX_ITERS = 10000

# Discounted main MDPs (gamma < 1, so S \\ {s0} = S in Theorem 1).
GAMMA = 0.9000
GOAL_REWARD = 1.0000
ILLEGAL_CYCLE_BONUS = 0.2500  # non-potential bonus on every visit to the ball
ILLEGAL_FORWARD_BONUS = 0.0500  # mild illegal bonus on a forward step
CONST_PHI = 3.0000
VI_START = "S"

# Undiscounted 3-state hand_calc (gamma = 1, absorbing G, Phi(G) = 0).
HC_GAMMA = 1.0000
HC_STEP_COST = -1.0000
HC_ILLEGAL_ENTER = 1.0000

STATES_CYCLE = ("S", "J", "P", "G", "B")
STATES_CORRIDOR = ("S", "J", "P", "G")
ACTIONS = ("fwd", "back", "ball", "stay")

# Distance-to-goal potential on each layout (declared).
DIST_CYCLE = {"S": 3, "J": 2, "P": 1, "G": 0, "B": 3}
DIST_CORRIDOR = {"S": 3, "J": 2, "P": 1, "G": 0}


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


def step(state: str, action: str, states: tuple[str, ...]) -> str:
    """Deterministic next state; unavailable moves stay put."""
    if state == "G":
        return "G"
    if state == "S":
        if action == "fwd":
            return "J"
        return "S"
    if state == "J":
        if action == "fwd":
            return "P"
        if action == "back":
            return "S"
        if action == "ball" and "B" in states:
            return "B"
        return "J"
    if state == "P":
        if action == "fwd":
            return "G"
        if action == "back":
            return "J"
        return "P"
    if state == "B":
        if action == "back":
            return "J"
        return "B"
    return state


def unshaped_r(state: str, nxt: str) -> float:
    if state != "G" and nxt == "G":
        return GOAL_REWARD
    return 0.0


def phi_dist(state: str, dist: dict[str, int], scale: float = 1.0) -> float:
    return -scale * float(dist[state])


def shaping_f(state: str, nxt: str, phi_fn, gamma: float) -> float:
    return gamma * phi_fn(nxt) - phi_fn(state)


def reward(arm: str, state: str, nxt: str, dist: dict[str, int], phi_scale: float) -> float:
    r = unshaped_r(state, nxt)
    if arm == "A":
        return r
    if arm in ("B", "B_const", "B_alt"):
        if arm == "B":
            phi = lambda s: phi_dist(s, dist, 1.0)
        elif arm == "B_const":
            phi = lambda s: CONST_PHI
        else:
            phi = lambda s: phi_dist(s, dist, phi_scale)
        return r + shaping_f(state, nxt, phi, GAMMA)
    if arm == "C":
        if "B" in dist and nxt == "B":
            return r + ILLEGAL_CYCLE_BONUS
        if "B" not in dist and nxt != state and dist[nxt] < dist[state]:
            return r + ILLEGAL_FORWARD_BONUS
        return r
    raise ValueError(arm)


def value_iteration(states, dist, arm: str, phi_scale: float = 2.0):
    v = {s: 0.0 for s in states}
    for _ in range(VI_MAX_ITERS):
        nxt_v = {}
        delta = 0.0
        for s in states:
            if s == "G":
                # Absorbing goal: stay, reward is whatever R+F pays on G->G.
                r = reward(arm, "G", "G", dist, phi_scale)
                nxt_v[s] = r + GAMMA * v["G"]
            else:
                q_best = None
                for a in ACTIONS:
                    sp = step(s, a, states)
                    r = reward(arm, s, sp, dist, phi_scale)
                    q = r + GAMMA * v[sp]
                    if q_best is None or q > q_best:
                        q_best = q
                nxt_v[s] = q_best
            delta = max(delta, abs(nxt_v[s] - v[s]))
        v = nxt_v
        if delta < VI_TOL:
            break
    else:
        raise RuntimeError("value iteration did not converge")
    # Q and greedy policy (tie-break: first action in ACTIONS).
    q = {}
    pi = {}
    for s in states:
        best_a, best_q = None, None
        for a in ACTIONS:
            sp = step(s, a, states)
            r = reward(arm, s, sp, dist, phi_scale)
            qa = r + GAMMA * v[sp]
            q[(s, a)] = qa
            if best_q is None or qa > best_q + 1e-12:
                best_q, best_a = qa, a
        pi[s] = best_a
    return v, q, pi


def evaluate_policy_unshaped(states, pi, start: str) -> float:
    """Discounted return of pi on the unshaped R, from start."""
    v = {s: 0.0 for s in states}
    for _ in range(VI_MAX_ITERS):
        nxt_v = {}
        delta = 0.0
        for s in states:
            a = "stay" if s == "G" else pi[s]
            sp = step(s, a, states)
            r = unshaped_r(s, sp)
            nxt_v[s] = r + GAMMA * v[sp]
            delta = max(delta, abs(nxt_v[s] - v[s]))
        v = nxt_v
        if delta < VI_TOL:
            break
    else:
        raise RuntimeError("policy evaluation did not converge")
    return v[start]


def greedy_path(states, pi, start: str, horizon: int = 16) -> list[str]:
    path = [start]
    s = start
    for _ in range(horizon):
        if s == "G":
            break
        s = step(s, pi[s], states)
        path.append(s)
        if len(path) >= 2 and path[-1] == path[-2]:
            break
    return path


def run_arm(states, dist, arm: str, phi_scale: float = 2.0) -> dict:
    v, q, pi = value_iteration(states, dist, arm, phi_scale)
    path = greedy_path(states, pi, VI_START)
    success = 1.0 if "G" in path else 0.0
    uses_cycle = 1.0 if "B" in path else 0.0
    original_return = evaluate_policy_unshaped(states, pi, VI_START)
    return {
        "success": success,
        "original_return": original_return,
        "uses_cycle": uses_cycle,
        "path": path,
        "pi": pi,
        "v": v,
        "q": q,
    }


def policy_agree(pi_a, pi_b, states) -> float:
    for s in states:
        if s == "G":
            continue
        if pi_a[s] != pi_b[s]:
            return 0.0
    return 1.0


def fmt_policy(pi, states) -> str:
    return " ".join(f"{s}:{pi[s]}" for s in states if s != "G")


def hand_calc_block() -> None:
    """Undiscounted 3-state chain and a 2-cycle; potential cycle sum is 0."""
    # States 0, 1, G with Phi(G)=0, Phi(1)=-1, Phi(0)=-2 (minus distance).
    phi = {"0": -2.0, "1": -1.0, "G": 0.0}
    def f(s, sp):
        return HC_GAMMA * phi[sp] - phi[s]

    path = [("0", "1"), ("1", "G")]
    path_terms = [f(s, sp) for s, sp in path]
    cycle = [("1", "0"), ("0", "1")]
    cycle_terms = [f(s, sp) for s, sp in cycle]
    illegal_cycle = [HC_ILLEGAL_ENTER if sp == "1" and s != "1" else 0.0 for s, sp in cycle]

    print(
        "hand_calc 3-state chain states=0,1,G gamma_undiscounted="
        + num(HC_GAMMA)
        + " Phi(0)="
        + num(phi["0"])
        + " Phi(1)="
        + num(phi["1"])
        + " Phi(G)="
        + num(phi["G"])
        + " (Phi(G)=0)"
    )
    print(
        "hand_calc potential F(s,s') = gamma*Phi(s')-Phi(s) with gamma="
        + num(HC_GAMMA)
        + " reduces to Phi(s')-Phi(s)"
    )
    print(
        "hand_calc path 0->1->G F terms = "
        + ", ".join(num(t) for t in path_terms)
        + " path sum = "
        + num(sum(path_terms))
    )
    print(
        "hand_calc potential 2-cycle 1->0->1 F terms = "
        + ", ".join(num(t) for t in cycle_terms)
        + " cycle sum = "
        + num(sum(cycle_terms))
    )
    print(
        "hand_calc illegal bonus "
        + num(HC_ILLEGAL_ENTER)
        + " on entering 1; same 2-cycle terms = "
        + ", ".join(num(t) for t in illegal_cycle)
        + " cycle sum = "
        + num(sum(illegal_cycle))
        + " (not 0)"
    )

    # Corollary 2 style check: step cost -1 until G, one forward action,
    # V_M(0)=-2, V_M(1)=-1, V_M(G)=0; V_M'(s)=V_M(s)-Phi(s).
    v_m = {"0": -2.0, "1": -1.0, "G": 0.0}
    print(
        "hand_calc corollary-2 setup step_cost="
        + num(HC_STEP_COST)
        + " V_M(0)="
        + num(v_m["0"])
        + " V_M(1)="
        + num(v_m["1"])
        + " V_M(G)="
        + num(v_m["G"])
    )
    for s in ("0", "1", "G"):
        v_mp = v_m[s] - phi[s]
        print(
            "hand_calc corollary-2 V_M'("
            + s
            + ")=V_M("
            + s
            + ")-Phi("
            + s
            + ") = "
            + num(v_m[s])
            + "-"
            + "("
            + num(phi[s])
            + ") = "
            + num(v_mp)
        )


def q_shift_err(q_b, q_a, phi_fn, states) -> float:
    err = 0.0
    for s in states:
        for a in ACTIONS:
            err = max(err, abs(q_b[(s, a)] - (q_a[(s, a)] - phi_fn(s))))
    return err


def col(rows, metric):
    return [row[metric] for row in rows]


def print_regime(name: str, expl: str, states, dist, arms: tuple[str, ...], const_phi: bool) -> dict:
    print(f"declared expectation {name}: {expl}")
    print(f"regime {name}  (mean+-sd over seeds; deterministic MDP)")
    rows = {arm: [] for arm in arms}
    recs0 = {}
    for seed in SEEDS:
        _ = seed
        for arm in arms:
            rec = run_arm(states, dist, arm)
            rec["policy_agree_A"] = 0.0  # filled after A is known
            rows[arm].append(rec)
        # fill agreement vs this seed's A
        pi_a = rows["A"][-1]["pi"]
        for arm in arms:
            rows[arm][-1]["policy_agree_A"] = policy_agree(pi_a, rows[arm][-1]["pi"], states)
        if seed == 0:
            recs0 = {arm: rows[arm][0] for arm in arms}

    print(f"  seed 0 (all {len(SEEDS)} seeds identical):")
    for arm in arms:
        rec = recs0[arm]
        print(
            f"    {arm}: success={num(rec['success'])} original_return={num(rec['original_return'])} "
            f"policy_agree_A={num(rec['policy_agree_A'])} uses_cycle={num(rec['uses_cycle'])} "
            f"path={'->'.join(rec['path'])} policy={fmt_policy(rec['pi'], states)}"
        )

    metrics = ("success", "original_return", "policy_agree_A", "uses_cycle")
    for arm in arms:
        for metric in metrics:
            xs = col(rows[arm], metric)
            print(f"  {arm} {metric} {fmt_pair(*mean_sd(xs))}")
    for metric in metrics:
        if "B" in arms:
            print(f"  paired B-A {metric}: {verdict(col(rows['B'], metric), col(rows['A'], metric))}")
        if "B_const" in arms:
            print(
                f"  paired B_const-A {metric}: "
                + verdict(col(rows["B_const"], metric), col(rows["A"], metric))
            )
        if "C" in arms:
            print(f"  paired C-A {metric}: {verdict(col(rows['C'], metric), col(rows['A'], metric))}")
            if "B" in arms:
                print(f"  paired C-B {metric}: {verdict(col(rows['C'], metric), col(rows['B'], metric))}")

    # Potential-based Q-shift check on seed 0 (toy identity, printed).
    if "B" in arms:
        err = q_shift_err(
            recs0["B"]["q"], recs0["A"]["q"], lambda s: phi_dist(s, dist, 1.0), states
        )
        print(f"  toy Q-shift check max|Q_B(s,a)-(Q_A(s,a)-Phi(s))| = {num(err)}")
    if "B_const" in arms:
        err = q_shift_err(
            recs0["B_const"]["q"], recs0["A"]["q"], lambda s: CONST_PHI, states
        )
        print(f"  toy Q-shift check max|Q_Bconst(s,a)-(Q_A(s,a)-CONST_PHI)| = {num(err)}")
    return rows


def main():
    print("Synthetic potential-based shaping stand-in; not ManiSkill, SB3, or a real arm")
    print(
        f"declared GAMMA={num(GAMMA)} GOAL_REWARD={num(GOAL_REWARD)} "
        f"ILLEGAL_CYCLE_BONUS={num(ILLEGAL_CYCLE_BONUS)} "
        f"ILLEGAL_FORWARD_BONUS={num(ILLEGAL_FORWARD_BONUS)} "
        f"CONST_PHI={num(CONST_PHI)} VI_START={VI_START} "
        f"VI_TOL={VI_TOL} VI_MAX_ITERS={VI_MAX_ITERS} "
        f"SMALL_FRAC={num(SMALL_FRAC)} seeds={','.join(str(s) for s in SEEDS)}"
    )
    print(
        "declared Phi_B(s) = -distance_to_goal; "
        + "cycle distances "
        + ", ".join(f"{s}={DIST_CYCLE[s]}" for s in STATES_CYCLE)
        + "; corridor distances "
        + ", ".join(f"{s}={DIST_CORRIDOR[s]}" for s in STATES_CORRIDOR)
    )
    print("declared F(s,a,s') = GAMMA*Phi(s')-Phi(s) on arms B / B_const / B_alt")
    print("declared arm A: unshaped sparse R (GOAL_REWARD on entering G, else 0)")
    print("declared arm B: potential-based F with Phi_B = -distance")
    print("declared arm B_const: potential-based F with constant Phi = CONST_PHI")
    print(
        "declared arm C: non-potential bonus ILLEGAL_CYCLE_BONUS on every visit "
        "to B (cycle layout), or ILLEGAL_FORWARD_BONUS on a forward step (corridor)"
    )
    print("hand_calc 20 percent small-vs-clear factor = " + num(SMALL_FRAC))
    print(
        "hand_calc unshaped return from S along S->J->P->G = GAMMA^2 * GOAL_REWARD = "
        + num(GAMMA)
        + "^2 * "
        + num(GOAL_REWARD)
        + " = "
        + num(GAMMA ** 2 * GOAL_REWARD)
    )
    hand_calc_block()
    print("Regimes and parameters were written before the first run")
    print("Common random numbers: deterministic shared MDP; seeds repeat the same tables")
    print("Assumptions: deterministic transitions; tabular value iteration; greedy tie-break is the first action in (fwd, back, ball, stay)")
    print("Paper Theorem 1 / Corollary 2 and the introduction bugs 以论文为准")
    print("ManiSkill / SB3 / a real arm: 本页未运行")

    corridor_expl = (
        "short acyclic corridor; mild illegal forward bonus cannot form a cycle: "
        "B and C may near-tie A on success - keep"
    )
    cycle_expl = (
        "distractor cycle at B: B preserves the unshaped optimum (policy agreement "
        "with A; reaches the goal); C consistently prefers the cycle - keep"
    )
    const_expl = (
        "constant Phi exact-ties A; C loses on original-task return when the "
        "illegal cycle is attractive - keep"
    )
    print(f"declared acyclic_corridor: {corridor_expl}")
    print(f"declared distractor_cycle: {cycle_expl}")
    print(f"declared constant_phi: {const_expl}")

    print_regime(
        "acyclic_corridor",
        corridor_expl,
        STATES_CORRIDOR,
        DIST_CORRIDOR,
        ("A", "B", "C"),
        const_phi=False,
    )
    print_regime(
        "distractor_cycle",
        cycle_expl,
        STATES_CYCLE,
        DIST_CYCLE,
        ("A", "B", "C"),
        const_phi=False,
    )
    print_regime(
        "constant_phi",
        const_expl,
        STATES_CYCLE,
        DIST_CYCLE,
        ("A", "B_const", "C"),
        const_phi=True,
    )

    print("named alternative B_alt (Phi = -2 * distance, still potential-based) - not adopted")
    for name, states, dist in (
        ("acyclic_corridor", STATES_CORRIDOR, DIST_CORRIDOR),
        ("distractor_cycle", STATES_CYCLE, DIST_CYCLE),
    ):
        alt = []
        base = []
        for seed in SEEDS:
            _ = seed
            alt.append(run_arm(states, dist, "B_alt", phi_scale=2.0))
            base.append(run_arm(states, dist, "B", phi_scale=1.0))
            alt[-1]["policy_agree_B"] = policy_agree(base[-1]["pi"], alt[-1]["pi"], states)
            base[-1]["policy_agree_B"] = 1.0
        print(f"  alt {name}: path={('->'.join(alt[0]['path']))} policy={fmt_policy(alt[0]['pi'], states)}")
        print(
            f"    paired alt-B success: {verdict([r['success'] for r in alt], [r['success'] for r in base])}"
        )
        print(
            f"    paired alt-B original_return: "
            + verdict([r["original_return"] for r in alt], [r["original_return"] for r in base])
        )
        print(
            f"    paired alt-B policy_agree_B: "
            + verdict([r["policy_agree_B"] for r in alt], [r["policy_agree_B"] for r in base])
        )
    print("No winner declared")


if __name__ == "__main__":
    main()
