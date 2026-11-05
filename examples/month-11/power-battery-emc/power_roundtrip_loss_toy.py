#!/usr/bin/env python3
"""power_roundtrip_loss_toy.py: round-trip IR drop, I^2R loss, fuse data gates (stdlib).

Illustrative SO-101-like bus-servo currents — NOT measured on this site.
Protection outcomes are ONLY insufficient_data or reject_known_constraint.
Never emits ok_slow_blow / "suitable fuse" from a peak-current ratio alone.
Real fuse selection needs DC voltage rating, interrupt capacity, wire ampacity
+ derating, prospective fault current, and manufacturer time-current / I^2t —
none of which this toy ships.
"""
SEED = 7

# Illustrative currents / geometry (labelled not measured)
V_nom = 12.0
I_idle = 0.35   # A per servo
I_peak = 1.8    # A stall-ish peak
n_servos = 6
wire_mohm_per_m = 50.0  # 22 AWG ballpark illustrative
# Two lengths under equal current — voltage constraint only
len_short_m = 0.8
len_long_m = 1.5
V_floor = 11.0
# Illustrative continuous ampacity input for the reject demo (not a datasheet claim)
wire_ampacity_A = 8.0  # deliberately below peak total for reject_known_constraint arm

I_peak_total = n_servos * I_peak
I_idle_total = n_servos * I_idle


def one_way_R(length_m):
    return wire_mohm_per_m * 1e-3 * length_m


def round_trip_drop(I, length_m):
    # Go + return: R_go + R_ret with symmetric return
    R_rt = 2.0 * one_way_R(length_m)
    return I * R_rt, R_rt


def i2r_loss(I, R):
    return I * I * R


def protection_status(*, v_at_load=None, v_floor=None, i_continuous=None, wire_ampacity=None,
                      have_fuse_curve=False, have_dc_interrupt=False, have_fault_current=False):
    """Data-gated protection literacy. Never certifies a fuse as suitable."""
    if v_at_load is not None and v_floor is not None and v_at_load < v_floor:
        return "reject_known_constraint"
    if (i_continuous is not None and wire_ampacity is not None
            and i_continuous > wire_ampacity):
        return "reject_known_constraint"
    # Missing manufacturer fuse curve / DC interrupt / fault current → cannot certify
    if not (have_fuse_curve and have_dc_interrupt and have_fault_current):
        return "insufficient_data"
    # Even with flags, this course never ships curves — unreachable by design.
    return "insufficient_data"


# --- Run A: short wire, default (no fuse datasheet fields) ---
drop_short, R_rt_short = round_trip_drop(I_peak_total, len_short_m)
V_load_short = V_nom - drop_short
P_idle_short = i2r_loss(I_idle_total, R_rt_short)
P_peak_short = i2r_loss(I_peak_total, R_rt_short)
# one-way for comparison with power_budget_toy
R_ow_short = one_way_R(len_short_m)
drop_ow_short = I_peak_total * R_ow_short
status_default = protection_status()  # missing all fuse fields

# --- Run B: long wire, same peak current — voltage floor only ---
drop_long, R_rt_long = round_trip_drop(I_peak_total, len_long_m)
V_load_long = V_nom - drop_long
status_long_v = protection_status(v_at_load=V_load_long, v_floor=V_floor)

# --- Run C: continuous current vs illustrative ampacity (reject) ---
status_ampacity = protection_status(
    i_continuous=I_peak_total, wire_ampacity=wire_ampacity_A
)

# Which length hits V_floor first (voltage constraint only; equal I)
hits_floor_first = "long" if V_load_long < V_floor and V_load_short >= V_floor else (
    "short" if V_load_short < V_floor else "neither"
)

# Sanity: never emit ok_* 
assert status_default == "insufficient_data"
assert "ok" not in status_default and "ok" not in status_long_v and "ok" not in status_ampacity

print(f"seed={SEED}")
print(f"V_nom={V_nom:.1f}")
print(f"n_servos={n_servos}")
print(f"I_idle_total={I_idle_total:.2f}")
print(f"I_peak_total={I_peak_total:.2f}")
print(f"len_short_m={len_short_m:.1f}")
print(f"len_long_m={len_long_m:.1f}")
print(f"R_oneway_short_ohm={R_ow_short:.4f}")
print(f"R_roundtrip_short_ohm={R_rt_short:.4f}")
print(f"V_drop_oneway_short={drop_ow_short:.3f}")
print(f"V_drop_roundtrip_short={drop_short:.3f}")
print(f"V_at_load_roundtrip_short={V_load_short:.3f}")
print(f"P_i2r_idle_short_W={P_idle_short:.4f}")
print(f"P_i2r_peak_short_W={P_peak_short:.4f}")
print(f"V_drop_roundtrip_long={drop_long:.3f}")
print(f"V_at_load_roundtrip_long={V_load_long:.3f}")
print(f"V_floor={V_floor:.1f}")
print(f"hits_V_floor_first={hits_floor_first}")
print(f"protection_status_default={status_default}")
print(f"protection_status_long_wire={status_long_v}")
print(f"protection_status_ampacity={status_ampacity}")
print(f"wire_ampacity_A={wire_ampacity_A:.1f}")
print("fuse_certification=never")  # explicit: toy never certifies
