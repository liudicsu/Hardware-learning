# PR-3 progress (branch `opencode/demos-pr3`)

Resume from git: each finished item is its own commit. Checks run before every push:
`npm run lint`, `npx next typegen`, `npx tsc --noEmit`, `npm run build`,
`python3 tools/check_wokwi.py`, `node tools/check_widgets.mjs`, `python3 tools/check_quotes.py`.

| # | Item | Status | Notes |
|---|---|---|---|
| 0 | lambda = 0.01 note (check_widgets.mjs + CONTENT_GUIDE) | done | hand-written: opencode (deepseek-v4.1-flash-free and glm-5.3-flash-free) both returned "Rate limit exceeded" |
| 1 | m2 first-robots line-follow PD | done | `lineFollow.ts` + `LineFollowWidget`; whole `m2-line_sim.txt` byte-matched (15 checks); hand-written (opencode rate-limited) |
| 2 | m2 sensors-fusion alpha | done | `complementary.ts` + `ComplementaryWidget`; analytic approximation (script uses seeded random noise), checked to 1 decimal place against `offset_flat` (4 checks); page says so in zh/en; hand-written |
| 3 | m3 fdm snap-fit | todo | |
| 4 | m3 transmissions planetary/backlash | todo | |
| 5 | m3 so101 STS packet | todo | |
| 6 | m3 gripper force | todo | |
| 7 | m4 urdf-tf pan/tilt | todo | |
| 8 | m4 ros2-control diff drive | todo | |
| 9 | m5 control-modelling Bode | todo | |
| 10 | m5 state-space LQR | todo | |
| 11 | m6 vla-models action tokens | todo | |
| 12 | m6 policy-evaluation Wilson | todo | |

## opencode vs hand log

- Item 0: opencode attempted twice (both models rate-limited, no output); written by hand.
- Item 1: opencode tried with both models (rate-limited before any edit); model, widget, shared `Chart.tsx`, `pyfmt.ts` and wiring hand-written.
- Item 2: hand-written (opencode still rate-limited).
