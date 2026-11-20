# Batch-27 PR2 sources

Units: H3 potential-based reward shaping (`rl-manipulation-sim`, +180 → 600) and H4 official Servo collision-proximity scale (`moveit-servo`, +180 → 360). Site **45180** = 44820+360; M7 **4050**, M9 **4470**; still 71 lessons. Branch `feat/potential-shaping-servo-collision` from `1e3f23f0534a5f3d84170efd2f01e0dc7f57a4e8`. **M9 = 4470 is 90 min above current heaviest M6 = 4380**; disclosed, not a dump onto M8 / M11.

## Pins actually opened

- Ng, Harada, Russell, “Policy invariance under reward transformations: Theory and application to reward shaping,” 10-page Berkeley CS287 Fall 2009 course copy https://people.eecs.berkeley.edu/~pabbeel/cs287-fa09/readings/NgHaradaRussell-shaping-ICML1999.pdf ; curl 200; sha256 `e83f9d13b8c5415d78a187a0b9000c5ab6aa90f3029d5c957f5c46caaabed207`. Title page + Theorem 1 + Corollary 2 + the introduction’s shaping bugs were read visually from rendered pages (Type 3 fonts break `pdftotext`). Title-page typography: sentence-case title as above; authors Andrew Y. Ng, Daishi Harada, Stuart Russell; Computer Science Division, University of California, Berkeley. This copy’s title page does **not** itself print a proceedings / journal-ref banner; none was invented. Theorem 1: F is potential-based if there exists Φ such that F(s,a,s')=γΦ(s')-Φ(s) (with S\{s0}=S if γ<1); necessary and sufficient for policy consistency of M'=(S,A,T,γ,R+F) vs M; sufficiency — every optimal policy in M' is optimal in M and vice versa; necessity — if no such Φ, there exist T,R such that no optimal policy in M' is optimal in M. Corollary 2 (Φ(s0)=0 if γ=1): Q_{M'}(s,a)=Q_M(s,a)-Φ(s), V_{M'}(s)=V_M(s)-Φ(s). Introduction bugs (Randløv and Alstrøm bicycle riding in circles; soccer agent vibrating on the ball) 以论文为准. The earlier `ai.stanford.edu/~ang/papers/icml99-rewardshaping.pdf` URL 404’d; this course copy is the body actually used. ManiSkill / SB3 / a real arm 本页未运行.
- moveit2_tutorials commit **`6ea5a7425d58c4b4d36788a8d105bf7715fe77d7`** (2026-11-18T23:53:55Z = 2026-11-19 07:53:55 Asia/Shanghai, `main` tip at fetch):
  - `doc/examples/realtime_servo/realtime_servo_tutorial.rst` blob **`151ea6dc5625bd89cb98a809c270cafbfe06d9ef`**, sha256 `68ce415dd7b5fef7fcb7d7158d344b339924e3e597295e29dddb94a12fdaa6b5`. Singularity *and* collision “scale down the velocities when approaching singularities or collisions (self collision or collision with other objects)”; collision checking and smoothing are optional (`check_collisions`, `use_smoothing`). Official wording 以文档为准.
  - `doc/examples/realtime_servo/config/panda_simulated_config.yaml` blob **`2b6c0f5b51bc754630a6e7602e0f1b94556aa591`**, sha256 `41a7f006c243fc54058b794fcf6848254f5fd6c94637a992775b16085f644adf`. `self_collision_proximity_threshold: 0.01`, `scene_collision_proximity_threshold: 0.02`, `check_collisions: true`, `collision_check_rate: 10.0`. Those distances are opened demo-config constants, 以文档为准, not vendor-universal defaults and not toy measurements. MoveIt / FCL / official keyboard demo 本页未运行.
- https://moveit.picknik.ai/main/doc/examples/realtime_servo/realtime_servo_tutorial.html — curl 200; HTML rendering used as a cross-check, not a second conflicting body.

## Official first runs

Both toys, 2026-11-20 13:09:53 Asia/Shanghai, byte-identical on rerun.

- `potential_based_shaping_toy.py` expected sha256 `33f2df8cf399e2c6de96d3ca734bc9e687139557b436ecc68c387ebbaf03cd5d`.
- `servo_collision_proximity_toy.py` expected sha256 `525c20a39dd4ab19d9311cdbb818362347893091554d8e6f9cddeb457d653882`.

## Pre-declared cells

All held and are disclosed in the en/zh results.

- H3 acyclic_corridor: A, B and C exact-tie on success and original_return (`0.0000+-0.0000`, identical on every seed). Declared may near-tie; held as an exact tie; kept.
- H3 distractor_cycle: B preserves the unshaped optimum (paired B-A exact-tie on success, original_return `0.8100+-0.0000`, and policy_agree_A). C consistently prefers the cycle (paired C-A original_return `-0.8100+-0.0000`, clear, 5/5; uses_cycle `1.0000+-0.0000`).
- H3 constant_phi: B_const exact-ties A on every metric. C loses on original-task return (`-0.8100+-0.0000`, clear, 5/5).
- H3 手算: potential 2-cycle sum `0.0000`; illegal cycle sum `1.0000`.
- H4 far_scene: A and B exact-tie on progress `0.0500+-0.0000` (declared may exact-tie or near-tie, held as an exact tie). C over-conservative loses on progress (paired C-A `-0.0253+-0.0000`, clear, 5/5).
- H4 in_band_scene: B consistent collision reduction (paired B-A collision_steps `-41.0000+-0.0000`, max_penetration `-0.0200+-0.0000`, clear, 5/5). A (no scale) loses on collisions.
- H4 in_band_self: B consistent collision reduction (paired B-A collision_steps `-71.0000+-0.0000`, max_penetration `-0.0350+-0.0000`, clear, 5/5). A (no scale) loses on collisions.

Named alternatives (Phi = -2 * distance; quadratic scale) were printed on the same MDPs / timeline and not adopted.

## Post-first-run disclosures

There was no official toy or `expected/` change after the first run. Lesson prose, hooks, curriculum, plans, sources, README typography and tip locks were written after those figures were frozen. Official expected/ was not retuned. No lock relaxed. Existing sparse-versus-dense and HER toys on `rl-manipulation-sim` were not retuned; existing `servo_loop_sim.py` (κ>12, scaled_rows=3, lesson-chosen thresholds) was not retuned. `kinematics.py`, `grip_sweep.py`, `servo_loop_sim.py`, `package.json` / lockfile, and `.github/workflows` are untouched.

## Mismatch with §9

None.

## Lock changes

New batch-27 PR2 block in `tools/check_diagrams.mjs` (toys, expected, CRN, label order, Theorem 1 / demo-config contract, sources, plans, README, declared regimes) plus `tools/test_b27p2_shaping_servo_toys.py`. Tipped site-total, host-minute, month-total and Current-header locks only (44820→45180, M7 3870→4050, M9 4290→4470, rl-manipulation-sim 420→600, moveit-servo 180→360). Historical strings inside already-written plan/sources files were not edited, including `Current / 当前：**M7 3870 min**, Batch-25 PR2` and `Current / 当前：**M9 4290 min**, Batch-23 PR3`. No lock relaxed.

- README `/44 820/` and `约 44 820 分钟` → `/45 180/` and `约 45 180 分钟`.
- Curriculum sum checks `44820` → `45180`; live M7/M9 sum checks 3870→4050 and 4290→4470; live host-minute check 420→600 on rl-manipulation-sim (HER deepen row).
