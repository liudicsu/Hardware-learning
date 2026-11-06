#!/usr/bin/env python3
"""Synthetic two-endpoint shared-strap transport, not TwinVLA inference.
All modes/arms RECEIVE (noisy xL,xR,vL,vR,goalL,goalR,span) every tick.
Independent deliberately factorizes local feedback, not local-only sensor access.
Leader-follower uses left velocity/position and a left waiting gate; joint uses
center/span feedback. No controller receives latent actuator gain or future noise.
Each mode runs all400 ticks, including after first arrival, with same plant/noise.
Span error is a kinematic compliance proxy, NOT a force/strain dynamics model.
"""
from math import sqrt
from random import Random
from statistics import mean, pstdev

SEEDS=(11,23,37,53,71)
MODES=('independent','leader_follower','joint')
TICKS, DT, VMAX, AMAX=400,.02,.35,.8
SPAN, COLLISION_DISTANCE=.6,.32


def clip(x,bound):return max(-bound,min(bound,x))


def make_case(seed):
    r=Random(seed);center=r.uniform(-.05,.05);span=SPAN+r.uniform(-.02,.02)
    start=(center-span/2,center+span/2);goal=center+r.uniform(.75,.9)
    gains=(r.uniform(.9,1.),r.uniform(.55,.8))
    # All modes share this exogenous sensor/disturbance stream, not their resulting states.
    stream=tuple((tuple(r.gauss(0,.003) for _ in range(2)),tuple(r.gauss(0,.01) for _ in range(2)),tuple(r.gauss(0,.006) for _ in range(2))) for _ in range(TICKS))
    return start,(goal-SPAN/2,goal+SPAN/2),gains,stream


def commands(observation,mode):
    left,right,vl,vr,gl,gr,span=observation
    if mode=='independent':return (2*(gl-left),2*(gr-right))
    if mode=='leader_follower':
        lead=2*(gl-left)
        if right-left<span-.06:lead=0. # Wait for follower, using the SAME noisy snapshot.
        return lead,2*(left+span-right)+vl
    center_error=(gl+gr-left-right)/2
    span_error=right-left-span
    common=2*center_error
    return common+5*span_error,common-5*span_error


def rollout(case,mode):
    start,goal,gains,stream=case;x=list(start);v=[0.,0.]
    stable=0;arrival=None;collisions=0;was_colliding=False;span_errors=[];min_sep=float('inf')
    for tick,(position_noise,velocity_noise,disturbance) in enumerate(stream):
        obs=(*tuple(a+b for a,b in zip(x,position_noise)),*tuple(a+b for a,b in zip(v,velocity_noise)),*goal,SPAN)
        command=commands(obs,mode)
        for j in range(2):
            desired=gains[j]*clip(command[j],VMAX)+disturbance[j]
            v[j]=clip(v[j]+clip(desired-v[j],AMAX*DT),VMAX)
            x[j]+=v[j]*DT
        separation=x[1]-x[0];min_sep=min(min_sep,separation)
        colliding=abs(separation)<COLLISION_DISTANCE
        collisions+=int(colliding and not was_colliding);was_colliding=colliding
        span_errors.append((separation-SPAN)**2)
        # Truth is a SCORE ONLY observer, not used by commands or its wait gate.
        settled=max(abs(a-b) for a,b in zip(x,goal))<=.025 and abs(separation-SPAN)<=.04
        stable=stable+1 if settled else 0
        if stable>=20 and arrival is None:arrival=(tick+1)*DT
    return {'success':int(arrival is not None and collisions==0),'collisions':collisions,
            'capped_makespan':arrival if arrival is not None else TICKS*DT,'timeout':int(arrival is None),
            'span_rmse':sqrt(mean(span_errors)),'min_separation':min_sep,'ticks':len(stream)}


def main():
    print('Synthetic shared-strap transport; seeds=11/23/37/53/71; no payload/force dynamics')
    print('all arms/modes RECEIVE same noisy xL,xR,vL,vR,goalL,goalR,span; no latent gain/future noise')
    print('independent: each uses own target/state; leader_follower: left gate + right follows measured left; joint: center/span')
    print('equal400 ticks after arrival too; dt=0.02s vmax=0.35m/s amax=0.8m/s2; same gain/noise stream per seed')
    print('arrival=20 consecutive settled ticks; score-only endpoints<=0.025m span_error<=0.04m')
    print('collision event=entry into distance<0.32m; success requires arrival AND zero collision events')
    print('mode success/5 collision_events_mean_sd capped_makespan_s_mean_sd timeouts/5 span_RMSE_m_mean_sd minimum_separation_m_mean_sd')
    cases=tuple(make_case(seed) for seed in SEEDS)
    for mode in MODES:
        rows=[rollout(case,mode) for case in cases]
        def report(key):
            values=[r[key] for r in rows];return f'{mean(values):.6f} {pstdev(values):.6f}'
        print(f'{mode} {sum(r["success"] for r in rows)}/5 {report("collisions")} {report("capped_makespan")} {sum(r["timeout"] for r in rows)}/5 {report("span_rmse")} {report("min_separation")}')
    print('Population sd; censored makespan uses8s at timeout, not an uncensored arrival-time mean')
    print('No presumed mode winner; independent available information equals joint, only coupling differs')
    print('Not ORCA-lite fleet / ACT chunk math; TwinVLA real robots/weights: 本页未运行; figures 以论文为准')


if __name__=='__main__':main()
