# 11.6 humanoid-wbc-overview

`lipm_track_toy.py` — planar linear inverted pendulum (LIPM) CoM sway with a ZMP limit and a capture-point fall check (stdlib).
ASAP numbers printed alongside are **paper constants** (arXiv 2502.01143 Table V), not toy measurements.
Buying a humanoid is **not required**; Isaac / MuJoCo training and on-robot sim2real steps are not run on this page.

`floating_base_contact_toy.py` — stdlib CPU deepen toy; run `python3 floating_base_contact_toy.py` in this directory.
No hardware, wiring or packages required. Expected stdout: `../expected/floating_base_contact_toy.txt`; run `bash examples/month-11/check.sh` from the repo root.
Six planar DOFs, no arm, two-row point constraint; finite-difference/JcN/residual assertions. Point force screen omits moments and cannot certify full point-wrench feasibility. No humanoid/Isaac/MoCap runs (本页未运行).
