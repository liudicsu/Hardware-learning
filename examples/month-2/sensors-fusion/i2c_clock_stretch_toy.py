#!/usr/bin/env python3
"""I2C clock stretching: a deaf controller vs one that waits for SCL high.

Synthetic bit-timing model, stdlib only.  Not a logic-analyser capture, not
the I2C rise-time / pull-up signal-integrity toy (arduino-io), not the I2C
scanner sketch and not RS-485.  Real bus / analyser: 本页未运行.
Wikipedia I2C statements 以原文为准.

What the Wikipedia I2C page says (and what this toy keeps):
  Clock stretching is a flow-control mechanism for targets: an addressed
  target may hold SCL low after receiving or sending a byte.  Because the
  lines are open-drain, SCL stays low; the controller must wait until it
  observes SCL actually going high, then a minimal time (4 us for standard
  100 kbit/s) before pulling SCL low again.  Some controllers do not support
  clock stretching (often labelled two-wire interface).  Pure I2C gives no
  stretch limit; SMBus does.
Edges are ideal here: RC rise time is not modelled (that is the arduino-io
rise-time toy), so the only reason SCL stays low is the target.

Common random numbers: per (regime, seed) one byte schedule, one stretch per
byte and one garbage bit stream, shared by every arm.  Arms:
  A_ignore  : releases SCL and samples after T_HIGH/2 on a fixed schedule,
              never reads SCL back (a controller without stretch support)
  B_wait    : waits until SCL is observed high, then samples (legal I2C)
  C_timeout : like B, but aborts the transaction when SCL stays low strictly
              longer than TIMEOUT_US (equality is still accepted)
The arms differ only in how the controller treats SCL.  The target stretches
the first clock of every byte after the first (it is preparing the next
byte, after the ACK).  A bit sampled strictly before the target releases SCL
reads the garbage bit instead of the data bit.  No integration step: event
times are summed, no ODE.

Regimes and the timeout were written before the first run:
  no_stretch       : target never stretches - A, B, C tie
  moderate_stretch : stretch 20..60 us per byte, below the timeout
                     - B consistent fewer byte errors than A; C ties B
  overtime_stretch : stretch 300..600 us per byte, above TIMEOUT_US=200 us
                     - C consistent fail (abort); B succeeds slowly; keep
"""
import math
import random

SEEDS = (0, 1, 2, 3, 4)
NUM_ZERO = 1e-9

# Declared model parameters, written before the first run (toy values).
T_LOW_US = 5.0        # us, controller low phase
T_HIGH_US = 5.0       # us, controller high phase (>= 4 us minimum, 以原文为准)
T_BIT_US = T_LOW_US + T_HIGH_US   # 10 us -> 100 kHz
CLOCKS_PER_BYTE = 9   # 8 data bits + ACK
N_BYTES = 16          # bytes per read transaction
N_TX = 20             # transactions per seed
TIMEOUT_US = 200.0    # us, C's SCL-low timeout (toy; pure I2C sets no limit)

REGIMES = {
    "no_stretch": (0.0, 0.0),
    "moderate_stretch": (20.0, 60.0),
    "overtime_stretch": (300.0, 600.0),
}
ARMS = ("A_ignore", "B_wait", "C_timeout")


def shared_bus(regime, seed):
    """Common random numbers: data, stretch and garbage bits, used by every arm."""
    rng = random.Random(f"{regime}/{seed}")
    lo, hi = REGIMES[regime]
    txs = []
    for _ in range(N_TX):
        data = [rng.randrange(256) for _ in range(N_BYTES)]
        stretch = [0.0] + [rng.uniform(lo, hi) if hi > 0.0 else 0.0 for _ in range(N_BYTES - 1)]
        garbage = [rng.randrange(256) for _ in range(N_BYTES)]
        txs.append({"data": data, "stretch": stretch, "garbage": garbage})
    return txs


def early_bits(stretch_us):
    """Bits a deaf controller samples strictly before the target releases SCL.

    Bit j of the byte is sampled at j*T_BIT + T_LOW + T_HIGH/2 after the byte
    starts; SCL is released at T_LOW + stretch.  Early iff sample < release.
    """
    return [j for j in range(8) if j * T_BIT_US + T_HIGH_US / 2.0 < stretch_us]


