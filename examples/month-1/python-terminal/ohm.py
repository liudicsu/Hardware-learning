"""ohm.py — command-line Ohm's law and voltage divider calculator."""

import argparse
import sys


def current(volts: float, ohms: float) -> float:
    """Return the current, in amps, through a resistance at a given voltage."""
    if ohms <= 0:
        raise ValueError("ohms must be positive")
    return volts / ohms


def divider(vin: float, r1: float, r2: float) -> float:
    """Return the output voltage of a two-resistor divider, in volts."""
    if r1 <= 0 or r2 <= 0:
        raise ValueError("resistances must be positive")
    return vin * r2 / (r1 + r2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ohm's law and voltage divider calculator"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_current = sub.add_parser("current", help="I = V / R, printed in mA")
    p_current.add_argument("--volts", type=float, required=True)
    p_current.add_argument("--ohms", type=float, required=True)

    p_divider = sub.add_parser("divider", help="Vout = Vin * R2 / (R1 + R2)")
    p_divider.add_argument("--vin", type=float, required=True)
    p_divider.add_argument("--r1", type=float, required=True)
    p_divider.add_argument("--r2", type=float, required=True)

    args = parser.parse_args()

    if args.command == "current":
        ma = current(args.volts, args.ohms) * 1000
        print(f"{ma:.1f} mA")
    elif args.command == "divider":
        v = divider(args.vin, args.r1, args.r2)
        print(f"{v:.3f} V")


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
