#!/usr/bin/env python3
"""clarke_park_toy.py: Clarke–Park round-trip for FOC (stdlib).

Given id_cmd=0, iq_cmd and electrical angle θ:
  inverse Park → inverse Clarke → Clarke → Park
and check sum_abc≈0 plus recovered id/iq.
Formulas follow SimpleFOC foc_theory (balanced three-phase).
"""
import math

SEED = 11
theta = math.pi / 6
iq_cmd, id_cmd = 1.0, 0.0


def clarke(ia, ib, ic):
    # Balanced: ia+ib+ic=0; SimpleFOC-style
    i_alpha = ia
    i_beta = (ia + 2 * ib) / math.sqrt(3)
    return i_alpha, i_beta


def park(i_alpha, i_beta, th):
    c, s = math.cos(th), math.sin(th)
    id_ = i_alpha * c + i_beta * s
    iq = -i_alpha * s + i_beta * c
    return id_, iq


# Inverse Park then inverse Clarke
u_alpha = id_cmd * math.cos(theta) - iq_cmd * math.sin(theta)
u_beta = id_cmd * math.sin(theta) + iq_cmd * math.cos(theta)
ia = u_alpha
ib = -0.5 * u_alpha + (math.sqrt(3) / 2) * u_beta
ic = -0.5 * u_alpha - (math.sqrt(3) / 2) * u_beta

a, b = clarke(ia, ib, ic)
id_r, iq_r = park(a, b, theta)

print(f"seed={SEED}")
print(f"theta_rad={theta:.6f}")
print(f"iq_cmd={iq_cmd:.4f} id_cmd={id_cmd:.4f}")
print(f"ia={ia:.6f} ib={ib:.6f} ic={ic:.6f}")
print(f"sum_abc={ia + ib + ic:.3e}")
print(f"id_recovered={id_r:.6f} iq_recovered={iq_r:.6f}")
print(f"id_err={abs(id_r - id_cmd):.3e} iq_err={abs(iq_r - iq_cmd):.3e}")
