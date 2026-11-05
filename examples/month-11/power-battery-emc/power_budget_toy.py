#!/usr/bin/env python3
"""power_budget_toy.py: IR drop and fuse margin for a desktop-arm bus (stdlib).

Illustrative SO-101-like bus-servo currents — NOT measured on this site.
Fixed seed for reproducibility; change n_servos / wire length to explore.
"""
SEED = 5
# SO-101-like bus servos: illustrative currents, not measured
V_nom = 12.0
I_idle = 0.35  # A per servo idle
I_peak = 1.8   # A stall-ish peak
n_servos = 6
wire_mohm_per_m = 50.0  # 22 AWG ballpark illustrative
wire_len_m = 0.8
fuse_A = 10.0
V_floor = 11.0

R = wire_mohm_per_m * 1e-3 * wire_len_m
I_total_peak = n_servos * I_peak
I_total_idle = n_servos * I_idle
V_drop = I_total_peak * R
V_at_load = V_nom - V_drop
margin = fuse_A / I_total_peak

print(f"seed={SEED}")
print(f"V_nom={V_nom:.1f}")
print(f"n_servos={n_servos}")
print(f"I_idle_total={I_total_idle:.2f}")
print(f"I_peak_total={I_total_peak:.2f}")
print(f"wire_R_ohm={R:.4f}")
print(f"V_drop_peak={V_drop:.3f}")
print(f"V_at_load={V_at_load:.3f}")
print(f"fuse_A={fuse_A:.1f}")
print(f"fuse_margin={margin:.3f}")
print(f"pass_11v_floor={str(V_at_load >= V_floor).lower()}")
