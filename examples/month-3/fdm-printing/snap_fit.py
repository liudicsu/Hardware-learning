"""snap_fit.py: will a printed cantilever snap-fit arm bend or break?

Classic straight-beam formulas for a rectangular cantilever arm with a hook at its tip
(as in the Bayer/Covestro snap-fit design guide):
    strain at the root   eps = 1.5 * y * t / L^2
    force to deflect it  P   = b * t^2 * E * eps / (6 * L)
    force to push it on  W   = P * (mu + tan a) / (1 - mu * tan a)
y = hook depth (how far the arm must bend), t = arm thickness, L = arm length,
b = arm width, E = stiffness of the plastic, a = lead-in angle of the hook, mu = friction.
The strain limits below are our cautious rules of thumb for FDM parts, not datasheet
values: a printed arm is weakest when it bends across its layers. Print a test arm before
you trust any of this.
"""
import math

MATERIALS = {             # E (MPa), strain we allow for a snap that is used many times
    "PLA":  (3500, 0.015),
    "PETG": (2000, 0.025),
}


def snap(L, t, y, b=6.0, material="PLA", lead_deg=30.0, mu=0.3):
    E, allowed = MATERIALS[material]
    eps = 1.5 * y * t / L ** 2
    P = b * t ** 2 * E * eps / (6 * L)
    tan_a = math.tan(math.radians(lead_deg))
    W = P * (mu + tan_a) / (1 - mu * tan_a)
    verdict = "ok" if eps <= allowed else f"too much (limit {allowed * 100:.1f} %)"
    return (f"L {L:4.1f}  t {t:.1f}  hook {y:.1f} mm, {material + ",":5s} lead-in {lead_deg:2.0f} deg: "
            f"strain {eps * 100:4.2f} % {verdict:22s} push-on {W:5.1f} N")


if __name__ == "__main__":
    print(snap(5, 1.5, 1.0))                   # short and thick: the first design people draw
    print(snap(10, 1.5, 1.0))
    print(snap(10, 1.2, 0.8))                  # the arm used in esp32_case.scad
    print(snap(10, 1.2, 0.8, material="PETG"))
    print(snap(10, 1.2, 0.8, lead_deg=60))     # steep lead-in: hard to push on
