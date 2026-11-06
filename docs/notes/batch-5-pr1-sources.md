# Batch-5 PR1: source, protocol and limitation audit

2026-11-06 (Asia/Shanghai, UTC+8). Base39215d6cbb06c9dd9ff4c6a5587e3935e620a151. Followed proposal §9 LOCKED corrections before implementation. New worktree /workspace/hl-b5p1,branch feat/backlash-dmm-kf;node_modules hardlinked,not a symlink.

## Opened and curl-verified

| Source | Result | Read/use |
|---|---|---|
| https://www.wescottdesign.com/articles/Friction/friction.pdf | HTTP200,pdftotext | §1 stiction/Coulomb/backlash hidden state;§3.2 P/I deadband,keep D,stored integral/leak and empirical band choice. Toy is our two-inertia load-friction model,not paper numerical reproduction. |
| https://physics.nist.gov/cuu/Uncertainty/typeb.html | HTTP200,readable full page | Rectangular half-width /√3;distribution assumptions,standard uncertainty versus limits/coverage. |
| https://www.itl.nist.gov/div898/handbook/mpc/section5/mpc55.htm | HTTP200,readable full page | Sensitivity derivatives,RSS,independence/covariance and linearization. |
| https://rlabbe.github.io/Kalman-and-Bayesian-Filters-in-Python/ | HTTP200,readable introduction | Existing KF resource reverified;recursive filter equations and discrete Q/R are derived explicitly in lesson,not claimed as a copied book experiment. |

BIPM JCGM publications landing page was also opened,not used as a claim to have read the GUM PDF. Attempted Welch/Bishop PDF returned404;not read/cited. **No real DMM datasheet opened**;all spec values explicitly synthetic.

## H3 physical/control contract

- Output-referred rad/N·m/kg·m²,two inertias,elastic deadzone coupling. Explicit load static FS=.4 and sliding FC=.02;deliberately strong synthetic drop makes stick-slip legible,not a typical real reducer spec. Zero shared encoder noise;identical IC/reference/gains/saturation/integral clamp. Extra q_load information disclosed;D motor velocity available to all.
- P/I deadband only;D unchanged. In-band I leaks2/s,explicitly disclosed,not a hidden algorithm change. Correct bhat=.04 measured load-error band[.033429,.033429]rad;conditional static allowance ±.053333rad. Too-small.004 under-budgets play;too-large.12 accepts.067457rad error. No accuracy winner presumed.
- Finite-window hunting/limit-cycle **candidate**,not a periodic-orbit proof. Needs p-p>.005rad,>=3 load-velocity reversals and both tail halves p-p>.002rad. Friction+I load arm p-p.047514rad/4reversals;no-friction and no-I controls do not meet candidate criterion.
- dt=.002/.001/.0005 gives p-p.047514/.046795/.047466rad and4/6/5reversals,all classified hunting. Additional sensitivity FS=.4,FC=.1 does not hunt with the same gains,so “both ingredients” is a selected-regime result,not inevitability. Old four-second backlash code/stdout untouched;perpetual-hunting prose qualified symmetrically.

## H4 uncertainty contract

Synthetic %reading+%FS total half-width L per channel. Rectangular total error implies u=L/√3;do not RSS the already-summed limit terms. Independent V/R channels only;real instrument correlation/loading/calibration not simulated. Derived I=V/R,cV=1/R,cR=-V/R². Compare RSS **standard uncertainty** against first-order worst-case **linear limit** and exact positive-denominator corner limit.20k shared standardized MC pairs,seed113;not repeated measurements removing systematic offsets. No95%/CAT/IEC certificate invented.

## H6 equal-tuning contract

- Declared sample-held bias + independent gyro/accel white noise. Q0=diag((sigma_g dt)²,sigma_rw²dt),R0=sigma_a²;not a continuous bias discretization with cross terms. Gravity-only accel-angle model excludes translational acceleration.
- Same sensor streams,initial noisy angle and zero bias prior mean. Neither estimator receives sampled true bias or truth;truth appears only in training objective/eval scorer.
- Plain complementary9α;bias-adaptive scalar complementary3×3α/kb;KF3×3 Q0/R0 scale grid. All9×3×1500=40500 updates,training201/202/203 only;frozen before held-out221–225. Equal updates,not equal FLOPs/model capacity. Added bias-adaptive comparison prevents attributing every gain merely to bias-state access.
- Report all5 eval rows,mean/population-SD/min/max;seed223 KF underperforms both complementary arms. No universal winner/significance/hardware characterization claim.

## Minutes and placement

19830+180+150+150=**20310**,still71 lessons. M1=720+150=**870**,M2=1500+150=**1650**,M3=1290+180=**1470**;other months unchanged. Independent full sum verified,no mismatch. Existing M1/M2/M3 plan files did not exist,so new incremental plan notes added rather than editing nonexistent files. All additions/code/stdout/exercises before sole final Summary;each en/zh Summary updated;reachable regression locks execute new toys. No old expected output modified.

## Tool fallback and checks

opencode DeepSeek→GLM→MiMo free models each produced only a startup banner and timed out35s(exit124),no edits. LongCat/MiniMax free models absent from catalog. Implemented locally,no CloudAgent.

PASS:check_diagrams10916 checks/0failed;widgets680/0;wokwi8diagrams/16cards/0problems;quotes326blocks/268simulated outputs/0problems;lint;next typegen;tsc --noEmit;CI=1build/postbuild including178page base-path/markdown/percentage checks. M1/M2 full check.sh pass;all three new toys match expected (also executed by regression locks);M3 gear/packet/grip-force/fingertip Python outputs match.

Extra full M3 check.sh attempt **does not pass legacy CAD outputs**:OpenSCAD absent. Installation attempt stopped because Debian apt repository returnedHTTP500/signature metadata errors;did not bypass signatures or change mirrors. Existing optional servo SDK comparison skipped(not installed). These are environment limitations,not regenerated expectations or claimed successful CAD checks.
