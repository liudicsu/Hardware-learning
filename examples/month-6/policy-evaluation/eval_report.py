"""eval_report.py: how to measure a policy, on the behaviour-cloning corridor from lesson 1.

1. Success rates with Wilson 95 % intervals: what "67/100" and "8/10" can and cannot tell you.
2. How much a 10-trial evaluation of the same policy moves around between sessions.
3. A paired comparison: every policy runs from the same list of per-trial seeds (same start, same noise),
   so trials can be compared one by one, with McNemar's exact test on the trials where they disagree.
4. How many trials you need to tell two success rates apart.
5. A failure table: where and when the failures happen.
Standard library only; imports the corridor, expert and policies from ../behaviour-cloning/bc_reach.py.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'behaviour-cloning'))
import bc_reach  # noqa: E402

Z95, Z80 = 1.959964, 0.841621          # two-sided 95 % confidence; 80 % power


def wilson(k, n, z=Z95):
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def trials(policy, seeds):
    """One rollout per seed; each trial gets its own random generator, so its start and noise are fixed."""
    return [bc_reach.rollout(policy, random.Random(s)) for s in seeds]


def mcnemar_p(b, c):
    """Exact two-sided McNemar test: under 'no difference' each disagreement is a fair coin."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def trials_needed(p1, p2):
    """Trials per policy for a two-sided 5 % test with 80 % power (normal approximation)."""
    pbar = (p1 + p2) / 2
    num = Z95 * math.sqrt(2 * pbar * (1 - pbar)) + Z80 * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    return math.ceil(num * num / (p1 - p2) ** 2)


def main():
    print('1. Success with a Wilson 95 % interval')
    for k, n in ((61, 100), (67, 100), (99, 100), (100, 100), (8, 10), (10, 10)):
        lo, hi = wilson(k, n)
        print(f'  {k:>3}/{n:<3}  {100 * k / n:5.1f} %   95 % interval {100 * lo:5.1f} .. {100 * hi:5.1f} %')

    demos = bc_reach.record_demos(80, random.Random(6))
    bc20 = bc_reach.nn_policy([f for f in demos if f[0] < 20])
    noisy = bc_reach.record_demos(20, random.Random(8), noise=bc_reach.NOISE)
    bc_noisy = bc_reach.nn_policy(noisy)

    print('\n2. BC on 20 demos, ten separate sessions of 10 trials each (different seeds per session)')
    scores = [sum(r[0] == 'success' for r in trials(bc20, range(100 * s, 100 * s + 10))) for s in range(10)]
    print('  successes out of 10: ' + ' '.join(str(v) for v in scores) + f'   (lowest {min(scores)}, highest {max(scores)})')

    print('\n3. Paired comparison over the same 100 trials (seeds 5000..5099)')
    seeds = range(5000, 5100)
    a = trials(bc20, seeds)
    b = trials(bc_noisy, seeds)
    sa, sb = [r[0] == 'success' for r in a], [r[0] == 'success' for r in b]
    both = sum(x and y for x, y in zip(sa, sb))
    only_a = sum(x and not y for x, y in zip(sa, sb))
    only_b = sum(y and not x for x, y in zip(sa, sb))
    neither = sum(not x and not y for x, y in zip(sa, sb))
    for label, s in (('BC, 20 demos', sa), ('BC, 20 noisy demos', sb)):
        lo, hi = wilson(sum(s), len(s))
        print(f'  {label:<20} {sum(s):>3}/100   95 % interval {100 * lo:5.1f} .. {100 * hi:5.1f} %')
    print(f'  both succeed {both}, only the first {only_a}, only the second {only_b}, both fail {neither}')
    print(f'  McNemar exact test on the {only_a + only_b} disagreements: p = {mcnemar_p(only_a, only_b):.2g}')

    print('\n4. Trials per policy to tell two success rates apart (5 % test, 80 % power)')
    for p1, p2 in ((0.67, 0.99), (0.60, 0.80), (0.80, 0.90), (0.90, 0.95)):
        print(f'  {100 * p1:.0f} % vs {100 * p2:.0f} %: {trials_needed(p1, p2):>4} trials each')

    print('\n5. Failures of BC on 20 demos in those 100 trials')
    fails = [r for r in a if r[0] != 'success']
    places = {}
    for result, steps, worst, p in fails:
        key = result if result != 'wall' else 'wall, ' + bc_reach.place(p)
        places.setdefault(key, []).append(steps)
    print(f'  {"failure":<18} {"count":>5} {"share":>7} {"mean step":>10}')
    for key in sorted(places, key=lambda k: -len(places[k])):
        v = places[key]
        print(f'  {key:<18} {len(v):>5} {100 * len(v) / len(fails):>6.0f}% {sum(v) / len(v):>10.1f}')


if __name__ == '__main__':
    main()
