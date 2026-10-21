# PR-4 progress (branch opencode/pr4-diffdrive-overflow, cut from origin/main cbb5da9)

Step A (live check of PR-3 deploy): done, see /workspace/hl-audit/pr3-live-check.md (134 checks, 4 failures = the known m3 so101-arm / gripper-fingers 390px overflow).

| # | item | status | notes |
|---|---|---|---|
| 1 | tools/sim/README: Python >= 3.12 for expected files | done | hand-written (opencode rate-limited) |
| 2 | m4 ros2-control diff_drive.py + expected + check.sh/reproduce.sh + widget + check_widgets | todo | |
| 3 | generic fix for 390px overflow (lesson header cost line, code blocks) | todo | |
| 4 | scan all pages at 390px (zh+en), fix, before/after counts | todo | |

## opencode
- 21:51 and 21:53 (UTC+8): deepseek-v4.1-flash-free and glm-5.3-flash-free both "Rate limit exceeded" (opencode log); runs produced nothing.
