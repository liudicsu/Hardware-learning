#!/usr/bin/env python3
"""Synthetic PDN: source through shared Rfeed, load, series ESL+ESR+C shunt.
All arms have EXACTLY 10 uF total and consume the SAME piecewise-linear pulses.
Identical parallel caps combine as C=N*Cpart, ESR=ESRpart/N, ESL=ESLpart/N;
shared placement-loop inductance is added ONCE, never divided by N.
Frequency impedance, SRF and time-domain pin voltage are different metrics.
No real component/PCB characterization, FCC/CE or fuse certification. Stdlib only.
"""
from math import ceil, pi, sqrt
from typing import NamedTuple

VRAIL = 3.3
RFEED = 0.5  # ohm, shared synthetic regulator/source impedance, not 11.1 wire sizing
HF_HZ = 20e6
TOTAL_C = 10e-6
PULSES = ((0.10, 20e-9), (0.16, 40e-9), (0.08, 10e-9))


class Bank(NamedTuple):
    name: str
    count: int
    each_uf: float
    each_esr: float  # ohm
    each_esl_nh: float
    loop_nh: float


BANKS = (Bank("far_bulk", 1, 10., .20, 5., 40.),
         Bank("local_single", 1, 10., .02, 1., 3.),
         Bank("local_split", 10, 1., .04, .8, 3.),
         Bank("long_trace", 10, 1., .04, .8, 100.))


def equivalent(bank):
    return (bank.count * bank.each_uf * 1e-6, bank.each_esr / bank.count,
            (bank.loop_nh + bank.each_esl_nh / bank.count) * 1e-9)


def impedance(bank, frequency):
    c, r, inductance = equivalent(bank)
    omega = 2 * pi * frequency
    return complex(r, omega * inductance - 1 / (omega * c))


def srf(bank):
    """Mounted-path resonance includes the shared loop, not bare-part SRF."""
    c, _, inductance = equivalent(bank)
    return 1 / (2 * pi * sqrt(inductance * c))


def component_srf(bank):
    """Intrinsic identical-bank SRF before the shared placement-loop L."""
    c, _, _ = equivalent(bank)
    esl = bank.each_esl_nh / bank.count * 1e-9
    return 1 / (2 * pi * sqrt(esl * c))


def pulse_segments():
    """(duration, I_start, I_end, max_step); same linear ramps and hold in all arms."""
    segments = []
    now = 0.
    for cycle in range(3):
        for index, (amplitude, rise) in enumerate(PULSES):
            start = cycle * 100e-6 + index * 10e-6
            if start > now:
                segments.append((start - now, 0., 0., 50e-9))
            segments.extend(((rise, 0., amplitude, .5e-9),
                             (500e-9, amplitude, amplitude, .5e-9),
                             (rise, amplitude, 0., .5e-9),
                             (1000e-9, 0., 0., .5e-9)))
            now = start + 2 * rise + 1500e-9
    segments.append((300e-6 - now, 0., 0., 50e-9))
    return tuple(segments)


def step(bank, u, current, load0, load1, dt):
    """Trapezoid on u=Vc-Vrail, i=capacitor-to-node current; KCL+KVL.
    du/dt=-i/C; L di/dt=u-(Rfeed+ESR)i+Rfeed*Iload.
    Vpin=Vrail-Rfeed*(Iload-i). Includes charge/recharge, not L*di/dt only.
    """
    c, r, inductance = equivalent(bank)
    a = dt / (2 * c)
    b = dt / (2 * inductance)
    damping = b * (RFEED + r)
    rhs0 = u - a * current
    rhs1 = b * u + (1 - damping) * current + b * RFEED * (load0 + load1)
    next_i = (rhs1 + b * rhs0) / (1 + damping + a * b)
    next_u = rhs0 - a * next_i
    return next_u, next_i


def simulate(bank, segments, refinement=1):
    u = current = 0.
    minimum = maximum = VRAIL
    for duration, load0, load1, max_step in segments:
        n = ceil(duration / (max_step / refinement))
        dt = duration / n
        for k in range(n):
            before = load0 + (load1 - load0) * k / n
            after = load0 + (load1 - load0) * (k + 1) / n
            u, current = step(bank, u, current, before, after, dt)
            pin = VRAIL - RFEED * (after - current)
            minimum, maximum = min(minimum, pin), max(maximum, pin)
    return minimum, VRAIL - minimum, maximum


def main():
    segments = pulse_segments()
    print("Synthetic series ESL+ESR+C capacitor path; shared source Rfeed=0.5ohm")
    print("Equal total C=10uF; shared 9 rising/9 falling ramps; 500ns plateaus; 3 cycles")
    print("arm count each_uF total_uF ESR_eq_ohm Ltotal_nH cap_SRF_MHz mounted_SRF_MHz min_rail_V dip_V max_rail_V")
    for bank in BANKS:
        c, r, inductance = equivalent(bank)
        minimum, dip, maximum = simulate(bank, segments)
        print(f"{bank.name} {bank.count} {bank.each_uf:.1f} {c * 1e6:.1f} {r:.4f} {inductance * 1e9:.3f} {component_srf(bank) / 1e6:.6f} {srf(bank) / 1e6:.6f} {minimum:.6f} {dip:.6f} {maximum:.6f}")
    print("arm Z_0.1SRF_ohm Z_SRF_ohm Z_10SRF_ohm ImZ_0.1SRF_ohm ImZ_10SRF_ohm XL_over_XC_at_10SRF")
    for bank in BANKS:
        f = srf(bank)
        print(f"{bank.name} {abs(impedance(bank, .1 * f)):.6f} {abs(impedance(bank, f)):.6f} {abs(impedance(bank, 10 * f)):.6f} {impedance(bank, .1 * f).imag:.6f} {impedance(bank, 10 * f).imag:.6f} 100.000")
    print("20MHz above all SRFs: arm Xloop_ohm Xesl_eq_ohm Xc_ohm ESR_eq_ohm")
    for bank in BANKS:
        c, r, _ = equivalent(bank)
        omega = 2 * pi * HF_HZ
        print(f"{bank.name} {omega * bank.loop_nh * 1e-9:.6f} {omega * bank.each_esl_nh / bank.count * 1e-9:.6f} {1 / (omega * c):.6f} {r:.6f}")
    print("SRF cancels reactances, not ESR; above SRF the path becomes inductive")
    print("Shared loop L is not divided by capacitor count; not a universal part/layout winner")
    print("No DC-bias/tolerance/mutual-L/distributed-PCB/regulator dynamics; no FCC/CE or fuse claim")
    print("Real board / scope / EMC test: 本页未运行")


if __name__ == "__main__":
    main()
