# Batch-4 polish: source and boundary audit

2026-11-06 (Asia/Shanghai, UTC+8). Base 0bd0e2c38adf27db77b4bd13e5db698e380e62f9; minutes unchanged at 19830.

- Opened and curl-verified HTTP200: https://public.acontis.com/manuals/EC-Master/3.3/html/ec-master-class-a/dc.html (existing resource); https://public.acontis.com/manuals/EC-Master/3.3/html/ec-master-class-a/dc_technical.html (Typical Bus Timing and its illustration). Added explicit SYNC0 shift-time reading pointer, not a claim of running/configuring hardware. Existing ETG.2200 PDF URL returned403; it was not read this turn and is not the verified pointer.
- Opened full Splat-Nav v2 https://arxiv.org/html/2403.02751v2 and curl-verified HTTP200. Sec. IV Eq.(2): D² ≤ χ²₃(γ), covariance rescaled by that quantile; γ=.99 in the scene convention. Sec. VI-C2 simulation comparison also sets χ²₃(γ)=4. Our k=2 is the same geometric threshold4, not the same confidence level as .99. Ideal 3-D mass Fχ²₃(4)=erf(√2)−2√(2/π)exp(−2)≈.738536; .99 needs k≈3.368. Opacity filter is independent. No calibrated physical-occupancy guarantee claimed; 以论文为准.
- Two-stage limit-switch coarse / Z-index fine homing named only, explicitly not implemented.
- SoC clipping is display-only and compresses reported differences near the bounds. Removed feedback of clipped display into the internal integrator to make that claim true; default profile stays interior, so stdout/expected remain unchanged. Embedded en/zh code mirrors updated.

## Verification

Final local PASS: check_diagrams (10786 checks,0 failed),check_widgets (680,0 failed),check_wokwi (8 diagrams/16 cards,0 problems),check_quotes (320 blocks/268 outputs,0 problems),lint,next typegen,tsc --noEmit,CI=1 build and postbuild (178 pages,base-path/visible-markdown/percentage checks). 71 lessons/19830 minutes independently summed; curriculum unchanged. All three affected toy stdout files exactly match existing expected; Month2/4/7/11 Python check suites pass. Existing ROS2 integration skipped (Jazzy not sourced),optional MuJoCo grip sweep skipped (not importable). A bound-crossing test integrate([3600,-3600],3600,.5)==[.5,0,.48] verifies clipped output is not fed back into the integrator.
