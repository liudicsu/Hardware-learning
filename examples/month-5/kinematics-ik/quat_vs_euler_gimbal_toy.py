#!/usr/bin/env python3
"""Synthetic ATTITUDE chart experiment, not the arm's position Jacobian.
Active intrinsic ZYX yaw-pitch-roll: R=Rz(yaw) Ry(pitch) Rx(roll), column vectors.
Body omega = J(roll,pitch) * [roll_dot,pitch_dot,yaw_dot]. Quaternion order w,x,y,z.
Shared orientation samples cross pitch90; shared interpolation endpoints/12steps.
Slerp flips dot<0 for the short arc; q/-q double cover and normalization matter.
"""
from math import sin, cos, asin, atan2, acos, sqrt, radians, degrees, pi
from statistics import mean, pstdev

N, DURATION=12,1.0
START=tuple(map(radians,(10.,80.,-50.)))  # roll,pitch,yaw; synthetic endpoints
END=tuple(map(radians,(-30.,100.,80.)))


def normalize(q):
    norm=sqrt(sum(x*x for x in q))
    return tuple(x/norm for x in q)


def multiply(a,b):
    w,x,y,z=a;v,i,j,k=b
    return (w*v-x*i-y*j-z*k,w*i+x*v+y*k-z*j,w*j-x*k+y*v+z*i,w*k+x*j-y*i+z*v)


def from_euler(rpy):
    r,p,y=(x/2 for x in rpy)
    return normalize(multiply(multiply((cos(y),0.,0.,sin(y)),(cos(p),0.,sin(p),0.)),(cos(r),sin(r),0.,0.)))


def to_euler(q):
    w,x,y,z=normalize(q)
    sine=max(-1.,min(1.,2*(w*y-z*x)))
    if abs(sine)>1-1e-12:
        R=matrix(q)
        return 0., (pi/2 if sine>0 else -pi/2), atan2(-R[0][1],R[1][1])
    return (atan2(2*(w*x+y*z),1-2*(x*x+y*y)),
            asin(sine),
            atan2(2*(w*z+x*y),1-2*(y*y+z*z)))


def matrix(q):
    w,x,y,z=normalize(q)
    return ((1-2*(y*y+z*z),2*(x*y-w*z),2*(x*z+w*y)),
            (2*(x*y+w*z),1-2*(x*x+z*z),2*(y*z-w*x)),
            (2*(x*z-w*y),2*(y*z+w*x),1-2*(x*x+y*y)))


def distance(a,b):
    # atan2 avoids acos precision loss near coincident rotations; sign-invariant.
    a=normalize(a);b=normalize(b)
    relative=multiply((a[0],-a[1],-a[2],-a[3]),b)
    return 2*atan2(sqrt(sum(x*x for x in relative[1:])),abs(relative[0]))


def slerp(a,b,u):
    a=normalize(a);b=normalize(b);dot=sum(x*y for x,y in zip(a,b))
    if dot<0:
        b=tuple(-x for x in b);dot=-dot
    dot=max(-1.,min(1.,dot))
    if dot>.9995:return normalize(tuple((1-u)*x+u*y for x,y in zip(a,b)))
    angle=acos(dot)
    return normalize(tuple((sin((1-u)*angle)*x+sin(u*angle)*y)/sin(angle) for x,y in zip(a,b)))


def rate_jacobian(roll,pitch):
    return ((1.,0.,-sin(pitch)),(0.,cos(roll),sin(roll)*cos(pitch)),(0.,-sin(roll),cos(roll)*cos(pitch)))


def rank(matrix):
    rows=[list(row) for row in matrix];pivot=0
    for column in range(3):
        chosen=max(range(pivot,3),key=lambda i:abs(rows[i][column]))
        if abs(rows[chosen][column])<1e-10:continue
        rows[pivot],rows[chosen]=rows[chosen],rows[pivot]
        divisor=rows[pivot][column];rows[pivot]=[x/divisor for x in rows[pivot]]
        for i in range(pivot+1,3):
            factor=rows[i][column];rows[i]=[a-factor*b for a,b in zip(rows[i],rows[pivot])]
        pivot+=1
        if pivot==3:break
    return pivot


