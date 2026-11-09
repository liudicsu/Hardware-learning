#!/usr/bin/env python3
"""Control-flow regression only: record check calls, do not fake CAD validation.
Real absent-OpenSCAD Python comparisons run separately in local/CI check.sh.
"""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
# Observe the real host before constructing either isolated presence-probe fixture.
print("m3 host OpenSCAD: " + (shutil.which("openscad") or "not found on PATH"))
FULL = [
    "cad-bracket.txt", "cad-bracket-tight.txt", "cad-bracket-assert.txt",
    "fdm-snap_fit.txt", "fdm-case.txt", "fdm-case-clash.txt", "fdm-case-clash-tight.txt",
    "tr-gear_calc.txt", "arm-sts_packet.txt", "grip-finger.txt", "grip-force.txt",
    "fingertip_retarget_toy.txt", "backlash_loop_toy.txt", "abs_vs_incr_power_on_toy.txt",
    "gdt_tolerance_stack_toy.txt",
    "gear_efficiency_load_toy.txt",
    "lead_lag_vs_pid_toy.txt",
]
CAD = {name for name in FULL if name.startswith(("cad-bracket", "fdm-case")) or name == "grip-finger.txt"}
script = (ROOT / "examples/month-3/check.sh").read_text()
# Replace only the checker with a call recorder; leave guards and every invocation intact.
spy, count = re.subn(r"^check\(\) \{.*?^\}",
                     lambda _: "check() { printf 'CHECK %s\\n' \"$1\"; }",
                     script, count=1, flags=re.M | re.S)
assert count == 1
with tempfile.TemporaryDirectory(prefix="m3-cad-guard-") as tmp:
    directory = Path(tmp)
    bindir = directory / "bin"
    bindir.mkdir()
    for name in ("dirname", "mktemp", "rm"):
        target = shutil.which(name)
        assert target
        (bindir / name).symlink_to(target)
    # Deterministically simulate the pre-existing optional SDK dependency being absent.
    probe = bindir / "python3"
    probe.write_text("#!/bin/sh\nexit 1\n")
    probe.chmod(0o755)
    test_script = directory / "check-spy.sh"
    test_script.write_text(spy)
    for available in (False, True):
        if available:
            (bindir / "openscad").symlink_to(shutil.which("true"))
        result = subprocess.run([shutil.which("bash"), str(test_script)],
                                env={"PATH": str(bindir)}, text=True, capture_output=True, check=True)
        calls = re.findall(r"^CHECK (\S+)$", result.stdout, re.M)
        assert calls == (FULL if available else [name for name in FULL if name not in CAD]), calls
        assert ("SKIP CAD: openscad not found" in result.stdout) == (not available)
print("m3 CAD guard: absent keeps all Python calls; present keeps all original checks/order (control-flow spy, not a CAD run)")
