"""lqr_sim.py: state space, LQR on a cart-pole, and a small MPC on the Month 3 arm joint.

Part 1 writes a cart-pole (the Month 2 balancer reduced to its essentials: a cart that is
pushed by a force and a pole balanced on it) in state space, x = [position, speed, angle,
angular rate], linearised about upright, discretised at 100 Hz. LQR gains come from
iterating the discrete Riccati equation. The gains are then tested on the full nonlinear
cart-pole, with the force limited to 10 N.
Part 2 moves the arm joint from lesson 1 (J = 0.004, B = 0.05, gravity cancelled by
feedforward) through 1 rad with a torque limit, comparing LQR whose output is simply
clipped with an MPC that knows the limit. Standard library only.
"""
import math

# ---------------------------------------------------------------- small matrix helpers
def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]


def add(a, b, s=1.0):
    return [[a[i][j] + s * b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def tr(a):
    return [list(r) for r in zip(*a)]


def eye(n, v=1.0):
    return [[v if i == j else 0.0 for j in range(n)] for i in range(n)]


def discretise(a, b, dt):
    """Zero-order-hold discretisation by a Taylor series of the matrix exponential."""
    n = len(a)
    phi, gam, term = eye(n), [[dt * x[0]] for x in b], eye(n)
    for k in range(1, 25):
        term = [[v * dt / k for v in r] for r in mul(term, a)]           # (A dt)^k / k!
        phi = add(phi, term)
        gam = add(gam, [[v * dt / (k + 1)] for v in [r[0] for r in mul(term, b)]])
    return phi, gam


def lqr(phi, gam, q, r, iters=5000):
    """Iterate P = Q + A'PA - A'PB (R + B'PB)^-1 B'PA; return K for u = -K x."""
    p = q
    for _ in range(iters):
        bp = mul(tr(gam), p)
        s = r + mul(bp, gam)[0][0]
        k = [[v / s for v in mul(bp, phi)[0]]]
        p = add(q, mul(tr(phi), mul(p, add(phi, mul(gam, k), -1.0))))
    return k[0]


# ---------------------------------------------------------------- part 1: cart-pole
M, m, L, G, DT, FMAX = 0.5, 0.2, 0.3, 9.81, 0.01, 10.0
A_CP = [[0, 1, 0, 0], [0, 0, -m * G / M, 0], [0, 0, 0, 1], [0, 0, (M + m) * G / (M * L), 0]]
B_CP = [[0], [1 / M], [0], [-1 / (M * L)]]


def cartpole(x, f, dt=0.001):
    """Full nonlinear cart-pole (point mass m at distance L), angle from upright."""
    p, v, th, w = x
    s, c = math.sin(th), math.cos(th)
    acc = (f + m * L * w * w * s - m * G * s * c) / (M + m - m * c * c)
    alpha = (G * s - acc * c) / L
    return [p + v * dt, v + acc * dt, th + w * dt, w + alpha * dt]


def balance(k, deg, seconds=4.0, show=False):
    x = [0.0, 0.0, math.radians(deg), 0.0]
    fpeak = 0.0
    for i in range(int(seconds / DT)):
        f = max(-FMAX, min(FMAX, -sum(ki * xi for ki, xi in zip(k, x))))
        fpeak = max(fpeak, abs(f))
        if show and i % 50 == 0:
            print(f"  t = {i * DT:3.1f} s  x = {x[0]:6.3f} m  angle = {math.degrees(x[2]):6.2f} deg  force = {f:6.2f} N")
        for _ in range(10):
            x = cartpole(x, f)
        if abs(x[2]) > math.pi / 2:
            return None, fpeak
    return x, fpeak


def part1():
    phi, gam = discretise(A_CP, B_CP, DT)
    print("Cart-pole, x = [position, speed, angle, rate], 100 Hz")
    print("  A (continuous) rows:", "  ".join("[" + ", ".join(f"{v:.2f}" for v in r) + "]" for r in A_CP))
    print("  B (continuous):     ", "[" + ", ".join(f"{r[0]:.2f}" for r in B_CP) + "]")
    for name, qd, r in (("Q = diag(1, 1, 10, 1), R = 1   ", (1, 1, 10, 1), 1.0),
                        ("Q = diag(100, 1, 10, 1), R = 1 ", (100, 1, 10, 1), 1.0),
                        ("Q = diag(1, 1, 10, 1), R = 0.01", (1, 1, 10, 1), 0.01)):
        q = [[qd[i] if i == j else 0.0 for j in range(4)] for i in range(4)]
        k = lqr(phi, gam, q, r)
        print(f"{name}  K = [" + ", ".join(f"{v:7.2f}" for v in k) + "]")
        if name.startswith("Q = diag(1, 1, 10, 1), R = 1 "):
            k_first = k
        x, fpeak = balance(k, 10)
        print(f"    from 10 deg: after 4 s x = {x[0]:6.3f} m, angle = {math.degrees(x[2]):5.2f} deg, peak force {fpeak:5.2f} N")
    print("Nonlinear run with the first K, starting 10 deg off upright:")
    balance(k_first, 10, seconds=3.0, show=True)
    biggest = max(d for d in range(1, 90) if balance(k_first, d, seconds=6.0)[0] is not None
                  and abs(balance(k_first, d, seconds=6.0)[0][2]) < 0.01)
    print(f"  largest start angle it still recovers from (force limit {FMAX:.0f} N): {biggest} deg")


# ---------------------------------------------------------------- part 2: MPC on the joint
J, BV, T, UMAX, N = 0.004, 0.05, 0.005, 0.6, 40
PHI_J, GAM_J = discretise([[0, 1], [0, -BV / J]], [[0], [1 / J]], T)


def jstep(x, u):
    return [PHI_J[0][0] * x[0] + PHI_J[0][1] * x[1] + GAM_J[0][0] * u,
            PHI_J[1][0] * x[0] + PHI_J[1][1] * x[1] + GAM_J[1][0] * u]


def mpc(x, target, kq, warm):
    """Minimise sum over N steps of kq*(q-target)^2 + 0.01*w^2 + u^2, |u| <= UMAX,
    by projected gradient descent on the N future torques; return them all."""
    u = warm[1:] + warm[-1:]
    lr = 2e-4
    for _ in range(150):
        xs = [x]
        for uk in u:
            xs.append(jstep(xs[-1], uk))
        lam = [0.0, 0.0]                  # backward pass: gradient of the cost wrt each u
        grad = [0.0] * N
        for k in range(N - 1, -1, -1):
            q, w = xs[k + 1]
            lam = [2 * kq * (q - target) + PHI_J[0][0] * lam[0] + PHI_J[1][0] * lam[1],
                   2 * 0.01 * w + PHI_J[0][1] * lam[0] + PHI_J[1][1] * lam[1]]
            grad[k] = 2 * u[k] + GAM_J[0][0] * lam[0] + GAM_J[1][0] * lam[1]
        u = [max(-UMAX, min(UMAX, uk - lr * g)) for uk, g in zip(u, grad)]
    return u


def move(kind, seconds=1.0):
    k = lqr(PHI_J, GAM_J, [[400.0, 0], [0, 0.01]], 1.0)
    x, target, peak, settle = [0.0, 0.0], 1.0, 0.0, None
    plan = [0.0] * N
    sat = 0
    for i in range(int(seconds / T)):
        if kind == "lqr":
            u = max(-UMAX, min(UMAX, -(k[0] * (x[0] - target) + k[1] * x[1])))
        else:
            plan = mpc(x, target, 400.0, plan)
            u = plan[0]
        sat += abs(u) >= UMAX - 1e-9
        x = jstep(x, u)
        peak = max(peak, x[0])
        if abs(x[0] - target) > math.radians(1):
            settle = None
        elif settle is None:
            settle = (i + 1) * T
    return k, peak, settle, sat * T


def part2():
    print(f"Arm joint, 1 rad move, |torque| <= {UMAX} N*m (on top of gravity feedforward), 200 Hz")
    for kind, label in (("lqr", "LQR, output clipped"), ("mpc", f"MPC, horizon {N} steps")):
        k, peak, settle, sat = move(kind)
        if kind == "lqr":
            print(f"  LQR gains: K = [{k[0]:.2f}, {k[1]:.3f}]  (kp in N*m/rad, kd in N*m/(rad/s))")
        s = f"{settle:.3f} s" if settle else "never"
        print(f"  {label:22s} overshoot {math.degrees(peak - 1.0):5.2f} deg, within 1 deg from {s}, at the limit for {sat:.3f} s")


if __name__ == "__main__":
    part1()
    print()
    part2()
