"""grip_force.py: how hard must a two-finger gripper squeeze so the object does not slip?

With two flat fingers squeezing with force F each, friction can hold up to 2 * mu * F.
To hold weight m * g while the arm also accelerates the object (a), with a safety factor S:
    F = S * m * (g + a) / (2 * mu)
mu is the friction coefficient between the finger and the object. Hard PLA on smooth
objects is low; soft TPU is much higher. The mu values below are rough guesses: measure
your own (tilt a board until the object slides: mu = tan(angle)).
"""
G = 9.81
SAFETY = 2.0
ARM_ACCEL = 3.0          # m/s^2: a brisk move of the arm

OBJECTS = [              # name, mass (kg)
    ("egg", 0.060),
    ("full 330 ml can", 0.350),
    ("AA battery", 0.023),
]
FINGERS = [("PLA", 0.3), ("TPU", 0.8)]


def squeeze(mass, mu):
    return SAFETY * mass * (G + ARM_ACCEL) / (2 * mu)


if __name__ == "__main__":
    print(f"safety factor {SAFETY}, arm acceleration {ARM_ACCEL} m/s^2")
    for name, mass in OBJECTS:
        row = ", ".join(f"{f} (mu {mu}): {squeeze(mass, mu):4.1f} N" for f, mu in FINGERS)
        print(f"{name:16s} {mass * 1000:4.0f} g  ->  {row}")
