#!/usr/bin/env python3
"""Synthetic contextual bandit, not robot/VLA DPO or an online RL reproduction.
Five arms reconcile BC-all/success-filter literacy with the three core baselines.
Every arm receives SAME 64 training preference pairs and 240 total gradient slots.
RM+RL spends 120 slots fitting reward, then 120 on exact expected reward-minus-KL.
Binary success labels are extra TRAINING supervision for success_filter only;
all records include them but core DPO/RM/BC_preferred do not consume them.
Truth utility is used only by data generation and held-out scoring, never training.
"""
from math import exp, log, log1p, sin
from random import Random
from statistics import mean, pstdev

SEEDS=(11,23,37,53,71)
ACTIONS=(-1.,0.,1.)
REF=(-.3,0.,.2,-.5)
PAIRS, UPDATES, BETA, LR=64,240,.5,.12
ARMS=('BC_all','success_filter','BC_preferred','DPO','RM_RL')


def features(x,a):return (a*x,a*sin(4*x),a,a*a)


def dot(a,b):return sum(x*y for x,y in zip(a,b))


def probabilities(theta,x):
    scores=[dot(theta,features(x,a)) for a in ACTIONS];mx=max(scores)
    values=[exp(v-mx) for v in scores];total=sum(values)
    return tuple(v/total for v in values)


def utility(x,a):return -(a-(.85*x+.2*sin(4*x)))**2


def successful(x,a):return max(utility(x,b) for b in ACTIONS)-utility(x,a)<=.12


def make_data(seed,noise):
    rng=Random(seed);flip=Random(seed+9000);records=[]
    for _ in range(PAIRS):
        x=rng.uniform(-1,1);a,b=rng.sample(range(3),2)
        w,l=(a,b) if utility(x,ACTIONS[a])>=utility(x,ACTIONS[b]) else (b,a)
        if flip.random()<noise:w,l=l,w
        records.append((x,w,l,tuple(int(successful(x,a)) for a in ACTIONS)))
    erng=Random(seed+1000);evaluation=tuple(erng.uniform(-1,1) for _ in range(256))
    assert not set(evaluation)&{x for x,_,_,_ in records}
    return tuple(records),evaluation


def sigmoid_minus(z):
    if z>=0:
        e=exp(-z);return e/(1+e)
    return 1/(1+exp(z))


def dpo_loss(theta,x,w,l):
    p,ref=probabilities(theta,x),probabilities(REF,x)
    z=BETA*((log(p[w])-log(ref[w]))-(log(p[l])-log(ref[l])))
    return max(0.,-z)+log1p(exp(-abs(z)))


def gradient(theta,reward,records,arm,slot):
    grad=[0.]*4
    for x,w,l,success in records:
        fs=tuple(features(x,a) for a in ACTIONS)
        if arm=='DPO' or (arm=='RM_RL' and slot<UPDATES//2):
            delta=tuple(a-b for a,b in zip(fs[w],fs[l]))
            if arm=='DPO':
                z=BETA*dot(tuple(a-b for a,b in zip(theta,REF)),delta)
                g=tuple(BETA*sigmoid_minus(z)*v for v in delta)
            else:g=tuple(sigmoid_minus(dot(reward,delta))*v for v in delta)
        else:
            p=probabilities(theta,x)
            if arm=='RM_RL':
                ref=probabilities(REF,x)
                adjusted=tuple(dot(reward,f)-BETA*log(pa/pr) for f,pa,pr in zip(fs,p,ref))
                baseline=dot(p,adjusted)
                g=tuple(sum(pa*(v-baseline)*f[j] for pa,v,f in zip(p,adjusted,fs)) for j in range(4))
            else:
                candidates=(w,l) if arm=='BC_all' else ((w,) if arm=='BC_preferred' else tuple(a for a in (w,l) if success[a]))
                # Empty binary-success pairs contribute zero, but still use the same slot/batch denominator.
                g=tuple((mean(fs[a][j] for a in candidates)-sum(pa*f[j] for pa,f in zip(p,fs))) if candidates else 0. for j in range(4))
        grad=[a+b/len(records) for a,b in zip(grad,g)]
    return tuple(grad)


def train(records,arm):
    theta=REF;reward=(0.,)*4;policy_updates=reward_updates=0
    for slot in range(UPDATES):
        g=gradient(theta,reward,records,arm,slot)
        if arm=='RM_RL' and slot<UPDATES//2:
            reward=tuple(a+LR*b for a,b in zip(reward,g));reward_updates+=1
        else:
            theta=tuple(a+LR*b for a,b in zip(theta,g));policy_updates+=1
    return theta,(policy_updates,reward_updates)


def evaluate(theta,contexts):
    successes=[];regrets=[]
    for x in contexts:
        p=probabilities(theta,x);u=tuple(utility(x,a) for a in ACTIONS)
        successes.append(sum(pa*int(successful(x,a)) for pa,a in zip(p,ACTIONS)))
        regrets.append(max(u)-dot(p,u))
    return 100*mean(successes),mean(regrets)


def main():
    print('Synthetic offline bandit; seeds=11/23/37/53/71; held-out256 contexts per seed')
    print('shared64 preference pairs; total_gradient_updates=240 each; full_batch=64; lr=0.12 beta=KL_tau=0.5')
    print('RM_RL budget: reward120+policy120; others policy240; equal slots, NOT equal FLOPs/parameter counts')
    print('success_filter alone consumes extra binary TRAINING success labels; core three use preferences only')
    print('noise arm heldout_expected_success_pct_mean_sd regret_mean_sd policy_updates reward_updates')
    for noise in (0.,.25):
        cases=tuple(make_data(seed,noise) for seed in SEEDS)
        for arm in ARMS:
            trained=[train(data,arm) for data,_ in cases]
            metrics=[evaluate(theta,case[1]) for (theta,_),case in zip(trained,cases)]
            success,regret=zip(*metrics);pu,ru=trained[0][1]
            print(f'{noise:.2f} {arm} {mean(success):.4f} {pstdev(success):.4f} {mean(regret):.6f} {pstdev(regret):.6f} {pu} {ru}')
    print('Population sd across all5 seeds; exact policy expectation, no sampled rollout winner assumption')
    print('No SARM progress weights / Cal-ConRFT / RPD / OneDP; full VLA and online RL: 本页未运行')
    print('DPO paper figures: 以论文为准; this is loss/budget literacy, not a robot benchmark')


if __name__=='__main__':main()
