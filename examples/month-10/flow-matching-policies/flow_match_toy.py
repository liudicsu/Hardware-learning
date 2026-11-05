"""flow_match_toy.py: 1-D flow matching with a closed-form velocity (stdlib).

Target: a bimodal mixture 0.5*N(-1, 0.1^2) + 0.5*N(+1, 0.1^2) — think of it as
"go left of the obstacle" vs "go right". Path (pi0 convention):

    x_tau = tau * x1 + (1 - tau) * eps,   eps ~ N(0, 1),   tau in [0, 1]
    target velocity u = x1 - eps

Because the target is a Gaussian mixture, the *marginal* velocity
E[x1 - eps | x_tau = x] has a closed form, so no network is trained here.
We integrate it with forward Euler from tau=0 (noise) to tau=1 and count how
many samples land near a mode vs near the (invalid) mean 0.

This is a toy: a real policy learns v_theta(A_tau, obs) with a network.
"""

import math
import random

SEED = 7
N = 2000
MODES = (-1.0, 1.0)
SIGMA = 0.1
STEPS = (1, 2, 3, 5, 10, 50)
NEAR = 0.3  # "near" radius for both mode and mean


def gauss(rng: random.Random) -> float:
    """Box-Muller from rng.random() so the stream is stable across versions."""
    u1 = rng.random()
    u2 = rng.random()
    return math.sqrt(-2.0 * math.log(1.0 - u1)) * math.cos(2.0 * math.pi * u2)


def velocity(x: float, tau: float) -> float:
    """Closed-form marginal velocity E[x1 - eps | x_tau = x] for the mixture."""
    var = tau * tau * SIGMA * SIGMA + (1.0 - tau) ** 2
    cov = tau * SIGMA * SIGMA - (1.0 - tau)  # Cov(x1 - eps, x_tau | mode)
    logw = [-(x - tau * m) ** 2 / (2.0 * var) for m in MODES]
    top = max(logw)
    w = [math.exp(v - top) for v in logw]
    z = sum(w)
    return sum(
        (wk / z) * (m + cov / var * (x - tau * m)) for wk, m in zip(w, MODES)
    )


def sample(x0: float, steps: int) -> float:
    x = x0
    dt = 1.0 / steps
    for k in range(steps):
        x = x + dt * velocity(x, k * dt)
    return x


def main() -> None:
    rng = random.Random(SEED)
    noise = [gauss(rng) for _ in range(N)]
    print(f"target: 0.5*N(-1,{SIGMA}^2) + 0.5*N(+1,{SIGMA}^2)  samples={N}  seed={SEED}")
    print(f"v(x=0.50, tau=0.0) = {velocity(0.5, 0.0):+.3f}   (= mean(x1) - x)")
    print(f"v(x=0.50, tau=0.9) = {velocity(0.5, 0.9):+.3f}   (points to the +1 mode)")
    print(f"{'steps':>5} {'near_mode':>9} {'near_mean':>9} {'mean_abs':>8}")
    for steps in STEPS:
        xs = [sample(x0, steps) for x0 in noise]
        near_mode = sum(1 for x in xs if abs(abs(x) - 1.0) < NEAR) / N
        near_mean = sum(1 for x in xs if abs(x) < NEAR) / N
        mean_abs = sum(abs(x) for x in xs) / N
        print(f"{steps:>5} {near_mode:>9.3f} {near_mean:>9.3f} {mean_abs:>8.3f}")
    print("1 Euler step lands every sample on the mean (an action between the modes);")
    print("more steps recover both modes. pi0 uses 10 steps (delta = 0.1).")


if __name__ == "__main__":
    main()
