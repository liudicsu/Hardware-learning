#!/usr/bin/env python3
"""Synthetic lumped open-drain RC bus; same bytes and SCL edges in all arms.
tr30to70=ln(7/3)*Rp*C is distinct from t70=-ln(0.3)*Rp*C.
TI SLVA689A Table 2-1: tr_max Sm=1000 ns, Fm=300 ns, Fm+=120 ns.
Three rise-only screens use shared bytes, NOT full mode compliance.
The waveform remains 400 kHz/Fm; TMP102 is not claimed to support Fm+.
TMP102 datasheet Fast-mode clock limits: 400 kHz, tr<=300 ns, low>=1300 ns,
high>=600 ns. 3.3 V is selected; all Rp, board/device/wire C are SYNTHETIC.
Every transmitter, including the master, is ASSUMED to support the example
3 mA / VOL<=0.4 V sink budget (TMP102 gives this for its outputs).
Edge-budget flags are NOT packet failures or ACK observations. Stdlib only.
No distributed-line/noise/fall/setup/hold/clock-stretch simulation; 本页未运行.
"""
from math import log

MESSAGE = bytes((0xA5, 0x00, 0xFF, 0x5A))  # synthetic, not a TMP102 register transaction
F_HZ = 400_000.0
LOW_S = 1500e-9
HIGH_RELEASE_S = 1 / F_HZ - LOW_S
MODE_RISE_LIMITS = (("Sm", 1000e-9), ("Fm", 300e-9), ("Fm+", 120e-9))
RISE_BUDGET_S = dict(MODE_RISE_LIMITS)["Fm"]
MIN_HIGH_S = 600e-9
VDD = 3.3
VOL_MAX = 0.4
IOL_A = 0.003
BOARD_PF = 30.0
DEVICES = 3
DEVICE_PF = 10.0
ARMS = (("weak_short", 10000.0, 40.0), ("strong_short", 2200.0, 40.0),
        ("strong_long_C", 2200.0, 340.0))


def capacitance(wire_pf):
    return (BOARD_PF + DEVICES * DEVICE_PF + wire_pf) * 1e-12


def scl_slots(message):
    # ACK is a slot, NOT a simulated response. All slots release SCL once.
    return tuple(slot for byte in message for slot in
                 tuple((byte >> bit) & 1 for bit in range(7, -1, -1)) + (None,))


def evaluate(rp, cbus, slots, frequency=F_HZ):
    if rp <= 0 or cbus <= 0 or frequency <= 0 or 1 / frequency <= LOW_S:
        raise ValueError("positive RC and a nonempty high release window required")
    tr = log(7 / 3) * rp * cbus
    t70 = -log(0.3) * rp * cbus  # starts at ideal zero, conservative vs positive VOL
    high = max(0.0, 1 / frequency - LOW_S - t70)
    rp_min = (VDD - VOL_MAX) / IOL_A
    rp_max = RISE_BUDGET_S / (log(7 / 3) * cbus)
    edge_ok = tr <= RISE_BUDGET_S and high >= MIN_HIGH_S
    return dict(tr=tr, fraction=tr * frequency, high=high, rp_min=rp_min,
                rp_max=rp_max, sink_ma=(VDD - VOL_MAX) / rp * 1000,
                sink_ok=rp >= rp_min, flags=sum(not edge_ok for _ in slots))


def rise_screens(tr, slots):
    """Generic mode rise limits only, not frequency/high/sink/device checks."""
    return tuple((mode, limit, tr / limit, len(slots) if tr > limit else 0)
                 for mode, limit in MODE_RISE_LIMITS)


def main():
    slots = scl_slots(MESSAGE)
    print("Synthetic Rp/Cbus; TMP102 example timing/sink budget, not a link certificate")
    print(f"shared bytes={MESSAGE.hex(' ').upper()} SCL_edges={len(slots)} ACK_outcome=not_modelled")
    print(f"bit_ns={1e9 / F_HZ:.0f} low_ns={LOW_S * 1e9:.0f} release_high_ns={HIGH_RELEASE_S * 1e9:.0f} rise_budget_ns={RISE_BUDGET_S * 1e9:.0f}")
    print("arm Rp_ohm Cbus_pF tr_ns tr_over_bit stable_high_ns sink_at_VOLmax_mA sink_ok edge_budget_flags")
    for arm, rp, wire_pf in ARMS:
        cbus = capacitance(wire_pf)
        r = evaluate(rp, cbus, slots)
        print(f"{arm} {rp:.0f} {cbus * 1e12:.0f} {r['tr'] * 1e9:.3f} {r['fraction']:.6f} {r['high'] * 1e9:.3f} {r['sink_ma']:.3f} {int(r['sink_ok'])} {r['flags']}")
    short = evaluate(2200, capacitance(40), slots)
    long = evaluate(2200, capacitance(340), slots)
    print(f"Rp_min_ohm={short['rp_min']:.3f} Rp_max_short_ohm={short['rp_max']:.3f} Rp_max_long_ohm={long['rp_max']:.3f}")
    print("TI SLVA689A Table 2-1: rise-only screens (not full mode/device compliance)")
    print("arm mode tr_max_ns tr_over_limit violating_edges")
    for arm, rp, wire_pf in ARMS:
        tr = evaluate(rp, capacitance(wire_pf), slots)["tr"]
        for mode, limit, ratio, flags in rise_screens(tr, slots):
            print(f"{arm} {mode} {limit * 1e9:.0f} {ratio:.6f} {flags}")
    print("400kHz waveform is Fm only; Sm rise-pass is not Sm link-pass; no TMP102 Fm+ claim")
    print("Flags are edge-budget violations, NOT observed packet loss; real bus/scope: 本页未运行")


if __name__ == "__main__":
    main()