def read_byte_ignore(true_byte, garbage_byte, stretch_us):
    out = true_byte
    early = early_bits(stretch_us)
    for j in early:
        bit = 7 - j  # MSB first
        mask = 1 << bit
        out = (out & ~mask) | (garbage_byte & mask)
    return out, len(early)


def run_tx(arm, tx, timeout_us=TIMEOUT_US):
    t = 0.0
    errors = early = lost = 0
    aborted = 0
    for k in range(N_BYTES):
        s = tx["stretch"][k]
        if arm == "A_ignore":
            got, e = read_byte_ignore(tx["data"][k], tx["garbage"][k], s)
            early += e
            errors += int(got != tx["data"][k])
            t += CLOCKS_PER_BYTE * T_BIT_US
            continue
        if arm == "C_timeout" and s > timeout_us:   # strict: equality accepted
            t += timeout_us
            lost += N_BYTES - k
            aborted = 1
            break
        t += CLOCKS_PER_BYTE * T_BIT_US + s
    return {"time_us": t, "errors": errors, "early": early, "lost": lost, "aborted": aborted}


def run_seed(regime, seed, arm, timeout_us=TIMEOUT_US):
    agg = {"time_us": 0.0, "errors": 0, "early": 0, "lost": 0, "aborted": 0}
    for tx in shared_bus(regime, seed):
        r = run_tx(arm, tx, timeout_us)
        for key in agg:
            agg[key] += r[key]
    total = N_TX * N_BYTES
    agg["bad_rate"] = (agg["errors"] + agg["lost"]) / total
    agg["bus_ms"] = agg["time_us"] / 1000.0
    return agg


def mean_sd(xs):
    mu = sum(xs) / len(xs)
    return mu, math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))


def num(x):
    if x != 0.0 and abs(x) < 5e-4:
        return f"{x:.3e}"
    return f"{x:.4f}"


def sign_note(diffs, m):
    n, opp, zero = len(diffs), sum(1 for d in diffs if d * m < 0), sum(1 for d in diffs if d == 0)
    if opp == 0 and zero == 0:
        return f"same sign on all {n} seeds"
    if opp == 0:
        return f"no seed has the opposite sign, {zero} of {n} equal"
    note = f"{opp} of {n} seeds {'has' if opp == 1 else 'have'} the opposite sign"
    return note + (f", {zero} of {n} equal" if zero else "")


def fmt_pair(m, s):
    return f"{num(m)}+-{num(s)}"


def verdict(xa, xb):
    diffs = [a - b for a, b in zip(xa, xb)]
    if all(d == 0.0 for d in diffs):
        return "0.0000+-0.0000: tie: identical on every seed"
    m, s = mean_sd(diffs)
    if abs(m) < NUM_ZERO and s < NUM_ZERO:
        return f"{fmt_pair(m, s)}: numerically zero (floating-point residue), effectively a tie"
    if abs(m) <= s:
        label = "near-tie / small gap, within seed noise (|m| <= sd)"
    elif abs(m) < 0.2 * min(abs(mean_sd(xa)[0]), abs(mean_sd(xb)[0])):
        label = "small but consistent gap, not a tie (|m| > sd)"
    else:
        label = "clear gap, not a tie (|m| > sd)"
    return f"{fmt_pair(m, s)}: {label}; {sign_note(diffs, m)}"


def table(regime, timeout_us=TIMEOUT_US):
    return {arm: [run_seed(regime, seed, arm, timeout_us) for seed in SEEDS] for arm in ARMS}


def col(res, arm, key):
    return [float(r[key]) for r in res[arm]]


