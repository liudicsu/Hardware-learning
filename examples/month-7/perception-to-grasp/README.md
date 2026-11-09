# perception-to-grasp

- `handeye_toy.py` — synthetic eye-in-hand AX=XB (Park SVD; NumPy). Mirrors OpenCV `calibrateHandEye` I/O.
- `grasp_from_mask.py` — synth mask+depth → camera centroid → base-frame grasp candidate (stdlib).
- `antipodal_force_closure_toy.py` — planar two-finger antipodal contacts, force closure and an ε proxy vs a random pick and a frictionless grasp (stdlib; `expected/antipodal_force_closure_toy.txt`).

SAM2 / MoveIt / real cameras stay「本页未运行」.
