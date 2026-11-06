#!/usr/bin/env python3
"""OneDP-style REGRESSION SURROGATE, not KL-along-chain/score distillation.
Synthetic analytic eight-field-call teacher solves a nonlinear inverse plant.
Both students see the SAME 64 noisy teacher demos and copy the SAME init;
240 vs 2 updates is a deliberately unequal underfit control, not convergence proof.
Every scored state/start is held out; fit() never receives eval states/labels.
NFE counts actual field/forward calls, not FLOPs, Hz or wall-clock speed.
Original Consistency Policy and GPU OneDP/Franka are not run: 本页未运行.
"""
from random import Random
from statistics import mean, pstdev

SEEDS = (11, 23, 37, 53, 71)
N_STEPS = 8
N_DEMOS = N_EVAL = 64
FULL_UPDATES, UNDER_UPDATES = 240, 2
LR, DEMO_SIGMA, TOLERANCE = .25, .008, .004
EVAL_STARTS = tuple(-1.2 + 2.4*(j+.9)/N_EVAL for j in range(N_EVAL))


def displacement(action):
    """Independent nonlinear one-step plant: x_next=-error+D(action), goal=0."""
    return action + .22*action**3


def field(error, action):
    return error - displacement(action)


def teacher(error):
    action, nfe = 0., 0
    for _ in range(N_STEPS):
        action += .5*field(error, action)
        nfe += 1
    return action, nfe


def features(error):
    """Fixed Legendre basis on normalized error; not evaluated teacher labels."""
    x = error/1.2
    return (1., x, (5*x**3-3*x)/2, (63*x**5-70*x**3+15*x)/8)


def student(weights, error):
    return sum(w*x for w,x in zip(weights, features(error))), 1


def demonstrations(seed):
    rng = Random(seed)
    # Training fractional bins .25..75 never overlap held-out fractional bin .9.
    starts = tuple(-1.2 + 2.4*(j+.25+.5*rng.random())/N_DEMOS for j in range(N_DEMOS))
    demos = tuple((s, teacher(s)[0]+rng.gauss(0,DEMO_SIGMA)) for s in starts)
    initial = tuple(rng.gauss(0,.02) for _ in range(4))
    return demos, initial


def fit(demos, initial, updates):
    """Only training pairs and initial weights; no teacher query or held-out input."""
    weights = list(initial)
    design = tuple((features(state), label) for state,label in demos)
    for _ in range(updates):
        gradient = [0.]*len(weights)
        for basis, label in design:
            residual = sum(w*x for w,x in zip(weights,basis))-label
            for j,x in enumerate(basis):
                gradient[j] += 2*residual*x/len(design)
        weights = [w-LR*g for w,g in zip(weights,gradient)]
    return tuple(weights)


def evaluate(policy, starts, references, training_states):
    if set(starts) & set(training_states):
        raise ValueError("training/evaluation state overlap")
    mse, successes, calls = 0., 0, 0
    for state, reference in zip(starts,references):
        action, nfe = policy(state)
        mse += (action-reference)**2
        successes += int(abs(-state+displacement(action)) <= TOLERANCE)
        calls += nfe
    return mse/len(starts), calls/len(starts), successes/len(starts)


def run(seed):
    demos, initial = demonstrations(seed)
    full, under = fit(demos, initial,FULL_UPDATES), fit(demos, initial,UNDER_UPDATES)
    # References are SCORER-ONLY; no student inference/fitting receives them.
    references = tuple(teacher(s)[0] for s in EVAL_STARTS)
    states = tuple(s for s,_ in demos)
    policies = (("teacher_N8",teacher,0),
                ("student_1",lambda s: student(full,s),FULL_UPDATES),
                ("underfit_1",lambda s: student(under,s),UNDER_UPDATES))
    return [(name,updates,evaluate(policy,EVAL_STARTS,references,states)) for name,policy,updates in policies]


def main():
    print("OneDP-style regression surrogate ONLY; KL-along-chain is reading, not implemented")
    print("shared demos=64 held-out eval starts=64 overlap=0; N-step teacher=8 actual field calls")
    print("student updates=240 underfit updates=2 (unequal on purpose); same data/features/init")
    print("demo_sigma=0.008 success_abs_plant_error<=0.004; NFE is calls, not Hz or wall time")
    print("seed arm fit_updates action_MSE NFE_per_query success")
    all_rows = {name: [] for name in ("teacher_N8","student_1","underfit_1")}
    for seed in SEEDS:
        for name,updates,metrics in run(seed):
            all_rows[name].append(metrics)
            mse,nfe,success=metrics
            print(f"{seed} {name} {updates} {mse:.8f} {nfe:.1f} {success:.6f}")
    print("five-seed spread: arm metric mean population_sd min max")
    for name,rows in all_rows.items():
        for j,metric in enumerate(("action_MSE","NFE","success")):
            values=[row[j] for row in rows]
            print(f"{name} {metric} {mean(values):.8f} {pstdev(values):.8f} {min(values):.8f} {max(values):.8f}")
    print("Teacher self-reference MSE=0 by definition; success independently uses nonlinear plant")
    print("Scorer reference queries excluded from policy NFE; different call types are not equal FLOPs")
    print("No diffusion distribution/score/consistency training; GPU and robot: 本页未运行; paper 以论文为准")


if __name__ == "__main__":
    main()
