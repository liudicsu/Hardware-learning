# Batch-28 PR1 sources

Unit: H1 JointLimiter enable-scope and coupled saturation (`ros2-hardware-interface`, +180 → 780). Site **45540** = 45360+180; M8 **4530**; still 71 lessons. Branch `feat/joint-saturation-limiter` from `06f937610f42489334ac3652197205e190d0c456`. **After this PR, M8 is the new sole heaviest month: 60 min above M9 / M10 = 4470, 150 min above M6 = 4380.** M11 stays 4350 in this PR. Disclosed, not a dump onto M9 / M10 or an avoided host. Parent accepted the 2-unit batch and Q4 contract stand-in; this PR is H1 only.

## Pins actually opened (re-fetched live at writing)

These are official documentation pages, not arXiv records: no Comments header and no journal-ref field were present, and none was invented.

- Official concept page *Joint Limiting for ros2_control*, ROS2_Control Jazzy Nov 2026 documentation, https://control.ros.org/jazzy/doc/ros2_control/hardware_interface/doc/joint_limiting.html — curl **200**; fetched-HTML sha256 `ff4685bc19bf0f9c390aa3cf19cf66bdadc3d649ce6ce87cd93008e8d57923b7`; `Last-Modified: Fri, 20 Nov 2026 05:38:53 GMT` = 2026-11-20 13:38:53 Asia/Shanghai. Identical hash and Last-Modified to the parent re-check; no hash drift. Sections *Configuration of Limits* and *Description of the Limiter Algorithms* are still literally `tba`. Official typo `controller_manger` is still present and is quoted as written. Matching source RST on branch `jazzy` at commit `c61a9d56880fc06da47a9ad0786101d72b9f1bf2` (2026-01-29 10:15:48 UTC = 2026-01-29 18:15:48 Asia/Shanghai), raw https://raw.githubusercontent.com/ros-controls/ros2_control/c61a9d56880fc06da47a9ad0786101d72b9f1bf2/hardware_interface/doc/joint_limiting.rst — curl **200**; raw sha256 `5872c60fb2f5f99c2cce89872f9d26da318017d66e87cb85297853db50565643` (identical to the parent pin; raw GitHub has no Last-Modified header).
- Official Jazzy controller-manager userdoc, https://control.ros.org/jazzy/doc/ros2_control/controller_manager/doc/userdoc.html — curl **200**; fetched-HTML sha256 `b208108a52b28875955d55e978c9b089ebb0a1eabe4fe97a70a456350f3848d5`; `Last-Modified: Fri, 20 Nov 2026 05:38:51 GMT` = 2026-11-20 13:38:51 Asia/Shanghai. Identical hash to the parent re-check; no hash drift. Parameter `enforce_command_limits` (bool, read-only, default **false**): if true, out-of-limit commands are clamped “depending on the type of configured joint limits”; if inside, they are passed through; if false, no limits are enforced.
- Official Jazzy API docs, `joint_limits::JointSaturationLimiter`, https://control.ros.org/jazzy/doc/api/classjoint__limits_1_1JointSaturationLimiter.html — curl **200**; fetched-HTML sha256 `2454e14a7a56a3ddcfb9b02067b22fd1ac0aeb4ad33d770e6d6ec0df6d252ff0`; `Last-Modified: Fri, 20 Nov 2026 05:38:50 GMT` = 2026-11-20 13:38:50 Asia/Shanghai. Identical hash to the parent re-check; no hash drift. Claims used: position then velocity then acceleration; may limit lower than the specified box; “if a joint is close to its position limit, velocity and acceleration will be reduced accordingly”; partial limits for continuous joints; may throw `std::runtime_error` if the actual position is out of bounds when commanding position. The sibling `JointLimits` URDF-mapping page was **not** opened in this PR; no YAML keys were invented.
- Implementation sources `joint_saturation_limiter.cpp` / `joint_limits_helpers.cpp` were opened in the survey as a cross-check only and are **not** presented as the official documented algorithm (parent Q4: labeled contract stand-in; official *Description of the Limiter Algorithms* is still `tba`). Official plugin / `ros2_control_node` 本页未运行.

