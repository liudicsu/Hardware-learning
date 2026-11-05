#!/usr/bin/env python3
"""tactile_marker_toy.py: marker-grid deformation → contact estimate (stdlib).

3×3 marker grid; a synthetic contact pulls markers radially inward.
Estimate contact as the displacement-weighted centroid of markers
(not the single largest-displacement marker). Also prints AnySkin
paper constants used in the lesson prose (replace time, slip accuracy,
plug-insertion success rates) — paper numbers, not toy measurements.
"""
import math

SEED = 13
# 3x3 marker grid, rest spacing 1.0
grid = [(x, y) for y in (-1.0, 0.0, 1.0) for x in (-1.0, 0.0, 1.0)]
force_N = 2.5
k = 0.08  # synthetic compliance in image units
cx, cy = 0.2, -0.15

obs = []
for x, y in grid:
    dx = x - cx
    dy = y - cy
    r2 = dx * dx + dy * dy + 1e-6
    scale = k * force_N / r2
    obs.append((x - dx * scale, y - dy * scale))

disps = [math.hypot(o[0] - g[0], o[1] - g[1]) for o, g in zip(obs, grid)]
# Displacement-weighted centroid of observed marker positions
wsum = sum(disps)
est_x = sum(o[0] * d for o, d in zip(obs, disps)) / wsum
est_y = sum(o[1] * d for o, d in zip(obs, disps)) / wsum
err = math.hypot(est_x - cx, est_y - cy)

print(f"seed={SEED}")
print(f"true_contact=({cx:.3f},{cy:.3f})")
print(f"force_N={force_N:.2f}")
print(f"est_contact=({est_x:.4f},{est_y:.4f})")
print(f"contact_err={err:.4f}")
print(f"max_disp={max(disps):.4f}")
# AnySkin paper constants (arXiv 2409.08276) for check_diagrams bindings
print(f"anyskin_replace_s=12")
print(f"anyskin_slip_acc=0.92")
print(f"anyskin_plug_cam=1.7")
print(f"anyskin_plug_skin=6.7")
print(f"anyskin_plug_swap=5.3")
