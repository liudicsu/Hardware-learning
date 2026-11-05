#!/usr/bin/env python3
"""oxe_imbalance_toy.py: synthetic embodiment imbalance + inverse-frequency weights (stdlib).

The counts below are **synthetic** — they are NOT Open X-Embodiment (OXE) real
cardinality. Real OXE / OXE-AugE numbers used in the lesson prose (1M+, 22
embodiments, top-4 >85 %, 4.4M, 24–45 %) are printed as separate paper constants
and must not be confused with this table. Take the papers / project pages as
source of truth. Downloading OXE or training is not run on this page.
Deterministic: no random draws, so there is no seed.
"""
# Synthetic counts mirroring OXE-style skew (NOT real OXE counts)
robots = ["Franka", "xArm", "Kuka", "Google", "WidowX", "UR5", "Jaco", "Other"]
counts = [420000, 280000, 180000, 150000, 40000, 35000, 20000, 25000]
total = sum(counts)
top4 = sum(counts[:4])
top4_share = top4 / total

# Inverse-frequency weights, clipped at 10
weights = []
for c in counts:
    w = total / (len(robots) * c)
    weights.append(min(w, 10.0))
reweighted_mass = sum(w * c for w, c in zip(weights, counts))

print(f"n_robots={len(robots)}")
print(f"total_traj={total}")
print(f"top4_share={top4_share:.4f}")
print(f"max_weight={max(weights):.3f}")
print(f"reweighted_mass={reweighted_mass:.1f}")
# Paper / project-page constants (not from the synthetic table)
print(f"oxe_traj_million_plus=1")
print(f"oxe_embodiments=22")
print(f"oxe_top4_pct=85")
print(f"oxe_auge_traj_million=4.4")
print(f"oxe_auge_multiplier=3")
print(f"oxe_auge_success_lift_lo=24")
print(f"oxe_auge_success_lift_hi=45")