Documentation-log constants such as position `[-1, 1]`, velocity `1`, effort `100` stay 以文档为准 and are not toy measurements. Lesson-chosen toy limits and `dt` (`DT = 0.1000`, `POS_MIN = -0.5000`, `POS_MAX = 0.5000`, `V_MAX = 1.0000`, `A_MAX = 5.0000`) were named on the page before the official first run.

## Official first run

`joint_saturation_limiter_toy.py`, 2026-11-20 16:03:43 Asia/Shanghai, byte-identical on rerun. Expected sha256 `0c728e72062485b7a584d87c05fc66d4e4394f0efe80ff78364108a3c249d3dd`. Official `expected/` was not retuned.

## Pre-declared cells

All held and are disclosed in the en/zh results.

- far_modest: C-B `pos_violation 0.0000+-0.0000`, **tie: identical on every seed**. Declared may exact-tie or near-tie; held as an exact tie; kept. C reports a derived `a = 3.0000` from the velocity step; the remaining-distance contract still exact-ties.
- near_limit_large_v: C `pos_violation 0.0000+-0.0000` (`v = 0.4000`, `room_hi/dt = 0.4000`, `next_pos = 0.5000`). B still steps to `0.5600` (`pos_violation 0.0600+-0.0000`) — a one-`dt` step that cannot stay inside the position box (lose kept). A steps to `0.6100` (`pos_violation 0.1100+-0.0000`). Paired C-B `pos_violation -0.0600+-0.0000`, **clear**, 5/5; paired C-A `-0.1100+-0.0000`, **clear**, 5/5. Kept.
- continuous_no_pos_limits: `pos_violation=n/a`; no position box is invented. C-B `vel_box_violation 0.0000+-0.0000`, **tie: identical on every seed**. A remains at `vel_box_violation 0.5000+-0.0000`. Kept.
- actual_pos_out_of_bounds: C `throws=1` (`actual position is out of bounds when commanding position`); A and B return a command and do not raise. Kept.

Named alternative `ALT_VEL_BOX_ONLY` was printed on the same streams and not adopted (on `near_limit_large_v` it matches B's `pos_violation 0.0600+-0.0000` and is clearly worse than official C).

## Post-first-run disclosures

There was no official toy or `expected/` change after the first run. Lesson prose (including the SimOutput embedding and the results / work-plan wording), hooks, curriculum, plans, sources, README typography and tip locks were written after those figures were frozen. A later postbuild visible-markdown check required wrapping the doxygen class URL (`classjoint__limits_1_1…`) in backticks in the en/zh lesson so the underscores would not leak as emphasis; official expected/ was not retuned. No lock relaxed. Existing `lifecycle_sm_toy.py`, `servo_bus_sim.py` and `can_fault_confinement_toy.py` were not retuned. `kinematics.py`, `grip_sweep.py`, `package.json` / lockfile, and `.github/workflows` are untouched.

## Mismatch with §9

None.

## Lock changes

New batch-28 PR1 block in `tools/check_diagrams.mjs` (toy, expected, CRN, label order, required enable-scope / coupled-saturation contrast, sources, plans, README, declared regimes) plus `tools/test_b28p1_joint_saturation_limiter_toy.py`. Tipped site-total, host-minute, month-total and Current-header locks only (45360→45540, M8 4350→4530, ros2-hardware-interface 600→780, README `45 360`→`45 540`). Historical strings inside already-written plan/sources files were not edited, including `Current / 当前：**M8 4350 min**, Batch-25 PR2`. M11 4350 and site 45720 were not tipped. No lock relaxed.

- README `/45 360/` and `约 45 360 分钟` → `/45 540/` and `约 45 540 分钟`.
- Curriculum sum checks `45360` → `45540`; live M8 sum checks 4350→4530; live host-minute check 600→780 on ros2-hardware-interface (including the Batch-6 PR2 host-minute row).
- Current-curriculum month table: M8 4350→4530; M11 stays 4350.
