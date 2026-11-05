#!/usr/bin/env python3
"""Planar floating-base velocity projection, not a dynamic WBC controller.
q=(xb,zb,theta_b,q1,q2,q3): three base + three leg DOFs, no arm.
Two-row point-position Jc permits foot rotation. Jc*qdot=0 is no-slip;
rank alone never enforces it. Base translation columns keep full Jc rank 2.
Force-only point screen omits moments; it does NOT certify a nonzero wrench
for an ideal point foot. Finite sole adds a CoP test on the SAME demand.
All forces/CoM are synthetic. No humanoid, MoCap or simulator is run.
"""
import math
import random

SEED = 31
LENGTHS = (0.35, 0.35, 0.12)


def kinematics(q):
    angles = [q[2] + sum(q[3:4 + i]) for i in range(3)]
    dx = [l * math.cos(a) for l, a in zip(LENGTHS, angles)]
    dz = [l * math.sin(a) for l, a in zip(LENGTHS, angles)]
    # Segment direction = (sin(a), -cos(a)); angle zero points down.
    point = [q[0] + sum(l * math.sin(a) for l, a in zip(LENGTHS, angles)),
             q[1] - sum(l * math.cos(a) for l, a in zip(LENGTHS, angles))]
    j = [[1.0, 0.0, sum(dx)] + [sum(dx[i:]) for i in range(3)],
         [0.0, 1.0, sum(dz)] + [sum(dz[i:]) for i in range(3)]]
    return point, j


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def norm(v):
    return math.sqrt(dot(v, v))


def spectrum(rows):
    a, b, c = dot(rows[0], rows[0]), dot(rows[0], rows[1]), dot(rows[1], rows[1])
    disc = math.hypot(a - c, 2 * b)
    s = [math.sqrt(max(0.0, (a + c + disc) / 2)),
         math.sqrt(max(0.0, (a + c - disc) / 2))]
    return sum(x > 1e-8 for x in s), s


def projector(j):
    # Full-row-rank right inverse: J+ = J^T (J J^T)^-1.
    a, b, c = dot(j[0], j[0]), dot(j[0], j[1]), dot(j[1], j[1])
    det = a * c - b * b
    assert det > 1e-12
    jp = [[(j[0][i] * c - j[1][i] * b) / det,
           (j[1][i] * a - j[0][i] * b) / det] for i in range(6)]
    return [[float(i == k) - sum(jp[i][r] * j[r][k] for r in range(2))
             for k in range(6)] for i in range(6)]


def main():
    rng = random.Random(SEED)
    q = [0.0, 0.8, 0.12, -0.3, 0.6, -0.2]
    _, j = kinematics(q)
    n = projector(j)
    jn = max(abs(sum(j[r][i] * n[i][k] for i in range(6)))
             for r in range(2) for k in range(6))
    # Central finite-difference check of all columns, not only translations.
    fd_err = 0.0
    for k in range(6):
        hi, lo = q[:], q[:]
        hi[k] += 1e-6
        lo[k] -= 1e-6
        ph, _ = kinematics(hi)
        pl, _ = kinematics(lo)
        fd_err = max(fd_err, *(abs((ph[r] - pl[r]) / 2e-6 - j[r][k]) for r in range(2)))
    raw = [rng.uniform(-0.3, 0.3) for _ in range(6)]
    projected = [dot(row, raw) for row in n]
    pitch_target = -2 * q[2]  # secondary base-pitch regulation, rad/s
    gain = (pitch_target - projected[2]) / n[2][2]
    velocity = [projected[i] + n[i][2] * gain for i in range(6)]
    rc = norm([dot(row, velocity) for row in j])
    pitch_err = abs(velocity[2] - pitch_target)
    rank, sigma = spectrum(j)
    straight = kinematics([0.0, 0.82, 0.0, 0.0, 0.0, 0.0])[1]
    straight_rank, _ = spectrum(straight)
    leg_rank, _ = spectrum([row[3:] for row in straight])
    assert jn < 1e-12 and rc < 1e-12 and pitch_err < 1e-12 and fd_err < 1e-8
    assert rank == straight_rank == 2 and leg_rank == 1

    # Shared synthetic CoM/wrench demand; no full inverse-dynamics solution.
    mass, height, mu, sole_half = 20.0, 0.8, 0.6, 0.10
    point_pass, sole_pass, max_cop = 0, 0, 0.0
    for k in range(201):
        t = 2 * math.pi * k / 200
        x = 0.14 * math.sin(2 * t)
        ax = -4 * x
        fx, fz = mass * ax, mass * 9.81
        cop = x - height * ax / 9.81  # zero centroidal angular-momentum rate
        # About the foot origin the demanded moment is -fz*cop.
        force_ok = fz > 0 and abs(fx) <= mu * fz
        sole_ok = force_ok and abs(cop) <= sole_half
        point_pass += int(force_ok)
        sole_pass += int(sole_ok)
        max_cop = max(max_cop, abs(cop))
    assert point_pass == 201 and 0 < sole_pass < point_pass
    print(f"seed={SEED} dofs=6 contact_rows=2 no_arm=True")
    print(f"Jc_rank={rank} sigma_max={sigma[0]:.6f} sigma_min={sigma[1]:.6f}")
    print(f"raw_contact_speed={norm([dot(row, raw) for row in j]):.6f}")
    print(f"contact_residual={rc:.3f} JcN_max={jn:.3f} pitch_rate_error={pitch_err:.3f}")
    print(f"jacobian_fd_ok={fd_err < 1e-8} nullspace_ok={jn < 1e-12}")
    print(f"straight_full_rank={straight_rank} straight_joint_only_rank={leg_rank}")
    print(f"point_force_screen={point_pass}/201 finite_sole_screen={sole_pass}/201")
    print(f"max_abs_cop_m={max_cop:.6f} sole_half_m={sole_half:.2f}")
    print("point_screen_omits_moment=True full_dynamic_feasibility_not_tested=True")


if __name__ == "__main__":
    main()
