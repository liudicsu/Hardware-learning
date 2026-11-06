#!/usr/bin/env python3
"""Offline discrete lock-chain; BC vs CQL+BC vs Cal-QL+BC (stdlib).
No consistency head, VLA backbone, online phase or HIL-SERL reproduction.
Tabular actor, restricted shared-action-feature linear critic (misspecified).
CQL uses a temperature-logsumexp conservative penalty; Cal-QL masks its
push-down via max(Q, V_MC) INSIDE that penalty, not a post-hoc Q clamp.
V_MC is behavior return-to-go from the SAME demos, never an eval oracle.
Equal full-batch actor updates; BC has no critic (Q scale NA), not equal FLOPs.
All settings synthetic; paper numbers 以论文为准; GPU/robot 本页未运行.
"""
import math
import random
import statistics
import sys

FEATURES = (1., 1.2, 1.4)  # Deliberately restricted critic: Q(s,a)=w_s*FEATURES[a].
SEEDS = (1071, 1072, 1073, 1074, 1075)
STATES, ACTIONS, DEMOS, UPDATES, EVAL_N = 4, 3, 48, 1000, 1000
GAMMA, ALPHA, TEMP, LR_Q, LR_PI = .95, 1., .1, .03, .06
BC_WEIGHT, Q_WEIGHT = 1., 2.
ARMS = ("BC_only", "CQL_BC", "CalQL_BC")


def softmax(xs):
    m = max(xs)
    es = [math.exp(x-m) for x in xs]
    return [x/sum(es) for x in es]


def transition(s, a, noise):
    # 0: advance with 90% probability; 1: wrong key, fail; 2: abort for .2.
    if a == 1:
        return 0., STATES, False
    if a == 2:
        return .2, STATES, False
    if noise >= .9:
        return 0., STATES, False
    return (1. if s == STATES-1 else 0.), s+1, s == STATES-1


def dataset(seed):
    rng = random.Random(seed)
    by_state = [[] for _ in range(STATES)]
    for _ in range(DEMOS):
        episode, s = [], 0
        while s < STATES:
            u = rng.random()
            a = 0 if u < .75 else (1 if u < .85 else 2)
            r, ns, _ = transition(s,a,rng.random())
            episode.append((s,a,r,ns)); s = ns
        ret = 0.
        for s,a,r,ns in reversed(episode):
            ret = r+GAMMA*ret
            by_state[s].append((a,r,ns,ret))
    assert all(by_state), "declared seeds must cover all four states"
    return tuple(tuple(rows) for rows in by_state)


def train(arm, data, tabular=False):
    weights, features = [0.]*STATES, FEATURES
    q = [[0.]*ACTIONS for _ in range(STATES)]
    logits = [[0.]*ACTIONS for _ in range(STATES)]
    refs = [statistics.fmean(row[3] for row in rows) for rows in data]
    beta = [[sum(row[0]==a for row in rows)/len(rows) for a in range(ACTIONS)] for rows in data]
    masked, proposals = 0, 0
    for _ in range(UPDATES):
        pi = [softmax(z) for z in logits]
        grads = [[0.]*ACTIONS for _ in range(STATES)]
        for s,rows in enumerate(data):
            if arm != "BC_only":
                scores = [max(x,refs[s]) if arm=="CalQL_BC" else x for x in q[s]]
                proposal = softmax([x/TEMP for x in scores])
                td = [0.]*ACTIONS
                for a,r,ns,_ in rows:
                    target = r if ns==STATES else r+GAMMA*sum(p*x for p,x in zip(pi[ns],q[ns]))
                    td[a] += (q[s][a]-target)/len(rows)
                for a in range(ACTIONS):
                    active = arm!="CalQL_BC" or q[s][a] > refs[s]
                    masked += not active; proposals += 1
                    grad = td[a]+ALPHA*(proposal[a]*active-beta[s][a])
                    grads[s][a] = grad
            # CE gradient plus gradient of -E_pi Q; critic held fixed here.
            meanq = sum(p*x for p,x in zip(pi[s],q[s]))
            eta = 0. if arm=="BC_only" else Q_WEIGHT
            for a in range(ACTIONS):
                grad = BC_WEIGHT*(pi[s][a]-beta[s][a])-eta*pi[s][a]*(q[s][a]-meanq)
                logits[s][a] -= LR_PI*grad
        if arm != "BC_only":
            if tabular:
                q = [[x-LR_Q*g for x,g in zip(qs,gs)] for qs,gs in zip(q,grads)]
            else:
                for s in range(STATES):
                    weights[s] -= LR_Q*sum(g*f for g,f in zip(grads[s],features))
                q = [[w*f for f in features] for w in weights]
    pi = [softmax(z) for z in logits]
    # Uniform weighting over the four covered dataset states (not start return).
    # Same dataset-state weighting for learned policy Q and MC behavior V.
    qscale = statistics.fmean(sum(p*x for p,x in zip(ps,qs)) for ps,qs in zip(pi,q))
    reference = statistics.fmean(refs)
    gaps = [sum(p*x for p,x in zip(ps,qs))-ref for ps,qs,ref in zip(pi,q,refs)]
    return pi,qscale,reference,min(gaps),masked/max(proposals,1)


