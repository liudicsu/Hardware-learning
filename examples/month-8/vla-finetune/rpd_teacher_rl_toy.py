#!/usr/bin/env python3
"""RPD-style tabular Bernoulli/REINFORCE + action-mean teacher-MSE surrogate.
NOT PPO, VLA/HTTP/ManiSkill, Cal-ConRFT offline Q+BC, or HIL-SERL.
Teacher is deliberately SUBOPTIMAL: correct probability .9 except bottleneck .6.
Each arm starts from identical logits and consumes the same keyed random tape,
8 episodes x12 ticks per update, 80 updates. Goal stays absorbing to horizon;
those ticks are charged and active-decision counts are reported separately.
BC-only is online teacher-MSE imitation, NOT categorical maximum-likelihood BC.
Gamma=1; full-episode terminal return REINFORCE, no critic/clipping/replay.
Evaluation is separate and cannot select checkpoints or affect updates.
"""
from math import exp
from random import Random
from statistics import mean, pstdev

SEEDS = (11,23,37,53,71)
CORRECT = (1,0,1,1,0)
GOAL, HORIZON, BATCH, UPDATES = 5,12,8,80
CHECKPOINTS = (8,80)
SLIP, LR = .05,.25
# (reward-gradient weight, teacher-MSE weight), fixed before evaluation.
WEIGHTS = {"BC_only":(0.,1.), "RL_scratch":(1.,0.), "RL_teacher_MSE":(1.,.5)}


def sigmoid(x):
    return 1/(1+exp(-x))


def teacher_mean(state):
    if state == GOAL:
        return .5  # Charged dummy query while absorbing, ignored by all gradients.
    good = .6 if state == 2 else .9
    return good if CORRECT[state] else 1-good


def transition(state, action, slip_uniform):
    if state == GOAL:
        return GOAL
    if action != CORRECT[state]:
        return 0
    return state if slip_uniform < SLIP else state+1


def tape(seed, episodes):
    """One immutable common-random-numbers tape; independent of arm/trajectory."""
    rng = Random(seed)
    return tuple((int(rng.random()>=.5),
                  tuple((rng.random(),rng.random(),rng.random()) for _ in range(HORIZON)))
                 for _ in range(episodes))


def episode(probabilities, data):
    state, steps = data[0], []
    for action_u,slip_u,teacher_u in data[1]:
        p = .5 if state==GOAL else probabilities[state]
        label = int(teacher_u < teacher_mean(state))
        action = int(action_u < p)
        if state != GOAL:
            steps.append((state,action,p,label))
        state = transition(state,action,slip_u)
    return float(state==GOAL), tuple(steps)


def mse_logit_gradient(p, teacher_action):
    return 2*(p-teacher_action)*p*(1-p)


def update(logits, episodes, arm):
    reward_weight,mse_weight = WEIGHTS[arm]
    probabilities = tuple(sigmoid(x) for x in logits)
    gradient,active = [0.]*GOAL,0
    for data in episodes:
        reward,records = episode(probabilities,data)
        active += len(records)
        for state,action,p,label in records:
            gradient[state] += reward_weight*reward*(action-p)-mse_weight*mse_logit_gradient(p,label)
    # Objective is per-episode mean SUM of visited-state terms, not per-state normalization.
    return tuple(x+LR*g/len(episodes) for x,g in zip(logits,gradient)),active


def train(seed, arm, training_tape):
    rng=Random(seed)
    logits=tuple(rng.gauss(0,.05) for _ in range(GOAL))
    checkpoints,active = {},0
    for step in range(1,UPDATES+1):
        batch=training_tape[(step-1)*BATCH:step*BATCH]
        logits,visits=update(logits,batch,arm)
        active += visits
        if step in CHECKPOINTS:
            checkpoints[step]=(tuple(sigmoid(x) for x in logits), step*BATCH*HORIZON, step, active)
    return checkpoints


def exact_success(probabilities):
    """Independent finite-horizon DP baseline, not used by train/update."""
    value=[0.]*GOAL+[1.]
    for _ in range(HORIZON):
        previous=value
        value=[0.]*(GOAL+1);value[GOAL]=1.
        for state in range(GOAL):
            good=probabilities[state] if CORRECT[state] else 1-probabilities[state]
            value[state]=good*((1-SLIP)*previous[state+1]+SLIP*previous[state])+(1-good)*previous[0]
    return (value[0]+value[1])/2


def evaluate(probabilities, evaluation_tape):
    successes=sum(episode(probabilities,data)[0] for data in evaluation_tape)
    mismatch=mean((p-teacher_mean(s))**2 for s,p in enumerate(probabilities))
    return successes/len(evaluation_tape), mismatch


def main():
    teacher=tuple(teacher_mean(s) for s in range(GOAL))
    optimal=tuple(float(a) for a in CORRECT)
    print("RPD-style surrogate: discrete chain, deliberately suboptimal stochastic teacher")
    print(f"teacher_exact_success={exact_success(teacher):.6f} optimal_exact_success={exact_success(optimal):.6f}")
    print("weights BC_only=(RL0,MSE1) RL_scratch=(RL1,MSE0) RL_teacher_MSE=(RL1,MSE0.5)")
    print("paired tape:8 episodes x12 ticks/update; checkpoints8/80; gamma1 lr0.25")
    print("equal charged env_steps/updates; goal absorbing ticks included; active decisions reported")
    print("seed updates arm env_steps teacher_queries active_decisions success teacher_mean_MSE")
    aggregate={(step,arm):[] for step in CHECKPOINTS for arm in WEIGHTS}
    for seed in SEEDS:
        training=tape(1000+seed,UPDATES*BATCH)
        evaluation=tape(100000+seed,256)
        trained={arm:train(seed,arm,training) for arm in WEIGHTS}
        for step in CHECKPOINTS:
            for arm in WEIGHTS:
                probabilities,env_steps,updates,active=trained[arm][step]
                metrics=evaluate(probabilities,evaluation)
                aggregate[(step,arm)].append(metrics)
                success,mse=metrics
                print(f"{seed} {updates} {arm} {env_steps} {env_steps} {active} {success:.6f} {mse:.6f}")
    print("five-seed mean+-population_sd and range: updates arm metric mean sd min max")
    for (step,arm),rows in aggregate.items():
        for j,metric in enumerate(("success","teacher_mean_MSE")):
            values=[row[j] for row in rows]
            print(f"{step} {arm} {metric} {mean(values):.6f} {pstdev(values):.6f} {min(values):.6f} {max(values):.6f}")
    print("BC consumes equal online ticks/updates but ignores rewards; MSE imitation is not Bernoulli MLE")
    print("No presumed winner; teacher bias can hinder improvement; no PPO or VLA trained")
    print("Not Cal-ConRFT or HIL-SERL; real robot/GPU/ManiSkill: 本页未运行; paper 以论文为准")


if __name__ == "__main__":
    main()