def paths():
    a,b=from_euler(START),from_euler(END)
    fractions=tuple(j/N for j in range(N+1))
    euler=tuple(from_euler(tuple((1-u)*x+u*y for x,y in zip(START,END))) for u in fractions)
    spherical=tuple(slerp(a,b,u) for u in fractions)
    return euler,spherical


def main():
    print('Active intrinsic ZYX: Rz(yaw)Ry(pitch)Rx(roll); body omega=J*[roll_dot,pitch_dot,yaw_dot]')
    print('pitch_deg det_J rank condition2; +/-90 loses one attitude-chart direction, not arm mobility')
    for angle in (-90.,-89.9,-60.,0.,60.,89.9,90.):
        p=radians(angle);condition='inf' if abs(cos(p))<1e-10 else f'{(1+abs(sin(p)))/abs(cos(p)):.3f}'
        print(f'{angle:.1f} {abs(cos(p)):.9f} {rank(rate_jacobian(.3,p))}/3 {condition}')
    print('null roll/pitch/yaw rate: pitch+90 -> (1,0,1); pitch-90 -> (1,0,-1)')
    print('same pure-pitch sequence: intended_pitch canonical_roll canonical_pitch canonical_yaw roundtrip_rotation_error_deg')
    for angle in (80.,85.,89.,90.,91.,95.,100.):
        q=from_euler((0.,radians(angle),0.));canonical=to_euler(q)
        print(f'{angle:.1f} '+ ' '.join(f'{degrees(x):.3f}' for x in canonical)+f' {degrees(distance(q,from_euler(canonical))):.9f}')
    euler,spherical=paths()
    print('shared synthetic RPY endpoints=(10,80,-50)->(-30,100,80) deg; steps=12 duration=1s')
    print('arm angular_speed_mean_sd_min_max_deg_per_s sampled_path_length_deg net_rotation_deg')
    for arm,path in (('Euler_lerp',euler),('quaternion_slerp',spherical)):
        increments=[degrees(distance(a,b)) for a,b in zip(path,path[1:])]
        speed=[x*N/DURATION for x in increments]
        print(f'{arm} {mean(speed):.6f} {pstdev(speed):.6f} {min(speed):.6f} {max(speed):.6f} {sum(increments):.6f} {degrees(distance(path[0],path[-1])):.6f}')
    deviation=max(degrees(distance(a,b)) for a,b in zip(euler,spherical))
    print(f'max_same_time_rotation_difference_deg={deviation:.6f} (two paths, not a ground-truth error)')
    q=from_euler(END);negative=tuple(-x for x in q)
    discrepancy=max(abs(x-y) for row1,row2 in zip(matrix(q),matrix(negative)) for x,y in zip(row1,row2))
    # Negative endpoint chosen deliberately to exercise the dot<0 branch.
    a=from_euler(START);b=negative if sum(x*y for x,y in zip(a,negative))<0 else q
    flipped=max(degrees(distance(slerp(a,q,j/N),slerp(a,b,j/N))) for j in range(N+1))
    print(f'q_vs_minus_q_matrix_maxdiff={discrepancy:.9f} rotation_distance_deg={degrees(distance(q,negative)):.9f}')
    print(f'negative_dot_endpoint={int(sum(x*y for x,y in zip(a,b))<0)} flipped_slerp_max_rotation_diff_deg={flipped:.9f}')
    raw=normalized=(1.,0.,0.,0.)
    for _ in range(100):
        # First-order quaternion derivative integration, NOT angle interpolation.
        raw=tuple(x+.005*y for x,y in zip(raw,multiply(raw,(0.,.4,-.2,.6))))
        normalized=normalize(tuple(x+.005*y for x,y in zip(normalized,multiply(normalized,(0.,.4,-.2,.6)))))
    print(f'100x_dt0.01_qdot norm_drift_raw={sqrt(sum(x*x for x in raw))-1:.9f} normalized={abs(sqrt(sum(x*x for x in normalized))-1):.9f}')
    print('Slerp fallback near equal endpoints uses normalized lerp; no universal task-path winner')
    print('Synthetic orientation only; real robot/IMU/ROS execution: 本页未运行')


if __name__=='__main__':main()