def evaluate(pi, draws):
    successes, returns, lengths = 0, [], []
    for trajectory in draws:
        s, ret = 0, 0.
        for t,(u,noise) in enumerate(trajectory):
            cdf = 0.
            for a,p in enumerate(pi[s]):
                cdf += p
                if u < cdf:
                    break
            r,s,success = transition(s,a,noise)
            ret += GAMMA**t*r
            if s == STATES:
                successes += success; lengths.append(t+1); break
        returns.append(ret)
    return successes/EVAL_N,statistics.fmean(returns),statistics.fmean(lengths)


def main():
    assert sys.argv[1:] in ([], ["--tabular"]), "optional representation control: --tabular"
    tabular = "--tabular" in sys.argv
    print(f"offline lock-chain: states={STATES} actions={ACTIONS} demos={DEMOS} updates={UPDATES} eval={EVAL_N}/seed")
    print(f"actor beta_BC={BC_WEIGHT} eta_Q=0(BC)/{Q_WEIGHT}(RL); critic TD=1 alpha={ALPHA} LSE_temperature={TEMP}; gamma={GAMMA}")
    print("critic=full tabular representation control" if tabular else
          f"critic Q(s,a)=w_s*features[a], features={FEATURES}; model misspecification intentionally retained")
    print("same full demo batch/actor updates and eval action+transition uniforms; BC critic=NA, not equal FLOPs")
    print("seed arm transitions success mean_return mean_steps policy_Q MC_behavior_V min_state_Q_minus_V masked_fraction")
    scores = {a:[] for a in ARMS}
    for seed in SEEDS:
        data = dataset(seed)
        rng = random.Random(seed+10000)
        draws = tuple(tuple((rng.random(),rng.random()) for _ in range(STATES)) for _ in range(EVAL_N))
        for arm in ARMS:
            pi,q,ref,gap,masked = train(arm,data,tabular)
            success,ret,steps = evaluate(pi,draws)
            scores[arm].append((success,ret,q,ref,gap))
            mechanism = f"{q:.6f} {ref:.6f} {gap:.6f} {masked:.4f}" if arm!="BC_only" else f"NA {ref:.6f} NA NA"
            print(f"{seed} {arm} {sum(map(len,data))} {success:.3f} {ret:.6f} {steps:.3f} {mechanism}")
    print("arm success_mean population_sd min max return_mean policy_Q_mean MC_behavior_V_mean")
    for arm,rs in scores.items():
        success = [r[0] for r in rs]
        q = f"{statistics.fmean(r[2] for r in rs):.6f}" if arm!="BC_only" else "NA"
        print(f"{arm} {statistics.fmean(success):.4f} {statistics.pstdev(success):.4f} {min(success):.3f} {max(success):.3f} "
              f"{statistics.fmean(r[1] for r in rs):.6f} {q} {statistics.fmean(r[3] for r in rs):.6f}")
    print("Cal-QL masks conservative push-down below MC reference; learned Q is NOT hard-clipped or a universal per-action lower bound")
    print("offline only: online unlearning dip is reading, NOT demonstrated; no universal winner")
    print("distinct from advantage filtering/10.6 HIL-SERL; consistency head not reproduced; paper 以论文为准; GPU/robot 本页未运行")


if __name__ == "__main__":
    main()
