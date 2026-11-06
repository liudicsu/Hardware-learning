#!/usr/bin/env python3
"""Independent boundary, frame, identification and held-out regressions (stdlib)."""
import ast
import inspect
import math
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
CAN = ROOT / 'examples/month-8/ros2-hardware-interface/can_fault_confinement_toy.py'
FT = ROOT / 'examples/month-9/effort-admittance/ft_bias_gravity_toy.py'
for path in (CAN, FT):
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            assert all(x.name in {'dataclasses', 'math', 'random', 'statistics'} for x in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module in {'dataclasses', 'math', 'random', 'statistics'} and node.level == 0
c, f = runpy.run_path(str(CAN)), runpy.run_path(str(FT))
Node = c['Node']

# Exact 127/128 and 255/256; REC alone never switches off TX drivers.
for tec, rec, state in ((127,127,'error-active'),(128,0,'error-passive'),
                        (0,128,'error-passive'),(255,0,'error-passive'),
                        (256,0,'bus-off'),(0,512,'error-passive')):
    assert Node(tec, rec).state == state
n=Node(tec=255); n.apply('tx_ok'); assert n.tec == 254 and n.state == 'error-passive'
n=Node(tec=255); n.apply('tx_error'); assert n.tec == 263 and n.state == 'bus-off'
for event in ('tx_error','tx_flag_bit','tx_extension'):
    n=Node(); n.apply(event); assert (n.tec,n.rec)==(8,0)
for event in ('rx_after_flag_dominant','rx_flag_bit','rx_extension'):
    n=Node(); n.apply(event); assert (n.tec,n.rec)==(0,8)
n=Node(); n.apply('rx_error'); n.apply('rx_after_flag_dominant'); assert n.rec==9
for value,expected in ((0,0),(1,0),(127,126),(128,127),(512,127)):
    n=Node(rec=value);n.apply('rx_ok');assert n.rec==expected
for event in ('rx_ok','tx_ok'):
    n=Node();n.apply(event);assert n.tec==n.rec==0
n=Node(tec=128);n.apply('tx_passive_ack_exception');assert n.tec==128
n.apply('tx_arbitration_stuff_exception');assert n.tec==128
# One isolated transmitter loses ACK: ordinary +8 only until passive, then exception.
n=Node()
for _ in range(100):
    n.apply('tx_passive_ack_exception' if n.state=='error-passive' else 'tx_error')
assert n.tec==128 and n.state=='error-passive'
for flag,first in (('active',14),('overload',14),('passive',8)):
    assert [c['extension_events'](flag,k) for k in (first-1,first,first+7,first+8)] == [0,1,1,2]
healthy,ht=c['transmitter_trace'](False);noisy,nt=c['transmitter_trace'](True)
assert len(c['shared_schedule']())==43
assert [row[1] for row in nt]==[128,120,248,256,256]
assert healthy.accepted==43 and noisy.accepted==8 and noisy.blocked==2
# While off, every event is gated before counters/ACK/acceptance change.
for event in c['EVENTS']:
    n=Node(tec=256);assert not n.apply(event);assert (n.tec,n.rec,n.accepted,n.blocked)==(256,0,0,1)
n=Node(tec=256);assert not n.request_recovery()
n.observe(('1'*10+'0')*128);assert n.sequences==0 and not n.request_recovery()
n.observe('1'*(127*11+10));assert (n.sequences,n.recessive_run)==(127,10) and not n.request_recovery()
n.observe('1');assert n.sequences==128 and n.request_recovery()
assert n.tec==n.rec==0 and n.state=='error-active'
n=Node(tec=256);n.observe('1'*11+'0'+'1'*11);assert n.sequences==2 # completed groups persist

# Independent coordinate tests: orthonormality, handedness, gravity and same-origin rotation.
for pose in f['CAL_POSES']+f['EVAL_POSES']:
    r=f['rotation'](pose)
    for j in range(3):
        for k in range(3):
            assert math.isclose(sum(r[a][j]*r[a][k] for a in range(3)),float(j==k),abs_tol=1e-12)
    assert f['norm'](f['sub'](f['cross'](r[0],r[1]),r[2]))<1e-12
    v=(.3,-.4,.7);assert f['norm'](f['sub'](f['to_base'](r,f['to_sensor'](r,v)),v))<1e-12
assert f['norm'](f['sub'](f['to_sensor'](f['rotation']((0,math.pi/2,0)),f['G_BASE']),(9.81,0,0)))<1e-12
assert len(f['CAL_POSES'])==6 and len(f['SEEDS'])>=5
assert not set(f['CAL_POSES']) & set(f['EVAL_POSES'])
for name in ('fit','compensate'):
    assert 'TRUTH' not in inspect.getsource(f[name])

# Identify a DIFFERENT plant from equations, not the toy's named truth/constants.
# Three sufficiently distinct orientations suffice here; six make a balanced design.
mass,com,bf,bt=1.23,(-.021,.042,.08),(.8,-.6,.1),(.03,.02,-.04)
rows=[]
for g in ((0.,0.,-9.81),(9.81,0.,0.),(0.,9.81,0.)):
    force=tuple(mass*x+b for x,b in zip(g,bf))
    h=tuple(mass*x for x in com)
    tau=(h[1]*g[2]-h[2]*g[1]+bt[0],h[2]*g[0]-h[0]*g[2]+bt[1],h[0]*g[1]-h[1]*g[0]+bt[2])
    rows.append((g,force,tau))
estimated=f['fit'](rows)
assert abs(estimated[0]-mass)<1e-12
for actual,expected in zip(estimated[1:],(com,bf,bt)):
    assert f['norm'](f['sub'](actual,expected))<1e-12
try:
    f['fit']([rows[0]]*16)
except ValueError as exc:
    assert 'rank deficient' in str(exc)
else:
    raise AssertionError('one-pose mass/COM/offset fit must reject rank failure')

# Exact noiseless held-out recovery and explicit one-pose orientation failure.
cal,evaluation=f['datasets'](11,0.,0.);est,zero=f['fit'](cal),f['tare'](cal)
assert f['score']('ls_gravity',evaluation,est,zero)[0]<1e-12
assert f['score']('ls_gravity',evaluation,est,zero)[1]<1e-12
assert f['norm'](f['compensate']('one_pose_tare',cal[0],est,zero)[0])<1e-12
# -Z to +X changes gravity vector by magnitude g*sqrt(2).
rotated=cal[32];residual=f['compensate']('one_pose_tare',rotated,est,zero)
assert math.isclose(f['norm'](residual[0]),f['TRUTH'][0]*9.81*math.sqrt(2),abs_tol=1e-12)
assert f['norm'](residual[1])>.1

# Held-out labels cannot change a calibration fit; same recorded rows, no arm resampling.
for seed in f['SEEDS']:
    cal,evaluation=f['datasets'](seed)
    assert (cal,evaluation)==f['datasets'](seed)
    assert len(cal)==96 and len(evaluation)==120 and sum(s[5] for s in evaluation)==60
    est,zero=f['fit'](cal),f['tare'](cal)
    assert abs(est[0]-.72)<.005 and f['norm'](f['sub'](est[1],f['TRUTH'][1]))<.0005
    copied=list(evaluation)
    scores={arm:f['score'](arm,evaluation,est,zero) for arm in f['ARMS']}
    assert evaluation==copied
    for result in scores.values():
        assert result[0]>=0 and result[1]>=0 and 0<=result[2]<=1 and 0<=result[3]<=60
    assert scores['one_pose_tare'][3]>=40
    assert .10<scores['ls_gravity'][0]<.20 and scores['ls_gravity'][1]<.01
    assert scores['ls_gravity'][0]<scores['raw'][0] # declared synthetic plant only
    assert scores['bias_only_ls'][0]>scores['raw'][0] # no assumed universal subtraction winner
print('b6p2 physical tests: CAN exact thresholds/exceptions/REC +8/recovery gates; independent frames, three-pose non-oracle LS, rank rejection, noiseless rotated-tare failure and five-seed held-out metrics passed')
