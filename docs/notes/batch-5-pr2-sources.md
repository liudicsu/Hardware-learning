# Batch-5 PR2: sources, protocol and limitations

2026-11-06 (Asia/Shanghai, UTC+8). Base `e5ac7034785681e21ae5b70555227fd8fcf38e91`; `/workspace/hl-b5p2`, branch `feat/stereo-multirobot`. Read proposal H5/H2 and §9 LOCKED. `node_modules` is hardlinked (`cp -al`), not a symlink.

## Sources actually opened and curl-verified

| Source | HTTP | Read/use |
|---|---|---|
| https://raw.githubusercontent.com/opencv/opencv/4.x/doc/py_tutorials/py_calib3d/py_depthmap/py_depthmap.markdown | 200 | Official OpenCV tutorial source: equivalent triangles, d=Bf/Z, disparity search range and noisy correspondence. |
| https://gamma-web.iacs.umd.edu/ORCA/ | 200 | Primary ORCA authors' page: half responsibility and low-dimensional LP; our reciprocal-stop sketch is NOT the full velocity-obstacle/LP method and inherits no guarantee. |
| https://arxiv.org/html/2509.25097 | 200 | Roche, Sebastián, Montijano: methodology and experiments; trajectory-length curriculum and noisy egocentric observations reconstructed from global demonstrations. Reading only. |
| https://arxiv.org/abs/2509.25097 | 200 | Paper metadata/resource pointer. Paper numbers 以论文为准. |

The rendered OpenCV docs URL https://docs.opencv.org/4.x/dd/d53/tutorial_py_depthmap.html redirects to 4.13.0 and remains **curl403**. Its readable page was opened, but the resource deliberately uses the official source that actually returns200. No false HTTP200 claim for docs.opencv.org.

## H5 contract

- Synthetic f=600px, B=.06/.24m, sigma_d=.25px; same true depths and identical disparity-error tuple across all conditions. Uniform bounded noise avoids pretending that unbounded Gaussian reciprocal moments are well-behaved near zero.
- 10000 independent antithetic pairs, not20000 independent observations. Zero sample-mean disparity error isolates nonlinear reciprocal bias. MC population SD, mean bias, RMSE and tolerance hits are distinct; no binomial CI inferred.
- Compare actual q=.125px rounding with the approximate independent q²/12 model. Phase can reduce measured variance in a particular row; not a universal quantization benefit.
- d<=0 or d>64px invalid, no epsilon clipping. Invalids count as misses; any invalids suppress unconditional MC moments (NA). Linear sigma on invalid rows is only a formal prediction. Exact continuous uniform log expectation applies only for positive support d0>a.
- Far short baseline: continuous linear sigma25m, MC SD41.901502m, bias15.575066m; exact bias15.752296m. Quantized MC SD47.936071m, bias16.878823m. Long baseline improves those far rows but fails all near-depth samples at.75/2m under the same disparity range.
- Nominal min-range .5625/2.2500m. Occlusion/common-FOV trade-offs explained, not simulated. Not hand-eye, multi-view extrinsics or 3DGS; real rectification/matching 本页未运行.

## H2 contract

- Two holonomic discs r=.22m, .60m corridor, common map/route; cannot pass side by side. Five independently sampled start/goal scenes, seeds926–930. Immutable time-indexed neighbor-noise tuple reused across arms; paths need not yield identical observed states.
- All arms vmax=.6m/s, amax=.8m/s², dt=.05s, deadline24s. Vector speed/delta-v assertions include arrival latch. Piecewise-linear positions; acceleration is the discrete per-tick velocity change, not a continuous actuator model. No wall projection/teleport.
- Ignore uses own route. Mutex has **EXTRA reliable communication/shared reservation**, with fixed priority and actual arrival release; no future oracle. ORCA-lite is explicitly only an **ORCA-inspired reciprocal-stop sketch**, not full ORCA. The proposal permits simple reciprocal stop. Each agent takes half the clearance/horizon approach budget; no side choice/back-out, nonholonomic dynamics or formal safety claim.
- Segment-exact min separation, overlap-entry episodes (no contact impulses), actual arrival/timeout, capped mean with explicit24s substitution, deadline misses, finite deadlock/starvation proxies. The proxies are not infinite-liveness proofs and can overlap.
- Results retain failures: ignore5 collision episodes; mutex0 collisions but5 deadline misses; reciprocal-stop0 collisions but10 misses/5 deadlock runs. Tight deadline penalizes sequential scheduling; not proof of permanent mutex deadlock. All arms fail some part of collision-free/both-arrive-before-deadline; no winner presumed.
- No IL/LEMURS/VMAS replication or paper performance attribution. Real fleet/communications 本页未运行.

## Minutes, placement and regression coverage

20310+180+210=**20700**, still71 lessons. M5=1620+180=**1800**, M9=2340+210=**2550**. Independently summed all71 entries: M1–M11 = 870/1650/1470/1620/1800/1350/2070/2670/2550/1650/3000. No arithmetic mismatch; PR3's final batch totals are not applied early.

All additions/code/stdout/exercises precede the sole final Summary in both languages. Camera-calibration previously had **no Summary** in either language: created symmetric final summaries with one legacy intrinsics reminder plus the new stereo sentence. Existing nav-arm Summary retained and extended. New M5 plan created (no current month-5-plan existed); historical follow-up note preserved. Added reachable locks before final process.exit for placement, exact code/stdout, units, numerical failure rows, information, kinematics, source pointers and minutes. No pre-existing expected output changed.

## Tool fallback and checks

opencode DeepSeek→GLM→MiMo free models each emitted only a startup banner and timed out20s (exit124), no edits. Fresh catalog has no LongCat/MiniMax free models. Implemented locally under the requested worktree workflow.

PASS: diagrams **11007 checks/0failed**, widgets680/0, Wokwi8diagrams/16cards/0problems, quotes330blocks/268simulated outputs/0problems; full affected M5/M9 check.sh; lint; next typegen; tsc --noEmit; CI=1 production build/postbuild, including all178 pages' visible markdown/percentage/base-path checks. First build caught five Chinese strong-label delimiters rendered literally; corrected punctuation placement, then full export passed. git diff --check passes. CI status is reported on the PR after push, not invented here.
