#!/usr/bin/env python3
"""power_roundtrip_loss_toy.py: round-trip IR drop, I^2R loss, fuse data gates (stdlib).

Illustrative SO-101-like bus-servo currents — NOT measured on this site.
Continuous and peak currents are INDEPENDENT example assumptions (do not
pretend peak is continuous). Ampacity gate uses continuous only; peak without
a time–current / I^2t curve stays insufficient_data.
Protection outcomes are ONLY insufficient_data or reject_known_constraint.
Never emits ok_slow_blow / "suitable fuse" from a peak-current ratio alone.
"""
SEED = 7

# Illustrative currents / geometry (labelled not measured)
V_nom = 12.0
I_idle = 0.35    # A per servo idle (example assumption)
I_cont = 0.55    # A per servo continuous under load (example assumption; NOT peak)
I_peak = 1.8     # A stall-ish peak (example assumption; duration unknown)
n_servos = 6
wire_mohm_per_m = 50.0  # 22 AWG ballpark illustrative
len_short_m = 0.8
len_long_m = 1.5
V_floor = 11.0
# Illustrative continuous ampacity — deliberately below I_cont_total for reject demo
wire_ampacity_A = 3.0

I_idle_total = n_servos * I_idle
I_cont_total = n_servos * I_cont   # continuous — used for ampacity gate
I_peak_total = n_servos * I_peak   # peak — NOT passed as continuous


def one_way_R(length_m):
    return wire_mohm_per_m * 1e-3 * length_m


def round_trip_drop(I, length_m):
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
    if not (have_fuse_curve and have_dc_interrupt and have_fault_current):
        return "insufficient_data"
    return "insufficient_data"


def undervoltage_label(v_short, v_long, v_floor):
    short_uv = v_short < v_floor
    long_uv = v_long < v_floor
    if short_uv and long_uv:
        return "both"
    if long_uv:
        return "long_only"
    if short_uv:
        return "short_only"
    return "neither"


# Round-trip IR / I^2R at peak (thermal hygiene numbers); idle I^2R for contrast
drop_short, R_rt_short = round_trip_drop(I_peak_total, len_short_m)
V_load_short = V_nom - drop_short
P_idle_short = i2r_loss(I_idle_total, R_rt_short)
P_peak_short = i2r_loss(I_peak_total, R_rt_short)
R_ow_short = one_way_R(len_short_m)
drop_ow_short = I_peak_total * R_ow_short

drop_long, R_rt_long = round_trip_drop(I_peak_total, len_long_m)
V_load_long = V_nom - drop_long

status_default = protection_status()  # missing fuse datasheet fields
status_long_v = protection_status(v_at_load=V_load_long, v_floor=V_floor)
# Ampacity gate uses CONTINUOUS only — never I_peak_total as i_continuous
status_ampacity = protection_status(
    i_continuous=I_cont_total, wire_ampacity=wire_ampacity_A
)
# Peak alone without curve/duration → still insufficient_data
status_peak_only = protection_status()  # same missing fields; peak not a reject input

hits_V_floor = undervoltage_label(V_load_short, V_load_long, V_floor)

assert status_default == "insufficient_data"
assert status_peak_only == "insufficient_data"
assert status_ampacity == "reject_known_constraint"
assert "ok" not in status_default
assert I_cont_total != I_peak_total

print(f"seed={SEED}")
print(f"V_nom={V_nom:.1f}")
print(f"n_servos={n_servos}")
print(f"I_idle_total={I_idle_total:.2f}")
print(f"I_cont_total={I_cont_total:.2f}")  # continuous example assumption
print(f"I_peak_total={I_peak_total:.2f}")  # peak example assumption (not continuous)
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
print(f"hits_V_floor={hits_V_floor}")
print(f"protection_status_default={status_default}")
print(f"protection_status_long_wire={status_long_v}")
print(f"protection_status_ampacity={status_ampacity}")
print(f"protection_status_peak_only={status_peak_only}")
print(f"wire_ampacity_A={wire_ampacity_A:.1f}")
print("currents_labelled=example_assumptions")
print("fuse_certification=never")
