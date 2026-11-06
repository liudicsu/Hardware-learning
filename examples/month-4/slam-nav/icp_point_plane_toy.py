#!/usr/bin/env python3
"""2D ICP surface surrogate, not Open3D/KITTI/SLAM Toolbox measurements.
Target scan vertices are connected polylines; BOTH arms use the same nearest
segment projection, not hidden true point indices. Normals come from those
same noisy segments. Point-point freezes projected q for a rigid increment;
point-plane linearizes normal residuals. This is not Open3D's discrete NN backend.
Corridor diagnostics REASSOCIATE projections: frozen point-point matches can
appear full rank while physical wall sliding is unobservable for BOTH arms.
"""
from math import atan2, cos, sin, sqrt, hypot, pi, radians, degrees
from random import Random
from statistics import mean, pstdev

SEEDS=(11,23,37,53,71)
OFFSETS=(-120,-60,-30,0,30,60,120)
CAP, STOP_RMSE=40,.012
TRUE=(.15,.12,-.07)  # source->target theta(rad), tx(m), ty(m); SCORE ONLY.
VERTICES=((-1.4,-.8),(1.1,-.8),(1.1,.45),(.25,.45),(.25,1.2),(-.9,1.2),(-1.4,.2))


def transform(point, pose):
    a,tx,ty=pose;c,s=cos(a),sin(a);x,y=point
    return c*x-s*y+tx,s*x+c*y+ty


def compose(pose, delta):
    dx,dy,da=delta
    tx,ty=transform((pose[1],pose[2]),(da,dx,dy))
    return pose[0]+da,tx,ty


def segments(vertices):
    return tuple(zip(vertices,vertices[1:]+vertices[:1]))


def nearest(point, target):
    best=None
    for a,b in target:
        vx,vy=b[0]-a[0],b[1]-a[1];den=vx*vx+vy*vy
        u=max(0.,min(1.,((point[0]-a[0])*vx+(point[1]-a[1])*vy)/den))
        q=(a[0]+u*vx,a[1]+u*vy)
        d=(point[0]-q[0])**2+(point[1]-q[1])**2
        if best is None or d<best[0]:best=(d,q,(-vy/sqrt(den),vx/sqrt(den)))
    return best


def correspondences(source, target, pose):
    return tuple((x,*nearest(x,target)[1:]) for x in (transform(p,pose) for p in source))


def rmse(source, target, pose):
    return sqrt(mean(nearest(transform(p,pose),target)[0] for p in source))


def solve3(a,b):
    scale=max(abs(x) for row in a for x in row)
    rows=[list(row)+[v] for row,v in zip(a,b)]
    for j in range(3):
        pivot=max(range(j,3),key=lambda i:abs(rows[i][j]))
        if abs(rows[pivot][j])<=1e-10*max(scale,1e-30):return None
        rows[j],rows[pivot]=rows[pivot],rows[j]
        factor=rows[j][j];rows[j]=[v/factor for v in rows[j]]
        for i in range(3):
            if i!=j:
                factor=rows[i][j];rows[i]=[x-factor*y for x,y in zip(rows[i],rows[j])]
    return tuple(row[3] for row in rows)


def normal_matrix(rows):
    return [[sum(row[i]*row[j] for row in rows) for j in range(3)] for i in range(3)]


def increment(matches,arm):
    if arm=='point_point':
        xc=tuple(mean(x[j] for x,_,_ in matches) for j in range(2))
        qc=tuple(mean(q[j] for _,q,_ in matches) for j in range(2))
        cross=sum((x[0]-xc[0])*(q[1]-qc[1])-(x[1]-xc[1])*(q[0]-qc[0]) for x,q,_ in matches)
        dot=sum((x[0]-xc[0])*(q[0]-qc[0])+(x[1]-xc[1])*(q[1]-qc[1]) for x,q,_ in matches)
        angle=atan2(cross,dot);rx,ry=transform(xc,(angle,0.,0.))
        return qc[0]-rx,qc[1]-ry,angle
    rows=[(n[0],n[1],-n[0]*x[1]+n[1]*x[0]) for x,_,n in matches]
    residual=[n[0]*(x[0]-q[0])+n[1]*(x[1]-q[1]) for x,q,n in matches]
    return solve3(normal_matrix(rows),[-sum(row[j]*v for row,v in zip(rows,residual)) for j in range(3)])


def fit(source,target,initial,arm):
    pose=initial
    for step in range(CAP+1):
        error=rmse(source,target,pose)
        if error<=STOP_RMSE or step==CAP:return pose,error,step
        delta=increment(correspondences(source,target,pose),arm)
        if delta is None:return pose,error,step
        # Same synthetic trust bounds for BOTH update rules: .35rad / .5m per step.
        factor=min(1.,.35/max(abs(delta[2]),1e-30),.5/max(hypot(*delta[:2]),1e-30))
        pose=compose(pose,tuple(factor*x for x in delta))
    raise AssertionError('unreachable')


