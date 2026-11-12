# Batch-17 polish sources / 来源记录

Base `83c982729b962c4c3a741d95078ac68e04a305ea` (main after #171; site **34710**). Minutes unchanged (**34710**); no lesson added or removed. control-modelling stays 780 min, cad-parametric stays 450 min.

## 1. Computed-torque FC=0 sensitivity and centre-pose stiffness (5.6 control-modelling)

The first-run table in `computed_torque_inverse_dynamics_toy.py` is unchanged (FC = 0.3 N m). A new print block, labelled **FC=0 sensitivity (added after the first run; not a pre-declared regime)**, was added after the closing lines.

- Centre pose `q = (0.3, 0.8)` rad, payload 0.5 kg (the `slow_quasi_static` mass used in the original hand calculation). The toy now prints `M11=0.5205 M12=0.1721 M22=0.09375` (same rounded values as the worked example), `(M⁻¹)22=27.1535`, `1/M22=10.6667`, stiffness `KP/(M⁻¹)22=14.7311` N m/rad against `D0 KP=M22 KP=37.5000` N m/rad, and `0.3 N m friction leaves 20.3651 mrad vs 8.0000 mrad`. The earlier hand values in the prose were 27.15, 10.67, about 14.7 vs 37.5, and about 20 vs 8 mrad; the prose now quotes the printed figures. 27.15 / 14.7 / 37.5 remain prefixes of the printed strings; 10.67 does not, so the lock markers were moved to the printed values (not relaxed).
- The same block reruns `slow_quasi_static` and `payload_mismatch` with `FC = 0` (common random numbers unchanged). Printed B−A rms is −0.1168±0.0515 mrad (slow; clear, 5/5) and −5.1016±1.3586 mrad (payload_mismatch; clear, 5/5). These two paired means match the previous unprinted side-run figures in the prose exactly; only the attribution changed: the numbers are now in `expected/` and the prose says they were added after the first run.
- en/zh no longer say the side run is "not part of the printed output" / "不在打印输出里". `expected/` was regenerated; a second run is byte-identical.

## 2. General Lamé interference formula (3.1 cad-parametric)

Wikipedia "Interference fit" (https://en.wikipedia.org/wiki/Interference_fit), fetched 2026-11-12 (Asia/Shanghai), HTTP **200**, still has no contact-pressure formula, as the lesson already states. Wikipedia "Cylinder stress" (https://en.wikipedia.org/wiki/Cylinder_stress), same day, HTTP **200**, has Lamé's thick-wall stress equations but not the combined shaft-and-hub press-fit formula and does not state that the Poisson terms cancel.

The general formula and the cancellation statement are taken from RoyMech, "Thick-Walled Cylinders – Lame Equations and Interference Fits", https://www.roymech.co.uk/Useful_Tables/Mechanics/Cylinders.html, body read on 2026-11-12 (Asia/Shanghai) via the page reader (a direct curl from this machine received HTTP 202 and did not return the body). In the Interference Fits section, with radial interference δ_r at interface radius c, hub outer radius b, shaft inner radius a, and possibly different materials:

p = δ_r / ( c · ( (1/E_h) · ((b² + c²)/(b² − c²) + ν_h) + (1/E_s) · ((c² + a²)/(c² − a²) − ν_s) ) )

For a solid shaft, a = 0 and the shaft term is (1 − ν_s)/E_s. The page states: "If the shaft is solid and both shaft and hub have the same Young's modulus and Poisson's ratio, the Poisson terms cancel from the total radial interference equation", giving p_f = δ E (b² − c²) / (2 c b²). With the toy's diametral δ = 2 δ_r, d = 2c and D = 2b, this is exactly `p = E · δ / (2 · d) · (1 − (d / D)²)`, the existing stand-in, which is kept. en/zh add the general formula, the δ_r = δ / 2 conversion, and the ν-cancellation sentence. The toy and its numbers are unchanged.

## Lock changes

- The batch-17 PR2 compact markers for the hand values `27.15`, `10.67`, `14.7`, `37.5` were updated to the printed values `27.1535`, `10.6667`, `14.7311`, `37.5000`, and extended with `20.3651`, `8.0000`. New expected lines (FC=0 block, stiffness, both B−A rms lines) were added to `outLines`. en/zh langMarkers now require the post-hoc wording. An extra `b17p2` check requires the new block in the toy and in `expected/`.
- New `b17pol` block: independent tests including the new stiffness / FC=0 assertions; printed numbers in en/zh prose; RoyMech general Lamé formula and ν cancellation in cad-parametric en/zh; original stand-in formula kept; this note; minutes 780 / 450 / site 34710. No lock relaxed; `.github/workflows` untouched.

## Models

- opencode free models (deepseek-v4.1-flash-free, glm-5.3-flash-free, mimo-v2.6-flash-free, longcat-2.5-free, minimax-m3.1-flash-free) were listed first. This is a surgical print-block and lock extension on an existing toy; it was implemented locally.

## Local validation

See the PR description (check_diagrams, check_widgets, check_wokwi, check_quotes, tools/test_*.py, month check.sh, lint, typegen, tsc, build + postbuild, CI=1 build).
