#!/usr/bin/env python3
"""Independent loss derivatives, no scoring leakage, budgets and controller information."""
import ast
import runpy
from copy import deepcopy
from math import log,isclose
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
paths=('examples/month-10/real-world-rl/preference_dpo_lite_toy.py','examples/month-6/act-diffusion/bimanual_coord_modes_toy.py')
for path in paths:
    for node in ast.walk(ast.parse((ROOT/path).read_text())):
        if isinstance(node,ast.ImportFrom):assert node.module in ('math','random','statistics')
        assert not isinstance(node,ast.Import)
d,b=(runpy.run_path(str(ROOT/p)) for p in paths)
assert len(d['SEEDS'])>=5 and len(b['SEEDS'])>=5
records,evaluation=d['make_data'](11,0.)
for seed in d['SEEDS']:
    clean,ev=d['make_data'](seed,0.);noisy,evn=d['make_data'](seed,.25)
    assert ev==evn and not set(ev)&{r[0] for r in clean}
    assert len(clean)==d['PAIRS'] and any(a[1:3]!=z[1:3] for a,z in zip(clean,noisy))
    for a,z in zip(clean,noisy):assert a[0]==z[0] and set(a[1:3])==set(z[1:3]) and a[3]==z[3]
# Finite differences of the actual DPO log-probability loss, with frozen nonuniform ref.
theta=(.1,-.2,.3,-.4);reward=(.4,-.1,.2,-.3);h=1e-6
x,w,l,_=records[0];one=(records[0],)
def finite(fn,j):
    plus=list(theta);minus=list(theta);plus[j]+=h;minus[j]-=h
    return (fn(tuple(plus))-fn(tuple(minus)))/(2*h)
g=d['gradient'](theta,reward,one,'DPO',0)
for j in range(4):assert isclose(g[j],-finite(lambda t:d['dpo_loss'](t,x,w,l),j),abs_tol=1e-8)
assert isclose(d['dpo_loss'](d['REF'],x,w,l),log(2),abs_tol=1e-12)
# Independent finite-action reward-minus-KL objective, not a true-utility training oracle.
def objective(t):
    p,ref=d['probabilities'](t,x),d['probabilities'](d['REF'],x)
    return sum(pa*(d['dot'](reward,d['features'](x,a))-d['BETA']*log(pa/pr)) for a,pa,pr in zip(d['ACTIONS'],p,ref))
g=d['gradient'](theta,reward,one,'RM_RL',d['UPDATES']//2)
for j in range(4):assert isclose(g[j],finite(objective,j),abs_tol=1e-8)
# Reward preference fitting derivative and preferred-only BC derivative independently.
def rm_loss(r):
    margin=d['dot'](r,tuple(a-b for a,b in zip(d['features'](x,d['ACTIONS'][w]),d['features'](x,d['ACTIONS'][l]))))
    return -log(1-d['sigmoid_minus'](margin))
g=d['gradient'](theta,theta,one,'RM_RL',0)
for j in range(4):assert isclose(g[j],-finite(rm_loss,j),abs_tol=1e-8)
g=d['gradient'](theta,reward,one,'BC_preferred',0)
for j in range(4):assert isclose(g[j],-finite(lambda t:-log(d['probabilities'](t,x)[w]),j),abs_tol=1e-8)
# Training cannot access utility/success or eval contexts. Poison those helpers dynamically.
namespace=d['train'].__globals__;saved={k:namespace[k] for k in ('utility','successful')}
def forbidden(*args):raise AssertionError('ground-truth scoring leaked into optimization')
namespace.update({k:forbidden for k in saved})
before=deepcopy(records)
try:
    for arm in d['ARMS']:
        _,(pu,ru)=d['train'](records,arm)
        assert pu+ru==240 and (pu,ru)==((120,120) if arm=='RM_RL' else (240,0))
        assert records==before
    poisoned=tuple((x,w,l,tuple(1-v for v in flags)) for x,w,l,flags in records)
    for arm in ('DPO','RM_RL','BC_preferred'):
        assert d['gradient'](theta,reward,records,arm,0)==d['gradient'](theta,reward,poisoned,arm,0)
finally:namespace.update(saved)
# All modes receive the same observation schema; independent only factorizes its use.
obs=(0.,.6,0.,0.,.8,1.4,.6);changed=(0.,.4,0.,0.,.8,1.4,.6)
assert b['commands'](obs,'independent')[0]==b['commands'](changed,'independent')[0]
assert b['commands'](obs,'leader_follower')[0]!=b['commands'](changed,'leader_follower')[0]
assert b['commands'](obs,'joint')[0]!=b['commands'](changed,'joint')[0]
assert 'gains' not in b['commands'].__code__.co_names and 'stream' not in b['commands'].__code__.co_names
# Count every action invocation even with an immediately settled task.
zero_noise=(((0.,0.),(0.,0.),(0.,0.)),)*400
case=((0.,.6),(0.,.6),(1.,.6),zero_noise)
namespace=b['rollout'].__globals__;original=namespace['commands']
for mode in b['MODES']:
    observations=[]
    def spy(obs,which):observations.append(obs);return original(obs,which)
    namespace['commands']=spy
    row=b['rollout'](case,mode)
    assert len(observations)==row['ticks']==400 and all(len(o)==7 for o in observations)
    assert row['capped_makespan']==.4 and row['success']==1 and row['collisions']==0
namespace['commands']=original
# Same immutable plant/noise cases for all modes and all seeds, no favorable seed subset.
for seed in b['SEEDS']:
    case=b['make_case'](seed);before=deepcopy(case)
    for mode in b['MODES']:
        row=b['rollout'](case,mode)
        assert row['ticks']==400 and 0<row['capped_makespan']<=8 and row['span_rmse']>=0
        assert row['success']==int(not row['timeout'] and row['collisions']==0) and case==before
# A deliberately impossible goal verifies censoring/timeout accounting, not a trained benchmark.
case=((0.,.6),(100.,100.6),(1.,.6),zero_noise)
row=b['rollout'](case,'joint');assert row['timeout']==1 and row['success']==0 and row['capped_makespan']==8
print('independent DPO/RM/RL/BC derivatives, no-truth training, equal total updates, shared bimanual observations/noise and full-horizon/censoring tests passed')