def make_case(seed, offset):
    rng=Random(seed)
    target=segments(tuple((x+rng.gauss(0,.004),y+rng.gauss(0,.004)) for x,y in VERTICES))
    source=[]
    for a,b in segments(VERTICES):
        for j in range(6):
            u=(j+.5)/6;x=a[0]+u*(b[0]-a[0]);y=a[1]+u*(b[1]-a[1])
            px,py=transform((x-TRUE[1],y-TRUE[2]),(-TRUE[0],0.,0.))
            source.append((px+rng.gauss(0,.004),py+rng.gauss(0,.004)))
    initial=(TRUE[0]+radians(offset)+rng.uniform(-.005,.005),TRUE[1]+.10+rng.uniform(-.01,.01),TRUE[2]-.08+rng.uniform(-.01,.01))
    return tuple(source),target,initial


def hit(pose):
    angle=abs((pose[0]-TRUE[0]+pi)%(2*pi)-pi)
    return angle<=.03 and hypot(pose[1]-TRUE[1],pose[2]-TRUE[2])<=.03


def eigenvalues(a):
    a=[list(row) for row in a]
    for _ in range(40):
        p,q=max(((0,1),(0,2),(1,2)),key=lambda ij:abs(a[ij[0]][ij[1]]))
        if abs(a[p][q])<1e-13:break
        tau=(a[q][q]-a[p][p])/(2*a[p][q]);t=(1 if tau>=0 else -1)/(abs(tau)+sqrt(1+tau*tau))
        c=1/sqrt(1+t*t);s=t*c;apq=a[p][q]
        a[p][p]-=t*apq;a[q][q]+=t*apq;a[p][q]=a[q][p]=0.
        for k in range(3):
            if k not in (p,q):
                x,y=a[k][p],a[k][q];a[k][p]=a[p][k]=c*x-s*y;a[k][q]=a[q][k]=s*x+c*y
    return tuple(sorted(a[i][i] for i in range(3)))


def conditioning(matrix):
    ev=eigenvalues(matrix);threshold=max(abs(x) for x in ev)*1e-7
    rank=sum(x>threshold for x in ev)
    return rank,('inf' if rank<3 else f'{ev[-1]/ev[0]:.3f}')


def corridor():
    source=tuple((x,y) for x in (-1.5,-1.,-.5,0.,.5,1.,1.5) for y in (-1.,1.))
    target=(((-100.,-1.),(100.,-1.)),((-100.,1.),(100.,1.)))
    # Hessian of freshly REASSOCIATED mean squared Euclidean distance.
    h=1e-4
    def cost(v):return rmse(source,target,(v[2],v[0],v[1]))**2
    zero=(0.,0.,0.);base=cost(zero);H=[[0.]*3 for _ in range(3)]
    for i in range(3):
        plus=[0.]*3;plus[i]=h;minus=[-x for x in plus]
        H[i][i]=(cost(plus)-2*base+cost(minus))/(h*h)
        for j in range(i):
            vals=[]
            for si,sj in ((1,1),(1,-1),(-1,1),(-1,-1)):
                v=[0.]*3;v[i]=si*h;v[j]=sj*h;vals.append(cost(v))
            H[i][j]=H[j][i]=(vals[0]-vals[1]-vals[2]+vals[3])/(4*h*h)
    return source,target,H


def main():
    print('ICP 2D nearest-segment surface surrogate; no true correspondence IDs supplied')
    print('seeds=11/23/37/53/71 shared scans/noise/init per offset; sigma=0.004m cap=40 stop_RMSE=0.012m')
    print('same trust bounds .35rad/.5m; hit uses SCORE-ONLY true pose <=0.03rad and <=0.03m')
    print('offset_deg arm pose_hit/5 geometric_RMSE_mean_sd_m iterations_mean_sd')
    for offset in OFFSETS:
        cases=tuple(make_case(seed,offset) for seed in SEEDS)
        for arm in ('point_point','point_plane'):
            results=[fit(*case,arm) for case in cases]
            errors=[row[1] for row in results];steps=[row[2] for row in results]
            print(f'{offset} {arm} {sum(hit(row[0]) for row in results)}/5 {mean(errors):.6f} {pstdev(errors):.6f} {mean(steps):.2f} {pstdev(steps):.2f}')
    source,target,H=corridor()
    print('corridor: two parallel walls, no visible ends; dx(m),dy(m),dtheta(rad) parameter scaling')
    for arm in ('point_point','point_plane'):
        rank,cond=conditioning(H)
        print(f'{arm} reassociated_H_rank={rank}/3 condition={cond} null=along_wall_dx shifted_1m_RMSE={rmse(source,target,(0.,1.,0.)):.6f}')
    matches=correspondences(source,target,(0.,0.,0.))
    frozen=normal_matrix([row for (x,y),_,_ in matches for row in ((1,0,-y),(0,1,x))])
    rank,cond=conditioning(frozen)
    print(f'point_point FROZEN-match normal rank={rank}/3 condition={cond}; artificial tangent anchoring != scene observability')
    print('No presumed winner; basin means sampled offsets only; population sd, not wall-clock speed')
    print('Open3D / real lidar / SLAM Toolbox registration: 本页未运行')


if __name__=='__main__':main()
