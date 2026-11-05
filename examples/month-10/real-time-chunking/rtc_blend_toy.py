"""rtc_blend_toy.py: chunk seam, naive switch vs soft-mask blend (stdlib).

Simplified LINEAR stand-in for real-time chunking (RTC, arXiv 2506.07339).
Real RTC puts the soft mask W inside a guidance term during flow-matching
denoising (a vector-Jacobian product, clipped by beta). Here we skip the
network and apply W directly as a post-hoc blend:

    blended[i] = W[i] * prev_left[i] + (1 - W[i]) * fresh[i]

W follows Eq. 5 of the RTC paper:
    W[i] = 1                              if i < d
    W[i] = c * (e^c - 1) / (e - 1)        if d <= i < H - s,  c = (H-s-i)/(H-s-d+1)
    W[i] = 0                              if i >= H - s

H = prediction horizon, s = actions executed from the previous chunk before
this inference started, d = inference delay in control steps.
"""

import math

H = 16
S = 8
DELAYS = (0, 2, 4)


def prev_chunk() -> list[float]:
    """Old plan: a steady ramp (rad), 0.05 per step."""
    return [0.05 * k for k in range(H)]


def fresh_chunk() -> list[float]:
    """New plan from a newer observation: a different 'strategy' (lower, slower)."""
    return [0.20 + 0.03 * i for i in range(H)]


def soft_mask(d: int) -> list[float]:
    w = []
    for i in range(H):
        if i < d:
            w.append(1.0)
        elif i < H - S:
            c = (H - S - i) / (H - S - d + 1)
            w.append(c * (math.exp(c) - 1.0) / (math.e - 1.0))
        else:
            w.append(0.0)
    return w


def executed(d: int, use_blend: bool) -> list[float]:
    """Last executed old action, then what the robot actually plays next."""
    prev = prev_chunk()
    left = prev[S:] + [0.0] * S  # right-pad to length H (paper: Algorithm 1)
    fresh = fresh_chunk()
    w = soft_mask(d) if use_blend else [1.0 if i < d else 0.0 for i in range(H)]
    new = [w[i] * left[i] + (1.0 - w[i]) * fresh[i] for i in range(H)]
    # actions 0..d-1 run from the old chunk while inference is in flight
    return [prev[S - 1]] + left[:d] + new[d:]


def stats(seq: list[float]) -> tuple[float, float]:
    steps = [abs(b - a) for a, b in zip(seq, seq[1:])]
    acc = [abs(seq[k + 1] - 2 * seq[k] + seq[k - 1]) for k in range(1, len(seq) - 1)]
    return max(steps), max(acc)


def main() -> None:
    print(f"H={H} s={S}  prev ramp 0.05/step, fresh = 0.20 + 0.03*i (other strategy)")
    print(f"{'d':>2} {'mode':<6} {'max_step':>8} {'max_acc':>8} {'tail=fresh':>10}")
    for d in DELAYS:
        for mode in ("naive", "blend"):
            seq = executed(d, mode == "blend")
            mstep, macc = stats(seq)
            tail_ok = all(
                abs(seq[1 + i] - fresh_chunk()[i]) < 1e-12 for i in range(H - S, H)
            )
            print(f"{d:>2} {mode:<6} {mstep:>8.3f} {macc:>8.3f} {str(tail_ok):>10}")
    w = soft_mask(2)
    print("W (d=2): " + " ".join(f"{v:.2f}" for v in w))
    print("naive jumps once at the seam; the blend spreads it over the overlap,")
    print("and the last s actions still follow the fresh chunk.")


if __name__ == "__main__":
    main()
