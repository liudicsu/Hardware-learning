# PR 7 follow-ups: verification record

Verified on 2026-10-20 (UTC+8) on branch `opencode/month-6`, after commits e7cf1ea, 375a279, cb1efe8, a05c92e.

## 1. `$ ` rule in docs/CONTENT_GUIDE.md (375a279)

Present (section "Code, examples and simulated outputs"): leading lines that start with `$ ` are left out on the
lesson side; a `$ ` line further down still compares byte-for-byte; a block made only of `$ ` lines is an error.

`python3 tools/check_quotes.py` → `170 code blocks, 108 simulated outputs checked, 0 problems`.

## 2. Month 3 check.sh with feetech-servo-sdk 1.0.0 (e7cf1ea)

```
python3 -m venv /tmp/m3venv && /tmp/m3venv/bin/pip install -r examples/month-3/requirements.txt
PATH=/tmp/m3venv/bin:$PATH bash examples/month-3/check.sh
```

feetech-servo-sdk 1.0.0 (+ pyserial 3.5) installed. Result: **12 same, 0 DIFF, 0 skipped**, including
`same  arm-compare_sdk.txt` (cad-bracket, cad-bracket-tight, cad-bracket-assert, fdm-snap_fit, fdm-case,
fdm-case-clash, fdm-case-clash-tight, tr-gear_calc, arm-sts_packet, arm-compare_sdk, grip-finger, grip-force).

## 3. map_check thresholds (cb1efe8)

Thresholds in `examples/month-4/slam-nav/map_check.py` are half of the smaller of two real runs:

| object | MIN_CELLS | run 1 | run 2 (test/room.yaml) | fresh run (tools/sim/out/maps) |
|---|---|---|---|---|
| north wall | 40 | 190 | 81 | 161 |
| south wall | 125 | 250 | 275 | 212 |
| west wall | 66 | 133 | 152 | 185 |
| east wall | 97 | 195 | 242 | 291 |
| red box | 12 | 24 | 26 | 26 |
| blue pillar | 6 | 12 | 12 | 14 |
| green block | 24 | 48 | 48 | 44 |
| whole map, occupied (MIN_OCCUPIED) | 347 | 747 | 694 | 797 |
| whole map, free (MIN_FREE) | 6329 | 12659 | 12730 | 12698 |

Normal run: `python3 map_check.py test/room.yaml` → all 7 objects `found`, exit 0
(119 x 120 cells, occupied 694 / free 12730 / unknown 856). The saved map from the last ROS run
(`tools/sim/out/maps/room.yaml`, 120 x 120 cells, occupied 797 / free 12698 / unknown 905) also passes, exit 0.

Negative tests: `python3 map_check_test.py` → `10 cases, 0 wrong`, exit 0:

- saved map: map_check exit 0 (want pass)
- blank map, all unknown: exit 1 (9 FAIL lines: 0 occupied < 347, 0 free < 6329, every object 0 cells)
- blank map, all free: exit 1 (8 FAIL lines: 0 occupied < 347, every object 0 cells)
- each of the 7 objects erased: exit 1 with exactly one FAIL line for that object (e.g. `red box: 0 occupied cells, need 12`)

## 4. Site checks

`npx tsc --noEmit` OK, `npx eslint .` OK, `npm run build` OK (all lesson pages prerendered).

Nothing was broken; no code changes were needed for these follow-ups.
