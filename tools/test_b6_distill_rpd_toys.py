#!/usr/bin/env python3
"""Independent non-oracle/data-split, NFE, derivative and equal-budget checks."""
import ast
from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
from math import isclose
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=spec_from_file_location(name,ROOT/path)
    module=module_from_spec(spec);spec.loader.exec_module(module)
    return module

D=load('distill','examples/month-10/flow-matching-policies/policy_distill_onestep_toy.py')
R=load('rpd','examples/month-8/vla-finetune/rpd_teacher_rl_toy.py')
assert len(D.SEEDS)>=5 and D.SEEDS==R.SEEDS
for module in (D,R):
    tree=ast.parse(Path(module.__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            assert all(n.name.split('.')[0] in sys.stdlib_module_names for n in node.names)
        elif isinstance(node,ast.ImportFrom):
            assert node.module.split('.')[0] in sys.stdlib_module_names
    assert sum(isinstance(n,ast.FunctionDef) and n.name=='main' for n in ast.walk(tree))==1
# Actual teacher calls, rather than trusting a reported counter.
original_field=D.field
count=[0]
def counted_field(*args):
    count[0]+=1
    return original_field(*args)
D.field=counted_field
for start in D.EVAL_STARTS:
    before=count[0];action,nfe=D.teacher(start)
    assert nfe==count[0]-before==D.N_STEPS
    # Independent plant expression, not teacher action agreement.
    assert abs(-start+action+.22*action**3)<=D.TOLERANCE
D.field=original_field
for seed in D.SEEDS:
    demos,initial=D.demonstrations(seed)
    original=deepcopy((demos,initial))
    states=tuple(x for x,_ in demos)
    assert len(set(states))==D.N_DEMOS and not set(states)&set(D.EVAL_STARTS)
    # Fail if fit or student secretly queries teacher, including eval labels.
    original_teacher=D.teacher
    def forbidden(*args):
        raise AssertionError('student fitting/inference queried teacher')
    D.teacher=forbidden
    full=D.fit(demos,initial,D.FULL_UPDATES)
    under=D.fit(demos,initial,D.UNDER_UPDATES)
    for weights in (full,under):
        predictions=[D.student(weights,x) for x in D.EVAL_STARTS]
        assert all(nfe==1 for _,nfe in predictions)
    D.teacher=original_teacher
    assert original==(demos,initial)
    # Reject accidental training-state evaluation.
    try:D.evaluate(lambda x:D.student(full,x),states,tuple(0. for _ in states),states)
    except ValueError:pass
    else:raise AssertionError('overlap not rejected')
# Independent forward probability propagation verifies the backward DP diagnostic.
def forward_success(p):
    distribution=[.5,.5,0.,0.,0.,0.]
    for _ in range(R.HORIZON):
        nxt=[0.]*6;nxt[5]=distribution[5]
        for state in range(5):
            for action,prob in ((1,p[state]),(0,1-p[state])):
                if action==R.CORRECT[state]:
                    nxt[state]+=distribution[state]*prob*R.SLIP
                    nxt[state+1]+=distribution[state]*prob*(1-R.SLIP)
                else:nxt[0]+=distribution[state]*prob
        distribution=nxt
    return distribution[5]
teacher=tuple(R.teacher_mean(s) for s in range(5));optimal=tuple(float(a) for a in R.CORRECT)
for p in (teacher,optimal,(.5,)*5):
    assert isclose(R.exact_success(p),forward_success(p),abs_tol=1e-12)
assert forward_success(optimal)>forward_success(teacher)+.1
for x in (-2.,-.3,.2,2.):
    for label in (0,1):
        h=1e-5
        numeric=((R.sigmoid(x+h)-label)**2-(R.sigmoid(x-h)-label)**2)/(2*h)
        assert isclose(numeric,R.mse_logit_gradient(R.sigmoid(x),label),abs_tol=1e-9)
# Verify executed ticks, teacher calls and updates (including absorbing ticks).
early_bc_wins=0
for seed in R.SEEDS:
    training=R.tape(1000+seed,R.UPDATES*R.BATCH)
    evaluation=R.tape(100000+seed,256)
    assert training==R.tape(1000+seed,R.UPDATES*R.BATCH) and evaluation!=training[:256]
    frozen=deepcopy(training)
    metrics={};initializations=[]
    for arm in R.WEIGHTS:
        original_transition,original_teacher,original_update=R.transition,R.teacher_mean,R.update
        counters={'ticks':0,'queries':0,'updates':0}
        first=[]
        def transition(*args):
            counters['ticks']+=1;return original_transition(*args)
        def teacher_mean(*args):
            counters['queries']+=1;return original_teacher(*args)
        def update(logits,batch,arm):
            if not first:first.append(tuple(logits))
            counters['updates']+=1;return original_update(logits,batch,arm)
        R.transition,R.teacher_mean,R.update=transition,teacher_mean,update
        result=R.train(seed,arm,training)
        R.transition,R.teacher_mean,R.update=original_transition,original_teacher,original_update
        assert counters=={'ticks':7680,'queries':7680,'updates':80}
        initializations.append(first[0]);snapshot=deepcopy(result)
        for step,(probabilities,ticks,updates,active) in result.items():
            assert ticks==step*R.BATCH*R.HORIZON and updates==step
            assert 0<active<=ticks and len(probabilities)==5
            metrics[(step,arm)]=R.evaluate(probabilities,evaluation)
        assert result==snapshot and training==frozen
    assert initializations[0]==initializations[1]==initializations[2]
    early_bc_wins+=metrics[(8,'BC_only')][0]>metrics[(8,'RL_scratch')][0]
assert early_bc_wins>0, 'retain observed BC-winning cases, no universal guidance win'
print('independent held-out splits, actual NFE, no teacher/eval-label cheat, beatable teacher DP, finite-difference MSE and equal executed budgets passed')
