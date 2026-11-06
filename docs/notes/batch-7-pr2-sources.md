# Batch-7 PR2 source and model audit / 来源与模型审计

Base `3d74d5dc77d0902fb42b5f8d1f0bc20826046f00` (`3d74d5d`), new worktree `/workspace/hl-b7p2`, branch `feat/icp-quat`. Node dependencies hardlinked with `cp -al`, not symlinked. No workflow changes.

Opened and curl-verified on 2026-11-06 11:31 Asia/Shanghai (UTC+8). All three HTTP200; actual relevant HTML content was read, not just a successful status code.

| Source | HTTP | Saved HTML SHA256 |
|---|---:|---|
| https://www.open3d.org/docs/release/tutorial/pipelines/icp_registration.html | 200 | `2419837b812d40bcac29ed409c4e9aa1920d39209f2a8b62e1049d511caf92d6` |
| https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles | 200 | `d1a1e72fededcf5bbc2f3aa2a0933a47fa61006858a5358a75618650f157367c` |
| https://en.wikipedia.org/wiki/Slerp | 200 | `0103b8f5cb50a472be2c1ff76404c8daee7bf0804d783b3c297e4b4a155ca191` |

## Interpretation and limits

- Open3D is the authoritative project tutorial for point-point/plane objectives and target normals, not evidence that our stdlib toy executed Open3D. We explicitly reconstruct a nearest-segment 2D surface from ordered noisy scan vertices and give the same surface/matcher to both arms. No generating wall IDs or clean normal oracle; truth is only generator/scorer. The reconstructed-surface variant differs from the tutorial’s discrete nearest-point backend. Both sides get identical five seeds/scans/inits/noise/trust bounds/cap/stop. Aggregate includes failures; sampled basin only.
- Corridor rank is measured for the freshly re-associated physical distance objective, rank2 with an along-wall null. Frozen point-point pair identities falsely supply tangential anchoring and a full-rank matrix; the page explicitly reports both rather than falsely calling frozen point-point equations singular. Plane normal equations are genuinely singular. Parameter units/scaling and the no-visible-ends idealization are declared.
- Wikipedia references are explicitly secondary; independently derived active intrinsic ZYX body angular velocity Jacobian is verified with direct matrix finite differences. Quaternion storage order and earlier planar-FK sign difference are stated. Shared endpoints/steps, q/-q sign equivalence, pole rank/null, short-arc flip and near-equal fallback are tested independently. No robot/IMU/ROS runs or universal path/method winner claim.

## Model attempts

Tried opencode free models in order: DeepSeek (`opencode/deepseek-v4.1-flash-free`) timed out after40s; GLM (`opencode/glm-5.3-flash-free`) returned a read-only mathematical audit successfully. Stopped after the first successful model; MiMo therefore not needed, LongCat/MiniMax free IDs absent from catalog. Audit was not used as authority: derivative/rank and correspondence assertions were independently verified, with unsupported suggestions discarded. Implementation local; no CloudAgent.

## Minutes and preservation

No arithmetic mismatch: 22830+210+150=**23190**; M4=1620+210=**1830**, M5=1800+150=**1950**;71 lessons. This PR only; M2=2310/M8=3180 unchanged. Allocation described in correctly headed month4/month5 notes. Neither target lesson had Summary: add full whole-lesson final blocks plus the added sentence in both en/zh; code/stdout/exercises precede them.

Base actually contains **189** tracked expected `.txt` files (`git ls-tree -r 3d74d5d`), not the141 in the brief. All189 were compared byte-for-byte against the base and preserved; only two new outputs are added (191 total). Existing ROS-dependent month4 checks retain their guard; the new stdlib ICP check executes BEFORE it so missing ROS cannot skip the new regression. Existing optional local skips remain unchanged.

## Local validation

All requested commands passed: check_diagrams (23 diagrams /11803 checks), check_widgets (680 checks), check_wokwi (8 diagrams /16 cards), check_quotes (358 blocks /298 outputs), all eleven month check.sh harnesses, ESLint, next typegen, tsc --noEmit, production build and postbuild visible-markdown/percent/basepath scans (178 pages), git diff --check. Independent geometry tests run from check_diagrams.

Existing environment skips, not weakened checks: Month3 OpenSCAD CAD and optional SDK comparison; Month4 ROS2 Jazzy/colcon checks (new ICP and existing EtherCAT Python checks both ran before the guard); Month7 optional MuJoCo grip sweep. No real sensor/robot execution claimed.
