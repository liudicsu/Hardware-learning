"""action_tokens.py: how a VLA turns robot actions into tokens, per-step bins versus a DCT of the whole chunk.

A language model outputs tokens, so an autoregressive VLA needs a way to write actions as tokens. Two schemes:
  bins  (RT-2, OpenVLA): each action dimension at each step becomes one of 256 tokens, bins spread evenly
        between that dimension's 1st and 99th percentile over the dataset.
  DCT   (the idea behind FAST, used by pi0-FAST): normalise each dimension to -1..1 with the same percentiles,
        take a discrete cosine transform of each dimension over the chunk, multiply by a scale and round.
        Smooth motion puts almost everything into a few low-frequency coefficients; the rest round to zero.
        (FAST then compresses the integers with byte-pair encoding; this program counts nonzero coefficients.)
The actions are synthetic but shaped like a teleoperated SO-101: 6 joint targets in degrees at 30 Hz, chunks of
1 s (30 steps). Standard library only, fixed seeds.
"""
import math
import random

HZ, CHUNK, JOINTS, BINS = 30, 30, 6, 256


def episode(rng, seconds=10):
    """Smooth joint targets: a few slow sine components per joint, like a person moving a leader arm."""
    comps = [[(rng.uniform(5, 40), rng.uniform(0.1, 0.8), rng.uniform(0, 2 * math.pi)) for _ in range(3)]
             for _ in range(JOINTS)]
    offset = [rng.uniform(-30, 30) for _ in range(JOINTS)]
    return [[offset[j] + sum(a * math.sin(2 * math.pi * f * t / HZ + ph) for a, f, ph in comps[j])
             for j in range(JOINTS)] for t in range(seconds * HZ)]


def percentile(values, q):
    v = sorted(values)
    k = (len(v) - 1) * q
    lo = int(k)
    return v[lo] + (v[min(lo + 1, len(v) - 1)] - v[lo]) * (k - lo)


def to_bins(x, lo, hi):
    u = (min(max(x, lo), hi) - lo) / (hi - lo)
    return min(int(u * BINS), BINS - 1)


def from_bins(token, lo, hi):
    return lo + (token + 0.5) * (hi - lo) / BINS


def dct(x):
    """DCT-II with orthonormal scaling."""
    n = len(x)
    return [math.sqrt((1 if k == 0 else 2) / n) * sum(x[i] * math.cos(math.pi * k * (2 * i + 1) / (2 * n))
                                                      for i in range(n)) for k in range(n)]


def idct(c):
    n = len(c)
    return [sum(math.sqrt((1 if k == 0 else 2) / n) * c[k] * math.cos(math.pi * k * (2 * i + 1) / (2 * n))
                for k in range(n)) for i in range(n)]


def errors(chunk, rebuilt):
    diffs = [abs(a - b) for row, rrow in zip(chunk, rebuilt) for a, b in zip(row, rrow)]
    return math.sqrt(sum(d * d for d in diffs) / len(diffs)), max(diffs)


def main():
    rng = random.Random(6)
    data = [episode(rng) for _ in range(50)]
    lo = [percentile([s[j] for ep in data for s in ep], 0.01) for j in range(JOINTS)]
    hi = [percentile([s[j] for ep in data for s in ep], 0.99) for j in range(JOINTS)]
    print(f'Dataset: 50 episodes of 10 s, {JOINTS} joints at {HZ} Hz; 1st..99th percentile per joint (deg):')
    print('  ' + '  '.join(f'j{j} {lo[j]:+.0f}..{hi[j]:+.0f}' for j in range(JOINTS)))
    print(f'  bin width = range / {BINS}: ' + ', '.join(f'{(hi[j] - lo[j]) / BINS:.2f}' for j in range(JOINTS)) + ' deg')

    chunk = episode(random.Random(99))[:CHUNK]          # a new episode, not in the dataset
    print(f'\nOne {CHUNK}-step chunk (1 s) from a new episode: {CHUNK} x {JOINTS} = {CHUNK * JOINTS} numbers')

    tokens = [[to_bins(chunk[t][j], lo[j], hi[j]) for j in range(JOINTS)] for t in range(CHUNK)]
    rebuilt = [[from_bins(tokens[t][j], lo[j], hi[j]) for j in range(JOINTS)] for t in range(CHUNK)]
    rms, worst = errors(chunk, rebuilt)
    clipped = sum(1 for t in range(CHUNK) for j in range(JOINTS) if not lo[j] <= chunk[t][j] <= hi[j])
    print(f'bins: {CHUNK * JOINTS} tokens, error rms {rms:.3f} deg, max {worst:.3f} deg '
          f'({clipped} values outside the 1st..99th percentile, clipped)')
    print('  joint 0 tokens, first 12 steps: ' + ' '.join(str(tokens[t][0]) for t in range(12)))
    same = sum(1 for t in range(1, CHUNK) for j in range(JOINTS) if tokens[t][j] == tokens[t - 1][j])
    near = sum(1 for t in range(1, CHUNK) for j in range(JOINTS) if abs(tokens[t][j] - tokens[t - 1][j]) <= 2)
    total = (CHUNK - 1) * JOINTS
    print(f'  token equal to the previous step: {same}/{total}; within 2 of it: {near}/{total}')

    print('\nDCT of each joint over the chunk, normalised to -1..1, then scale and round:')
    norm = [[2 * (chunk[t][j] - lo[j]) / (hi[j] - lo[j]) - 1 for j in range(JOINTS)] for t in range(CHUNK)]
    coeffs = [dct([norm[t][j] for t in range(CHUNK)]) for j in range(JOINTS)]
    for scale in (5, 10, 30, 100):
        q = [[round(c * scale) for c in coeffs[j]] for j in range(JOINTS)]
        nonzero = sum(1 for j in range(JOINTS) for v in q[j] if v != 0)
        back = [idct([v / scale for v in q[j]]) for j in range(JOINTS)]
        rebuilt = [[(back[j][t] + 1) / 2 * (hi[j] - lo[j]) + lo[j] for j in range(JOINTS)] for t in range(CHUNK)]
        rms, worst = errors(chunk, rebuilt)
        print(f'  scale {scale:>3}: {nonzero:>3} nonzero coefficients of {CHUNK * JOINTS}, '
              f'error rms {rms:.3f} deg, max {worst:.3f} deg')
    q = [round(c * 10) for c in coeffs[0]]
    print('  joint 0 at scale 10: ' + ' '.join(str(v) for v in q))


if __name__ == '__main__':
    main()
