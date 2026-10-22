"""kinematics.py: forward kinematics, numerical inverse kinematics and singularities.

A three-joint arm with the first three joints of an SO-101 (base yaw q0 = shoulder_pan about the
vertical axis, then a shoulder q1 = shoulder_lift and an elbow q2 = elbow_flex that both pitch in the
arm's vertical plane), with the SO-101's axis-to-axis distances from the SO-ARM100 URDF
(TheRobotStudio/SO-ARM100 @ a758567, Simulation/SO101/so101_new_calib.urdf):
  L1 = |(-0.11257, -0.028)|  = 0.1160 m, shoulder_lift -> elbow_flex (elbow_flex origin, line 395)
  L2 = |(-0.1349, 0.0052)|   = 0.1350 m, elbow_flex -> wrist_flex (wrist_flex origin, line 374)
  H  = 0.0624 + 0.0542       = 0.1166 m, base_link origin -> shoulder_lift axis (lines 435 and 415)
The tip is the wrist_flex axis. Left out: the shoulder axis sits 30.4 mm forward of and 18.3 mm beside
the base axis, the upper arm is bent by atan(0.028 / 0.11257) = 14.0 deg, and the joint zeros differ
from the real arm's. Angles in radians, q1 = q2 = 0 means the arm points straight out horizontally.
Standard library only.
"""
import math

H, L1, L2 = 0.1166, 0.1160, 0.1350


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def rot_y(a):          # positive a pitches the arm up (rotation about -y)
    c, s = math.cos(a), math.sin(a)
    return [[c, 0, -s, 0], [0, 1, 0, 0], [s, 0, c, 0], [0, 0, 0, 1]]


def trans(x, y, z):
    return [[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]]


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def fk(q):
    """Chain of transforms base -> shoulder -> elbow -> tip; returns the tip position."""
    t = mul(rot_z(q[0]), trans(0, 0, H))
    t = mul(t, mul(rot_y(q[1]), trans(L1, 0, 0)))
    t = mul(t, mul(rot_y(q[2]), trans(L2, 0, 0)))
    return [t[0][3], t[1][3], t[2][3]]


def jacobian(q, h=1e-6):
    """Numerical Jacobian: how the tip moves per radian of each joint (3 x 3)."""
    p = fk(q)
    cols = []
    for i in range(3):
        dq = list(q)
        dq[i] += h
        cols.append([(a - b) / h for a, b in zip(fk(dq), p)])
    return [[cols[j][i] for j in range(3)] for i in range(3)]


def det3(m):
    return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))


def solve3(a, b):
    """Solve a x = b by Cramer's rule (3 x 3)."""
    d = det3(a)
    out = []
    for i in range(3):
        m = [row[:] for row in a]
        for r in range(3):
            m[r][i] = b[r]
        out.append(det3(m) / d)
    return out


def dls_step(q, err, lam):
    """Damped least squares: dq = J' (J J' + lam^2 I)^-1 err."""
    j = jacobian(q)
    jjt = [[sum(j[r][k] * j[c][k] for k in range(3)) + (lam * lam if r == c else 0) for c in range(3)] for r in range(3)]
    y = solve3(jjt, err)
    return [sum(j[k][i] * y[k] for k in range(3)) for i in range(3)]


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))        # back into -180 .. 180 degrees


def ik(target, q, lam=0.03, tol=1e-5, max_step=0.02, show=False):
    """Repeat small damped least-squares steps; each step aims at most max_step metres."""
    for it in range(200):
        p = fk(q)
        err = [t - c for t, c in zip(target, p)]
        dist = math.sqrt(sum(e * e for e in err))
        if show:
            print(f"  iter {it:2d}  q = [{', '.join(f'{math.degrees(v):7.2f}' for v in q)}] deg  error {1000 * dist:8.3f} mm")
        if dist < tol:
            break
        scale = min(1.0, max_step / dist)
        q = [wrap(a + b) for a, b in zip(q, dls_step(q, [e * scale for e in err], lam))]
    return q, it, dist


def show_fk():
    q = [math.radians(30), math.radians(45), math.radians(-60)]
    p = fk(q)
    r = L1 * math.cos(q[1]) + L2 * math.cos(q[1] + q[2])
    z = H + L1 * math.sin(q[1]) + L2 * math.sin(q[1] + q[2])
    print("Forward kinematics, q = [30, 45, -60] deg")
    print(f"  by hand: reach r = {r:.4f} m, height z = {z:.4f} m, x = r cos 30 = {r * math.cos(q[0]):.4f}, y = r sin 30 = {r * math.sin(q[0]):.4f}")
    print(f"  transforms: tip = ({p[0]:.4f}, {p[1]:.4f}, {p[2]:.4f}) m")


def show_ik():
    target = [0.10, 0.15, 0.12]
    print(f"Numerical IK to ({target[0]:.2f}, {target[1]:.2f}, {target[2]:.2f}) m from q = [0, 30, -30] deg")
    q, it, dist = ik(target, [0.0, math.radians(30), math.radians(-30)], show=True)
    p = fk(q)
    print(f"  check with FK: ({p[0]:.4f}, {p[1]:.4f}, {p[2]:.4f}) m")
    q2, it2, _ = ik(target, [0.0, math.radians(90), math.radians(60)])
    print(f"  from q = [0, 90, 60] deg instead: q = [{', '.join(f'{math.degrees(v):.2f}' for v in q2)}] deg after {it2} iterations (base turned round, reaching back over the top)")
    far = [0.20, 0.20, 0.10]
    q3, it3, d3 = ik(far, [0.0, math.radians(30), math.radians(-30)])
    out = math.sqrt(0.20 ** 2 + 0.20 ** 2 + (0.10 - H) ** 2)
    print(f"  to (0.20, 0.20, 0.10) m, {out:.3f} m from the shoulder but L1 + L2 = {L1 + L2:.2f} m: "
          f"stops {1000 * d3:.1f} mm short, elbow {round(math.degrees(q3[2]), 2) + 0.0:.2f} deg")
    q4, it4, d4 = ik(far, [0.0, math.radians(30), math.radians(-30)], lam=0.01)
    print(f"  same with lambda = 0.01: after {it4 + 1} iterations still {1000 * d4:.1f} mm short, elbow {math.degrees(q4[2]):.2f} deg (it never settles)")


def show_singular():
    print("Singularity: the elbow straightening, shoulder at 20 deg, base at 0")
    print("  elbow (deg)  det J (m^3)  joint speed for 0.05 m/s straight out (deg/s)")
    print("                            exact inverse        damped, lambda = 0.03")
    for e in (-60, -30, -10, -3, -1, -0.3):
        q = [0.0, math.radians(20), math.radians(e)]
        j = jacobian(q)
        d = det3(j)
        p = fk(q)
        r = math.hypot(p[0], p[1])
        v = [0.05 * p[0] / r, 0.05 * p[1] / r, 0.0]          # radial, horizontal
        exact = max(abs(math.degrees(x)) for x in solve3(j, v))
        damped = max(abs(math.degrees(x)) for x in dls_step(q, v, 0.03))
        print(f"  {e:10.1f}  {d:11.2e}  {exact:18.1f}  {damped:22.1f}")
    print("  formula: |det J| = L1 x L2 x r x |sin(elbow)|, r = the tip's horizontal reach")


if __name__ == "__main__":
    show_fk()
    print()
    show_ik()
    print()
    show_singular()