def main():
    print("Synthetic I2C clock-stretch toy; shared byte schedule; not an analyser capture")
    print(f"seeds={len(SEEDS)} T_LOW={T_LOW_US:.1f} us T_HIGH={T_HIGH_US:.1f} us T_BIT={T_BIT_US:.1f} us "
          f"CLOCKS_PER_BYTE={CLOCKS_PER_BYTE} N_BYTES={N_BYTES} N_TX={N_TX} TIMEOUT_US={TIMEOUT_US:.1f} (toy)")
    print("No integration step: summed event times, no time-step criterion")
    print("Regimes and TIMEOUT_US were written before the first run")
    print(f"hand_calc bit rate: 1/T_BIT = 1/{T_BIT_US:.1f} us = {1000.0 / T_BIT_US:.1f} kHz; "
          f"T_HIGH={T_HIGH_US:.1f} us >= 4 us standard-mode minimum (以原文为准)")
    print(f"hand_calc unstretched transaction: {N_BYTES}*{CLOCKS_PER_BYTE}*{T_BIT_US:.1f} us = "
          f"{N_BYTES * CLOCKS_PER_BYTE * T_BIT_US:.1f} us")
    print("early_rule: deaf controller samples bit j at j*T_BIT+T_LOW+T_HIGH/2; early iff that is strictly before "
          "release at T_LOW+stretch")
    for s in (2.5, 2.5001, 20.0, 60.0):
        print(f"  stretch={s:.4f} us -> early bits {len(early_bits(s))}")
    print(f"timeout_rule: C aborts iff stretch > TIMEOUT_US (strict); stretch={TIMEOUT_US:.4f} us aborts="
          f"{int(TIMEOUT_US > TIMEOUT_US)}; stretch={TIMEOUT_US + 0.001:.4f} us aborts={int(TIMEOUT_US + 0.001 > TIMEOUT_US)}")
    for regime, (lo, hi) in REGIMES.items():
        res = table(regime)
        print(f"{regime} (stretch {lo:.1f}..{hi:.1f} us per byte after the first; {N_TX}x{N_BYTES} bytes per seed):")
        for arm in ARMS:
            print(f"  {arm} bad_rate {fmt_pair(*mean_sd(col(res, arm, 'bad_rate')))} "
                  f"byte_errors {fmt_pair(*mean_sd(col(res, arm, 'errors')))} lost {fmt_pair(*mean_sd(col(res, arm, 'lost')))} "
                  f"aborts {fmt_pair(*mean_sd(col(res, arm, 'aborted')))} early_samples {fmt_pair(*mean_sd(col(res, arm, 'early')))} "
                  f"bus_ms {fmt_pair(*mean_sd(col(res, arm, 'bus_ms')))}")
        print(f"  paired A-B bad_rate: {verdict(col(res, 'A_ignore', 'bad_rate'), col(res, 'B_wait', 'bad_rate'))}")
        print(f"  paired C-B bad_rate: {verdict(col(res, 'C_timeout', 'bad_rate'), col(res, 'B_wait', 'bad_rate'))}")
        print(f"  paired C-B aborts: {verdict(col(res, 'C_timeout', 'aborted'), col(res, 'B_wait', 'aborted'))}")
        print(f"  paired B-A bus_ms: {verdict(col(res, 'B_wait', 'bus_ms'), col(res, 'A_ignore', 'bus_ms'))}")
        print(f"  paired A-B early_samples: {verdict(col(res, 'A_ignore', 'early'), col(res, 'B_wait', 'early'))}")
    for regime, alt in (("overtime_stretch", 1000.0), ("moderate_stretch", 50.0)):
        base = table(regime)
        res = table(regime, alt)
        print(f"alternative TIMEOUT_US={alt:.1f} on {regime} (same seeds):")
        print(f"  C_timeout bad_rate@alt {fmt_pair(*mean_sd(col(res, 'C_timeout', 'bad_rate')))} "
              f"aborts@alt {fmt_pair(*mean_sd(col(res, 'C_timeout', 'aborted')))} "
              f"(default bad_rate {fmt_pair(*mean_sd(col(base, 'C_timeout', 'bad_rate')))})")
        print(f"  paired C-B bad_rate@alt: {verdict(col(res, 'C_timeout', 'bad_rate'), col(res, 'B_wait', 'bad_rate'))}")
    print("No winner declared: without stretching all three tie; with stretching only a controller that waits for SCL "
          "reads correctly, and a timeout shorter than the target's stretch turns a slow read into a failed one")
    print("Real bus / analyser: 本页未运行; Wikipedia statements 以原文为准")


if __name__ == "__main__":
    main()
