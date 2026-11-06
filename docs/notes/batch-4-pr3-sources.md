# Batch-4 PR3: opened sources, protocol and boundaries

Verified 2026-11-06 (Asia/Shanghai, UTC+8). Base e15dd44060a327b10abf81f0f5a9be753c8a536e.

## Sources actually read this turn

| Source | curl -L result | Checked content / use |
|---|---|---|
| https://arxiv.org/html/2502.01143v3 | 200 | ASAP original Figure2,III-B/C/D: fit delta-action using real rollout data so simulator with added delta matches real; freeze delta, fine-tune policy in aligned simulation; deploy WITHOUT delta. Not a residual network running on the real robot. |
| https://arxiv.org/abs/2502.01143 | 200 | Existing asap-paper resource endpoint reverified; summary updated with policy-only deployment. |
| https://ar5iv.labs.arxiv.org/html/2301.04317 | 200 | Darvish et al., Teleoperation of Humanoid Robots: A Survey, V-A,V-D/E: transmission delays, passivity/wave variables, constant-delay assumptions, jitter/loss/sampling complications, stability vs transparency. Opened readable full HTML. This is the cited survey, not a claim to have opened each primary reference it cites. |

An initial arxiv.org/html/2301.04317v2 curl returned404 although public readable fetch yielded the survey; final lesson/resource use the curl200 ar5iv URL. A MIT thesis landing page was readable but its PDF returned429; the thesis full text was NOT read and is NOT used as evidence/cited. No unavailable source is represented as successfully opened full text.

## H2 protocol

- Scalar semi-implicit plant, q[m],v[m/s],acceleration-equivalent action; nonlinear drag plus gain/damping/bias shift. Bias is a torque-bias proxy, not a motor torque measurement.
- Pretrain tracker policy by finite simulation candidate search on Plant-A, NOT neural RL/PPO; all arms begin with same base policy.
- Exactly160 Plant-B transitions collected once per seed (100+60), same observations/noise/data object for all3 arms; no hidden extra B queries for model selection. Same4 tuning references,81 policy candidates,4*100 simulator steps/candidate/arm.
- Five seeds720–724; five reserved evaluation trajectories per seed (seed+10000) shared by all arms. Evaluate selected policy alone on B; no delta input in deployment signature.
- SysID explicit linear physical model omits nonlinear drag. DR uses that fit's residual RMS to choose four lesson-defined parameter corners. Residual-action has a richer nonlinear feature set; equal data/steps is NOT equal model capacity. DR uses a four-scenario empirical average, not worst-case assurance.
- Residual action fits action-coordinate correction to align A with B, not uniquely identified physical parameters. This toy is a supervised/grid-search analogy of ASAP workflow, NOT ASAP reproduction.
- Report all seed rows, population SD/min/max. No universal winner; ties retained; SysID seed722 regresses. 0.35m fall-proxy threshold is a lesson-defined tracking-error proxy, not actual humanoid falls. Isaac/real-robot parts 本页未运行; paper claims 以论文为准.

## H7 protocol

- Unilateral position commands only, same500-command sine stream and per-command jitter draws; same first-order follower. No force feedback or passivity controller implemented.
- Nominal command one-way20/100ms; control probeRTT40/220ms; request-to-image video probeRTT100/340ms; unsolicited event display age80/240ms. RTT != twice outgoing delay in an asymmetric link. Probe definition explicit, not a universal WebRTC field.
- Stop trial: remote hazard2.00s, same0.35m/s ramp, shared20 reaction draws180–280ms. Operator sends hold at event+display age+reaction; network still delays delivery. Extra travel after hazard defines stop advance; >0.18m exercise threshold defines miss. Not e-stop/certification/human-subject performance.
- one_way_only_estimate is an optimistic accounting ablation of the high link that omits display age, NOT a third physical network or an actual safer controller. Tracking equals high intentionally; optimistic stop misses do not claim physical improvement.
- Delay/jitter/reaction values are illustrative; no Wi-Fi/WebRTC/device benchmark. Bilateral force feedback needs its own stability/energy argument; survey discusses passivity/wave variables with assumptions. Do not infer bilateral guarantees from unilateral toy.

## Minutes and placement

19440+210+180=**19830**,71 lessons. M7=1860+210=**2070**;M11=2820+180=**3000**. No mismatch and no unrelated lesson inflation. All added sections, code, stdout and exercises precede final bilingual Summary; summaries teach the additions. Regression locks run before the sole final process.exit and execute both toys against expected outputs. Reciprocal7.2↔11.6 links.

## Tool fallback

opencode free DeepSeek→GLM→MiMo each produced only a startup banner and timed out after45s with no edits. LongCat/MiniMax free models absent from catalog. Implemented locally in new worktree with hardlinked node_modules; no CloudAgent.

## Local verification

PASS: check_diagrams(23 diagrams,10786 checks,0 failed; both new toys executed),check_widgets(680/0),check_wokwi(8 diagrams/16 cards/0 problems),check_quotes(320 code blocks/268 simulated outputs/0 problems),lint,next typegen,tsc --noEmit,CI=1 production build including static base-path/visible-markdown/percentage checks. Month7 and Month11 expected tables matched. Existing optional Month7 MuJoCo grip_sweep skipped under default python (mujoco unavailable); NumPy handeye ran. No new dependency required.
