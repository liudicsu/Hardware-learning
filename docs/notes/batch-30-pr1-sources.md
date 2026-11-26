# Batch-30 PR1 sources

Unit: H1 monotonic vs wall-clock timeouts (`python-terminal`, 330→510). Site **46260** = 46080+180; M1 **3270** (still lightest); still 71 lessons. Branch `feat/python-monotonic-clocks` from `49a7c23a80ec9d497129ba346047271613b88d92`. After this PR alone, site typography is `46 260` (the full-batch target 46 440 is after PR2). M2 stays 4290; M8=M11 stay jointly heaviest at 4530. These load facts are recorded here and in the month-1 plan Current header only, not as a student-facing process lecture. Parent accepted the 2-unit batch; this PR is H1 only. H2 / `timing-interrupts` was not started.

## Pins actually opened (re-fetched live at writing)

This is a Python documentation page, not an arXiv record: no Comments header and no journal-ref field were present, and none was invented.

- Official Python 3 library docs, `time`, https://docs.python.org/3/library/time.html — curl **200**; sha256 `fbcc210c825b949d38206969a890e9a7ef2d32cf0d5590728dcb8b8820ebdafd`. HTTP body 129610 bytes. Last-Modified Wed, 25 Nov 2026 20:08:49 GMT = **2026-11-26 04:08:49 Asia/Shanghai**. Footer “Last updated on Nov 25, 2026 (20:07 UTC)” = 04:07 Asia/Shanghai. Banner / title: Python 3.15.2 documentation. Live re-fetch at writing 2026-11-26 11:38:27 Asia/Shanghai (response Date Thu, 26 Nov 2026 03:38:27 GMT): HTTP 200, sha256, byte length and Last-Modified all match the parent pin `fbcc210c…` and the cached body at `/tmp/b30p1-docs/time.html`. Relative to the batch-29 pin `165710e4…`, only the footer date had already moved before this pin; substantive claims below are unchanged, and this write-time fetch did not move again. This page was **not** already in `src/lib/resources.ts`, `src/lib/curriculum.ts`, or the host MDX; it is added here as a new Resource / reading-map / curriculum entry `python-time` and is the formula body. The existing `python-tutorial` resource is `https://docs.python.org/3/tutorial/` and does not already cover the library `time` page. 以文档为准: `time.monotonic()` returns the value (in fractional seconds) of a monotonic clock, i.e. a clock that cannot go backwards; the clock is not affected by system clock updates; the reference point of the returned value is undefined, so that only the difference between the results of two calls is valid; `time.time()` returns the time in seconds since the epoch as a floating-point number, and while this function normally returns non-decreasing values, it can return a lower value than a previous call if the system clock has been set back between the two calls; `time.get_clock_info` `adjustable` is True if the clock can be set to jump forward or backward in time, False otherwise, and does not refer to gradual NTP rate adjustments; `monotonic` is True if the clock cannot go backward, False otherwise; platform notes in the `monotonic()` entry (Windows `QueryPerformanceCounter` / `QueryPerformanceFrequency`, otherwise `clock_gettime(CLOCK_MONOTONIC)`, and the documented macOS / HP-UX alternatives) are official availability text, not toy outputs; `time.clock_settime` currently accepts `CLOCK_REALTIME` only. “The handling of leap seconds is platform dependent” is the only leap-second sentence used. No NTP-slew numbers and no clock-resolution values were invented or printed.

Lesson-chosen toy parameters (`TIMEOUT_S=1.0000` s, `DT_S=0.1250` s, `JUMP_AT_S=0.2500` s, `BACKWARD_S=-2.0000` s, `FORWARD_S=2.0000` s, `FORWARD_ALT_S=0.5000` s, `WALL_ORIGIN_S=1700000000.0000` s, `MONO_ORIGIN_S=1000.0000` s, `MAX_WAIT_S=5.0000` s, `clear_frac=0.2000`, work plan `30+25+50+40+35=180`) were named in the toy header / `hand_calc` lines before the official first run. Jumps are injected by a wrapped clock inside the toy. Live NTP / `clock_settime` 本页未运行. No claim is made that the machine clock was stepped on this page.

## Official first run

`monotonic_vs_wallclock_timeout_toy.py`, 2026-11-26 11:32:14 Asia/Shanghai, byte-identical on rerun. Expected sha256 `b981b3f75fe99977a20b1758b70d5ddcf047ac4b9db6b551ca8746ab65e75d05`. Official `expected/` was not retuned.

## Pre-declared cells

All held and are disclosed in the en/zh results.

- no_jump: paired A-B `fire_s` `0.0000+-0.0000: tie: identical on every seed` (`1.0000 s`). Both arms accept the deadline. Declared exact tie or official near-tie; held as an exact tie; kept.
- backward_jump: paired A-B `fire_s` `2.0000+-0.0000 s`, **clear**, same sign on all 5 seeds (wall-clock timeout late / missed at `3.0000 s`; monotonic holds at `1.0000 s`). Held; kept.
- forward_jump: paired A-B `fire_s` `-0.7500+-0.0000 s`, **clear**, same sign on all 5 seeds (wall-clock timeout expires early at `0.2500 s`; monotonic holds at `1.0000 s`). Held; kept.
- stamp_confusion: paired C-B `fire_s` `4.0000+-0.0000 s`, **clear**, same sign on all 5 seeds (C loses at the `5.0000 s` cap, because the absolute monotonic reading never reaches the epoch stamp `1700000001.0000000000 s`). Held; kept.
- Named alternative `FORWARD_ALT_S=0.5000 s` was printed on the same jump instant and not adopted (paired A-B `fire_s` `-0.5000+-0.0000 s`, still clear).

## Post-first-run disclosures

There was no official toy or `expected/` change after the first run. Lesson prose (including the SimOutput embedding and the results / work-plan wording), hooks, curriculum, plans, sources, README typography and tip locks were written after those figures were frozen. `|m| <= sd` was wrapped in backticks in the first official en/zh draft so the less-than sign would not be parsed as a tag; official expected/ was not retuned. No lock relaxed. Existing `nyquist_aliasing_toy.py` and its `expected/`, `ohm.py`, `resistors.py`, and `log.py` (including the UTC stamp line and its lesson wording) were not retuned or edited. The existing Nyquist / aliasing / Common-mistakes wording was left byte-untouched except the allowed one new Summary sentence and the new section immediately before `<Summary>`. Avoided hosts were not reopened. `package.json` / lockfile, `.github/workflows`, and the authoritative proposal file were not edited.

## Mismatch with §9

None.

## Lock changes

New batch-30 PR1 block in `tools/check_diagrams.mjs` (toy, expected, CRN, label order, required `python-time` addition, official monotonic vs wall-clock timeout contrast, sources, plans, README, declared regimes) plus `tools/test_b30p1_monotonic_vs_wallclock_timeout_toy.py`. Tipped site-total, host-minute, month-total and Current-header locks only (46080→46260, M1 3090→3270, python-terminal 330→510, README `46 080`→`46 260`). Historical strings inside already-written plan/sources files were not edited, including `Current / 当前：**M1 3090 min**, Batch-29 PR1` and `Current / 当前：**M1 2910 min**, Batch-22 PR1`. No lock was jumped to 46440 / `46 440`. M2 stays 4290; M8=M11 stay 4530. No lock relaxed.

- README `/46 080/` and `约 46 080 分钟` → `/46 260/` and `约 46 260 分钟`.
- Curriculum sum checks `46080` → `46260`; live M1 sum checks 3090→3270; live host-minute checks 330→510 on python-terminal.
- Current-curriculum month table: M1 3090→3270; other months unchanged.
