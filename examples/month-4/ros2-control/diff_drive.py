"""diff_drive.py: the arithmetic diff_drive_controller does for m4bot, by hand.

A differential drive has two wheels a distance b apart (wheel_separation), each of
radius r (wheel_radius). For a body velocity v (m/s, forward) and w (rad/s,
counter-clockwise seen from above):
    v_left  = v - w * b/2
    v_right = v + w * b/2
    wheel speed (rad/s) = v_wheel / r
The turn radius is v / w: the centre of the turn lies that far to the robot's left (a
negative value: to its right); there is none when w = 0 (straight) and it is 0 when v = 0
(spinning in place).
b and r are the numbers in m4_control/config/controllers.yaml; the script checks that the
file next to it still says so. Plain Python, no ROS needed.
"""
import pathlib
import re

B = 0.28   # m, wheel_separation
R = 0.05   # m, wheel_radius

CASES = [  # name, v (m/s), w (rad/s)
    ("straight", 0.2, 0.0),
    ("straight, quiz", 0.3, 0.0),
    ("spin left", 0.0, 1.0),
    ("arc left", 0.2, 0.5),
    ("arc right", 0.3, -1.0),
    ("spin right, max", 0.0, -2.0),
    ("reverse, yaw left", -0.2, 0.5),
]


def wheels(v, w):
    """Left and right wheel speeds in rad/s."""
    v_left = v - w * B / 2
    v_right = v + w * B / 2
    return v_left / R, v_right / R


def yaml_values():
    """wheel_separation and wheel_radius as written in controllers.yaml (None if missing)."""
    path = pathlib.Path(__file__).parent / "m4_control/config/controllers.yaml"
    if not path.is_file():
        return None
    text = path.read_text()
    sep = re.search(r"^\s*wheel_separation:\s*([0-9.]+)", text, re.M)
    rad = re.search(r"^\s*wheel_radius:\s*([0-9.]+)", text, re.M)
    return float(sep.group(1)), float(rad.group(1))


if __name__ == "__main__":
    found = yaml_values()
    if found is None:
        print("controllers.yaml not found: using b and r from this script")
    elif found == (B, R):
        print(f"controllers.yaml: wheel_separation {found[0]} m, wheel_radius {found[1]} m (same as this script)")
    else:
        print(f"WARNING: controllers.yaml says {found}, this script uses {(B, R)}")
    print(f"b/2 = {B / 2:.2f} m")
    print(f"{'case':17s} {'v m/s':>6s} {'w rad/s':>7s}  {'left rad/s':>10s} {'right rad/s':>11s}  turn radius")
    for name, v, w in CASES:
        left, right = wheels(v, w)
        radius = "none (straight)" if w == 0 else "0 (in place)" if v == 0 else f"{v / w:.2f} m"
        print(f"{name:17s} {v:6.2f} {w:7.2f}  {left:10.1f} {right:11.1f}  {radius}")
