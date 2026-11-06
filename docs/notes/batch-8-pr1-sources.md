# Batch-8 PR1 source, scope and validation audit

Base:6afd38362e289a95fb3334d90a5eb23e196d44b8 (#132 merged). Authoritative current proposal §9 and §4–5: H1+H2 only; H3 IBVS is PR2. No arithmetic mismatch: M4 1830+150+150=2130; site23610+300=23910;71 lessons. All193 prior expected files must remain byte-identical.

## Opened primary Jazzy documentation

Curl -L verified HTTP200 and page contents read on 2026-11-06 (Asia/Shanghai UTC+8):

- `ros2-sros-intro` — https://docs.ros.org/en/jazzy/Tutorials/Advanced/Security/Introducing-ros2-security.html — HTTP200.
- `ros2-sros-keystore` — https://docs.ros.org/en/jazzy/Tutorials/Advanced/Security/The-Keystore.html — HTTP200.
- `ros2-sros-acl` — https://docs.ros.org/en/jazzy/Tutorials/Advanced/Security/Access-Controls.html — HTTP200.
- `ros2-composition` — https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Composition.html — HTTP200.
- `ros2-intraprocess` — https://docs.ros.org/en/jazzy/Tutorials/Demos/Intra-Process-Communication.html — HTTP200.
- `ros2-composable-launch` — https://docs.ros.org/en/jazzy/How-To-Guides/Launching-composable-nodes.html — HTTP200.

The keystore and access-control pages distinguish enclave identity from actual restrictive permissions (edited/re-signed policies, DDS rt/ names). Intro confirms Enforce missing-material startup denial, per-terminal exports and CLI override. Composition confirms component_container and run-time load; intra-process demo qualifies pointer/ownership-based zero-copy; launch guide confirms ComposableNodeContainer/ComposableNode. No real DDS or ROS container execution performed.

## Models / reproducibility

Tried opencode/deepseek-v4.1-flash-free, then glm-5.3-flash-free, then mimo-v2.6-flash-free for25s each; all timed out with startup headers only (exit124), no generated content. LongCat and MiniMax free IDs were absent from `opencode models`. Implemented locally. Existing clean worktree was repurposed via a fresh branch from origin/main; node_modules is a real hardlinked directory (`cp -al`, matching inode verified), not a symlink. The dropped hardware branch has no commits and remains local; no unrelated worktree modified.

ACL is an exhaustive policy table (24 shared requests), not cryptographic authentication, encryption, network discovery, QoS or lifecycle. Missing-material arm intentionally loses intended traffic too. Composition is a declared deterministic scheduler accounting model: same stream and callback work, healthy and identical fatal component-process fault; poll counts are neither context switches nor elapsed time. No stochastic seeds are applicable. Tests independently enumerate requests/jobs, denial reasons, conservation, group placement and fault blast radius across additional sizes; source/stdout/summary placement/minutes locked by check_diagrams.

## Local validation

Required suite: check_diagrams (23 diagrams /12116 checks), check_widgets (680), check_wokwi (8 diagrams/16 cards), check_quotes (366 code blocks/302 outputs), month1–11 check.sh, lint, Next typegen, tsc --noEmit, production build and postbuild HTML checks (178 pages). Also run the independent3-case exhaustive/perturbation test suite. Existing optional environment guards may skip OpenSCAD CAD/arm SDK, real ROS Jazzy/colcon and MuJoCo; the new stdlib examples run before the ROS guard. No workflow edits. The first build caught Chinese strong-delimiter punctuation in exercises; corrected and revalidated, without weakening a check.
