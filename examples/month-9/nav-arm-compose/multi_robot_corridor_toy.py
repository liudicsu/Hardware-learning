#!/usr/bin/env python3
"""Two holonomic discs, single-lane corridor with holding rooms (stdlib).
Shared starts/goals and pre-generated neighbor-noise draws across all arms.
Ignore sees own route only. Mutex uses reliable request/grant/release messages
and a shared reservation: EXTRA information, not a local-only competitor.
ORCA-lite is an ORCA-INSPIRED reciprocal STOP sketch, NOT the ORCA velocity-
obstacle construction/LP. Each approaching disc takes half the available
clearance budget over horizon TAU, slowing BOTH. No passing-side or back-out
planner: local collision avoidance can deadlock in a single-lane corridor.
For clarity, this is not the linear program of the original RVO/ORCA.
Holonomic vector velocities, same speed/acceleration limits in ALL arms.
Acceleration/noise can invalidate ideal reciprocal-avoidance guarantees;
we measure collisions instead of claiming a certificate or real ORCA results.
Kinematic overlaps are logged, not resolved with fictional contact dynamics.
Real fleet/communications 本页未运行; IL/VMAS paper is reading only, 以论文为准.
"""
import math
import random
import statistics

DT, LIMIT_S = .05, 24.
VMAX, AMAX, RADIUS = .6, .8, .22
TAU, MARGIN, SENSOR_RANGE = 2., .08, 3.
SEEDS = (926, 927, 928, 929, 930)
ARMS = ("ignore_others", "priority_mutex_extra_info", "ORCA_lite_reciprocal_stop")


def norm(v):
    return math.hypot(*v)


def sub(a, b):
    return (a[0]-b[0], a[1]-b[1])


def cap(v, length):
    scale = min(1., length/max(norm(v), 1e-15))
    return (v[0]*scale, v[1]*scale)


def scenario(seed):
    rng = random.Random(seed)
    starts = ((-rng.uniform(2.3,3.2), -rng.uniform(.65,.85)),
              (rng.uniform(2.3,3.2), rng.uniform(.65,.85)))
    goals = ((rng.uniform(2.3,3.2), -rng.uniform(.65,.85)),
             (-rng.uniform(2.3,3.2), rng.uniform(.65,.85)))
    # Same indexed perturbations, not the same measured state after paths diverge.
    noise = tuple(tuple((rng.uniform(-.005,.005), rng.uniform(-.005,.005))
                        for _ in range(2)) for _ in range(round(LIMIT_S/DT)))
    return starts, goals, noise


def segment_distance(old, new):
    # Exact closest relative point over one linear integration segment.
    r, dr = sub(old[0],old[1]), sub(sub(new[0],new[1]),sub(old[0],old[1]))
    t = max(0., min(1., -(r[0]*dr[0]+r[1]*dr[1])/max(norm(dr)**2,1e-30)))
    return norm((r[0]+t*dr[0], r[1]+t*dr[1]))


