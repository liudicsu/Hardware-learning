#!/usr/bin/env python3
"""Independent geometry/linearization, observability and attitude-chart tests."""
import ast
from copy import deepcopy
from math import sin,cos,pi,isclose,hypot
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parents[1]
paths=('examples/month-4/slam-nav/icp_point_plane_toy.py','examples/month-5/kinematics-ik/quat_vs_euler_gimbal_toy.py')
for path in paths:
    for node in ast.walk(ast.parse((ROOT/path).read_text())):
        if isinstance(node,ast.ImportFrom):assert node.module in ('math','random','statistics')
        if isinstance(node,ast.Import):raise AssertionError('unexpected import')
i,q=(runpy.run_path(str(ROOT/path)) for path in paths)
# Nearest geometry uses no generating point IDs; estimated normal from target segment.
d,point,normal=i['nearest']((2.,3.),(((0.,0.),(0.,5.)),))
assert d==4 and point==(0.,3.) and normal==(-1.,0.)
assert i['nearest']((1.,8.),(((0.,0.),(0.,5.)),))[1]==(0.,5.)
# Closed-form rigid update, independent known correspondences in this UNIT TEST only.
points=((-1.,0.),(.5,1.),(1.,-.4),(.1,-1.))
truth=(.2,.3,-.1)
matches=tuple((x,i['transform'](x,truth),(0.,1.)) for x in points)
delta=i['increment'](matches,'point_point')
assert all(isclose(a,b,abs_tol=1e-12) for a,b in zip(delta,(truth[1],truth[2],truth[0])))
# Check the point-plane small-angle row numerically, not by repeating the solve.
x=(.4,-.7);n=(.6,.8);target=(.2,.1);h=1e-6
row=(n[0],n[1],-n[0]*x[1]+n[1]*x[0])
def residual(v):
    a=i['transform'](x,(v[2],v[0],v[1]));return sum(nn*(aa-bb) for nn,aa,bb in zip(n,a,target))
for j in range(3):
    v=[0.]*3;v[j]=h;minus=[-z for z in v]
    assert isclose((residual(v)-residual(minus))/(2*h),row[j],abs_tol=1e-9)
assert i['conditioning'](((2.,1.,0.),(1.,2.,0.),(0.,0.,4.)))==(3,'4.000')
assert 'TRUE' not in i['fit'].__code__.co_names and 'TRUE' not in i['correspondences'].__code__.co_names
assert len(i['SEEDS'])>=5 and len(i['OFFSETS'])>=5
for offset in i['OFFSETS']:
    for seed in i['SEEDS']:
        case=i['make_case'](seed,offset);assert case==i['make_case'](seed,offset)
        before=deepcopy(case)
        for arm in ('point_point','point_plane'):
            pose,error,steps=i['fit'](*case,arm)
            assert 0<=steps<=i['CAP'] and error>=0 and isclose(error,i['rmse'](case[0],case[1],pose))
            assert case==before
# Re-associated corridor objective genuinely loses dx; frozen q can falsely anchor it.
source,target,H=i['corridor']();assert i['conditioning'](H)==(2,'inf')
assert max(abs(H[0][j]) for j in range(3))<1e-6
for dx in (-5.,-1.,0.,1.,5.):assert i['rmse'](source,target,(0.,dx,0.))<1e-12
matches=i['correspondences'](source,target,(0.,1.,.1))
assert i['increment'](matches,'point_plane') is None # Reject rank loss, no hidden damping/oracle.
frozen=i['normal_matrix']([r for (x,y),_,_ in matches for r in ((1,0,-y),(0,1,x))])
assert i['conditioning'](frozen)[0]==3
# Independent direct active Rz Ry Rx matrix, not the quaternion multiplication path.
def direct(r,p,y):
    cr,sr,cp,sp,cy,sy=cos(r),sin(r),cos(p),sin(p),cos(y),sin(y)
    return ((cy*cp,cy*sp*sr-sy*cr,cy*sp*cr+sy*sr),
            (sy*cp,sy*sp*sr+cy*cr,sy*sp*cr-cy*sr),(-sp,cp*sr,cp*cr))
for pitch in (-pi/2,-1.,0.,1.,pi/2):
    angles=(.4,pitch,-.6);quat=q['from_euler'](angles);R=q['matrix'](quat)
    assert max(abs(a-b) for row,ref in zip(R,direct(*angles)) for a,b in zip(row,ref))<1e-12
    reconstructed=q['from_euler'](q['to_euler'](quat))
    assert q['distance'](quat,reconstructed)<1e-10
    assert q['distance'](quat,tuple(-x for x in quat))<1e-12
    # vee(R^T dR/dangle) independently checks body-rate Jacobian convention.
    J=q['rate_jacobian'](angles[0],angles[1])
    for column in range(3):
        ap=list(angles);am=list(angles);ap[column]+=h;am[column]-=h
        Rp,Rm=direct(*ap),direct(*am)
        derivative=[[(a-b)/(2*h) for a,b in zip(row1,row2)] for row1,row2 in zip(Rp,Rm)]
        skew=[[sum(R[k][j]*derivative[k][l] for k in range(3)) for l in range(3)] for j in range(3)]
        actual=(skew[2][1],skew[0][2],skew[1][0])
        assert max(abs(actual[j]-J[j][column]) for j in range(3))<1e-9
    assert q['rank'](J)==(2 if abs(pitch)==pi/2 else 3)
for sign in (-1,1):
    J=q['rate_jacobian'](.4,sign*pi/2);null=(1.,0.,float(sign))
    assert max(abs(sum(a*b for a,b in zip(row,null))) for row in J)<1e-12
paths=q['paths']();assert all(len(path)==q['N']+1 for path in paths)
for path in paths:
    assert q['distance'](path[0],q['from_euler'](q['START']))<1e-12
    assert q['distance'](path[-1],q['from_euler'](q['END']))<1e-12
    assert max(abs(sum(x*x for x in quat)-1) for quat in path)<1e-12
increments=[q['distance'](a,b) for a,b in zip(paths[1],paths[1][1:])]
assert max(increments)-min(increments)<1e-12
for u in (0.,.2,.5,.8,1.):
    a=q['from_euler'](q['START']);b=q['from_euler'](q['END'])
    assert q['distance'](q['slerp'](a,b,u),q['slerp'](a,tuple(-x for x in b),u))<1e-12
# Explicit identical/nearly identical endpoint tests exercise the normalized-lerp fallback.
a=q['from_euler']((.2,-.3,.4))
for b in (a,q['from_euler']((.20001,-.29998,.39997))):
    assert sum(x*y for x,y in zip(a,b))>.9995
    for u in (0.,.2,.5,.8,1.):
        blend=tuple((1-u)*x+u*y for x,y in zip(a,b))
        norm=sum(x*x for x in blend)**.5
        oracle=tuple(x/norm for x in blend)
        actual=q['slerp'](a,b,u)
        assert max(abs(x-y) for x,y in zip(actual,oracle))<1e-12
        assert abs(sum(x*x for x in actual)-1)<1e-12
        assert q['distance'](actual,q['slerp'](a,tuple(-x for x in b),u))<1e-12
# Independent exact norm-growth law for first-order qdot integration at constant body rate.
expected_norm_drift=(1+.01**2*(.4**2+.2**2+.6**2)/4)**(100/2)-1
assert abs(expected_norm_drift-.000700240)<.5e-9
print('independent shared-scan ICP, finite-difference plane rows, re-associated corridor null, direct ZYX/body-Jacobian, pole rank and equal-endpoint signed-slerp tests passed')
