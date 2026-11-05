"""int8_quant_toy.py: 8-bit linear quantisation by hand (stdlib).

Formulas follow the ONNX Runtime quantisation docs:
    val_fp32 = scale * (val_quantized - zero_point)
    asymmetric: scale = (max - min) / (qmax - qmin)
    symmetric:  scale = max(|max|, |min|) * 2 / (qmax - qmin)

Symmetric int8 here uses the range -127..127 (zero_point = 0); asymmetric
uint8 uses 0..255. The range is widened to include 0 so that 0.0 is exactly
representable. A 4 x 16 weight matrix (4 output channels) is quantised
per-tensor (one scale) and per-channel (one scale per row). One outlier in
channel 1 shows why a single large value hurts every weight that shares its
scale.
"""

import random

SEED = 3
ROWS, COLS = 4, 16


def weights(with_outlier: bool) -> list[list[float]]:
    rng = random.Random(SEED)
    w = [[round(rng.uniform(-0.5, 0.5), 4) for _ in range(COLS)] for _ in range(ROWS)]
    if with_outlier:
        w[1][5] = 4.0
    return w


def sym_params(xs: list[float]) -> tuple[float, int, int, int]:
    qmin, qmax = -127, 127
    scale = max(abs(max(xs)), abs(min(xs))) * 2 / (qmax - qmin)
    return scale, 0, qmin, qmax


def asym_params(xs: list[float]) -> tuple[float, int, int, int]:
    qmin, qmax = 0, 255
    lo, hi = min(min(xs), 0.0), max(max(xs), 0.0)
    scale = (hi - lo) / (qmax - qmin)
    zp = max(qmin, min(qmax, round(qmin - lo / scale)))
    return scale, zp, qmin, qmax


def roundtrip(xs: list[float], params: tuple[float, int, int, int]) -> list[float]:
    scale, zp, qmin, qmax = params
    q = [max(qmin, min(qmax, round(x / scale) + zp)) for x in xs]
    return [scale * (v - zp) for v in q]


def run(w: list[list[float]], scheme: str) -> tuple[float, float, float, bool]:
    flat = [x for row in w for x in row]
    back: list[float] = []
    scales: list[float] = []
    if scheme == "per-channel":
        for row in w:
            p = sym_params(row)
            scales.append(p[0])
            back += roundtrip(row, p)
    else:
        p = sym_params(flat) if scheme == "sym tensor" else asym_params(flat)
        scales = [p[0]] * ROWS
        back = roundtrip(flat, p)
    errs = [abs(a - b) for a, b in zip(flat, back)]
    ch0 = errs[:COLS]
    bound = all(
        e <= scales[i // COLS] / 2 + 1e-12 for i, e in enumerate(errs)
    )
    mse = sum(e * e for e in errs) / len(errs)
    return scales[0], max(ch0), mse, bound


def main() -> None:
    print(f"{ROWS}x{COLS} weights, seed={SEED}, uniform(-0.5, 0.5); outlier case sets w[1][5]=4.0")
    print(f"{'case':<8} {'scheme':<12} {'scale_ch0':>9} {'ch0_max_err':>11} {'mse':>10} {'<=scale/2':>9}")
    for case, flag in (("plain", False), ("outlier", True)):
        w = weights(flag)
        for scheme in ("sym tensor", "asym tensor", "per-channel"):
            s0, e0, mse, bound = run(w, scheme)
            print(f"{case:<8} {scheme:<12} {s0:>9.5f} {e0:>11.5f} {mse:>10.2e} {str(bound):>9}")
    params = 100_000_000
    print(f"weight bytes for {params // 1_000_000}M params (weights only, no activations):")
    for name, nbytes in (("fp32", 4), ("bf16", 2), ("int8", 1)):
        print(f"  {name:<5} {params * nbytes / 1e6:>6.0f} MB")


if __name__ == "__main__":
    main()
