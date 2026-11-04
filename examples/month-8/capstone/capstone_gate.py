#!/usr/bin/env python3
"""capstone_gate.py: check a capstone project folder for Month 8 shared gates.

Looks for (stdlib text rules only — cannot judge quality):
  track          TRACK.md or README names track A/B/C
  safety         bench_safety_checklist.md (or SAFETY.md) with e-stop / 急停
  devops         .devcontainer/ or a workflow mentioning action-ros-ci / ros-ci
  eval_protocol  README mentions 20 starts / Wilson / held-out (or 未见 / Wilson)
  portfolio_8    delegates to Month 6 portfolio_check on the same folder

usage:
  python3 capstone_gate.py PROJECT_DIR
  python3 capstone_gate.py --demo    # runs against bundled sample_project
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PORTFOLIO = os.path.normpath(
    os.path.join(HERE, "..", "..", "month-6", "specialisation-portfolio", "portfolio_check.py")
)


def read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def find_safety(root: str) -> str | None:
    for name in ("bench_safety_checklist.md", "SAFETY.md", "safety.md"):
        p = os.path.join(root, name)
        if os.path.isfile(p):
            return p
    return None


def check(root: str) -> int:
    root = os.path.abspath(root)
    readme = os.path.join(root, "README.md")
    if not os.path.isfile(readme):
        print(f"FAIL  no README.md under {root}")
        return 1
    text = read(readme)
    missing = 0

    def gate(name: str, ok: bool, detail: str) -> None:
        nonlocal missing
        missing += not ok
        print(f"  {'ok     ' if ok else 'MISSING'} {name:<14} {detail}")

    print(f"{os.path.basename(root)}: capstone gates")

    track_ok = bool(
        re.search(r"\btrack\s*[ABC]\b|轨道\s*[ABC]|Track\s*[ABC]", text, re.I)
    ) or os.path.isfile(os.path.join(root, "TRACK.md"))
    gate("track", track_ok, "README/TRACK names track A, B, or C")

    safety_path = find_safety(root)
    safety_ok = False
    if safety_path:
        s = read(safety_path)
        safety_ok = bool(re.search(r"e-?stop|急停", s, re.I))
    gate("safety", safety_ok, "bench_safety_checklist.md (or SAFETY.md) with e-stop/急停")

    devops_ok = os.path.isdir(os.path.join(root, ".devcontainer")) or bool(
        re.search(r"action-ros-ci|ros-tooling/action-ros-ci", text, re.I)
    )
    if not devops_ok:
        wf = os.path.join(root, ".github", "workflows")
        if os.path.isdir(wf):
            for fn in os.listdir(wf):
                body = read(os.path.join(wf, fn))
                if re.search(r"action-ros-ci|ros-tooling", body, re.I):
                    devops_ok = True
                    break
    gate("devops", devops_ok, ".devcontainer or action-ros-ci workflow")

    eval_ok = bool(
        re.search(r"\b20\b.*(?:start|position|trial)|Wilson|held[- ]out|未见|起始", text, re.I)
    )
    gate("eval_protocol", eval_ok, "M6 protocol: 20 starts / held-out / Wilson")

    # portfolio 8/8
    if not os.path.isfile(PORTFOLIO):
        gate("portfolio_8", False, f"cannot find portfolio_check.py at {PORTFOLIO}")
    else:
        proc = subprocess.run(
            [sys.executable, PORTFOLIO, root],
            capture_output=True,
            text=True,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        m = re.search(r"(\d+)\s+of\s+8\s+present", out)
        n = int(m.group(1)) if m else -1
        gate("portfolio_8", n == 8, f"portfolio_check → {n}/8 (exit {proc.returncode})")

    print(f"  {5 - missing} of 5 gates present")
    return 1 if missing else 0


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "--demo":
        sample = os.path.join(HERE, "sample_project")
        raise SystemExit(check(sample))
    if len(sys.argv) != 2:
        raise SystemExit(__doc__.strip().splitlines()[-2])
    raise SystemExit(check(sys.argv[1]))


if __name__ == "__main__":
    main()