def simulate(arm, data):
    starts, goals, noise = data
    p, v = list(starts), [(0.,0.),(0.,0.)]
    routes = (((-1.4,0.),(1.4,0.),goals[0]), ((1.4,0.),(-1.4,0.),goals[1]))
    stage, arrival, waited = [0,0], [None,None], [0.,0.]
    # Both request at t=0; fixed ID priority, token released by arrival message.
    token = 0
    collisions, overlapping, minsep = 0, False, norm(sub(*starts))
    positions = [tuple(p)]
    for k, eps in enumerate(noise):
        desired = []
        for i in range(2):
            if arrival[i] is not None:
                desired.append((0.,0.)); continue
            if stage[i] < 2 and norm(sub(routes[i][stage[i]],p[i])) < .04:
                stage[i] += 1
            delta = sub(routes[i][stage[i]],p[i])
            pref = cap((2*delta[0],2*delta[1]),VMAX)
            if arm == "priority_mutex_extra_info" and i != token:
                pref = (0.,0.)
            elif arm == "ORCA_lite_reciprocal_stop":
                j = 1-i
                rel = (p[j][0]-p[i][0]+eps[i][0], p[j][1]-p[i][1]+eps[i][1])
                dist = norm(rel)
                approach = (pref[0]*rel[0]+pref[1]*rel[1])/max(dist,1e-15)
                if dist < SENSOR_RANGE and approach > 0:
                    clearance = max(0.,dist-2*RADIUS-MARGIN)
                    # Equal half of pair clearance/T; stop only, no side-step LP.
                    scale = min(1.,clearance/(2*TAU*approach))
                    pref = (pref[0]*scale,pref[1]*scale)
            desired.append(pref)
        old = tuple(p)
        for i in range(2):
            dv = cap(sub(desired[i],v[i]),AMAX*DT)
            nextv = (v[i][0]+dv[0],v[i][1]+dv[1])
            if stage[i] == 2 and norm(sub(goals[i],p[i])) < .06 and norm(v[i]) <= AMAX*DT:
                nextv = (0.,0.)
                if arrival[i] is None:
                    arrival[i] = (k+1)*DT
                    if arm == "priority_mutex_extra_info" and token == i:
                        token = 1-i  # release/grant; never pre-grants future clearance
            assert norm(nextv) <= VMAX+1e-12 and norm(sub(nextv,v[i])) <= AMAX*DT+1e-12
            v[i] = nextv
            p[i] = (p[i][0]+v[i][0]*DT,p[i][1]+v[i][1]*DT)
            # Conservative inflated single-lane rectangle; no wall projection/teleport.
            assert abs(p[i][0]) > 1.22 or abs(p[i][1]) <= .08+1e-12
            if arrival[i] is None and norm(v[i]) < .06:
                waited[i] += DT
        sep = segment_distance(old,p)
        minsep = min(minsep,sep)
        inside = sep < 2*RADIUS
        collisions += inside and not overlapping
        overlapping = inside
        positions.append(tuple(p))
    unfinished = sum(t is None for t in arrival)
    # Finite-time liveness proxies, not a proof of infinite starvation/deadlock.
    tail_start = positions[-1-round(3/DT)]
    progress = sum(norm(sub(p[i],tail_start[i])) for i in range(2) if arrival[i] is None)
    deadlock = int(unfinished == 2 and progress < .02)
    starvation = sum(arrival[i] is None and waited[i] >= LIMIT_S/2 for i in range(2))
    censored_mean = statistics.fmean(t if t is not None else LIMIT_S for t in arrival)
    times = "/".join("timeout" if t is None else f"{t:.2f}" for t in arrival)
    return collisions, times, censored_mean, unfinished, deadlock, starvation, minsep


def main():
    print(f"holonomic discs r={RADIUS} m corridor_width=.60 m; vmax={VMAX} m/s amax={AMAX} m/s^2 dt={DT} s limit={LIMIT_S} s")
    print("mutex=EXTRA reliable communication/shared reservation; ORCA-lite=reciprocal stop sketch, NOT full ORCA LP")
    print("seed starts(x,y)_m goals(x,y)_m")
    datasets = {seed:scenario(seed) for seed in SEEDS}
    for seed,(starts,goals,_) in datasets.items():
        fmt = lambda points: ";".join(f"({x:.3f},{y:.3f})" for x,y in points)
        print(f"{seed} {fmt(starts)} {fmt(goals)}")
    print("seed arm collision_episodes arrivals_s capped_mean_s timeouts/2 deadlock_proxy starvation_proxy min_sep_m")
    scores = {a:[] for a in ARMS}
    for seed,data in datasets.items():
        for arm in ARMS:
            r = simulate(arm,data)
            scores[arm].append(r)
            c,t,m,n,d,s,sep = r
            print(f"{seed} {arm} {c} {t} {m:.3f} {n}/2 {d} {s} {sep:.6f}")
    print("arm total_collisions mean_capped_arrival_s population_sd total_timeouts deadlock_runs starvation_robots min_sep_m")
    for arm,rs in scores.items():
        means=[r[2] for r in rs]
        print(f"{arm} {sum(r[0] for r in rs)} {statistics.fmean(means):.3f} {statistics.pstdev(means):.3f} "
              f"{sum(r[3] for r in rs)} {sum(r[4] for r in rs)} {sum(r[5] for r in rs)} {min(r[6] for r in rs):.6f}")
    print("capped mean substitutes 24s for unfinished; collision episodes do not imply safe arrivals; no universal winner")
    print("not nav-pick BT/teleop RTT/EtherCAT; real fleet 本页未运行; curriculum IL reading only, 以论文为准")


if __name__ == "__main__":
    main()
