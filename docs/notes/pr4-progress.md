# PR-4 progress (branch opencode/pr4-diffdrive-overflow, cut from origin/main cbb5da9)

Step A (live check of PR-3 deploy): done, see /workspace/hl-audit/pr3-live-check.md (134 checks, 4 failures = the known m3 so101-arm / gripper-fingers 390px overflow).

| # | item | status | notes |
|---|---|---|---|
| 1 | tools/sim/README: Python >= 3.12 for expected files | done | hand-written (opencode rate-limited) |
| 2 | m4 ros2-control diff_drive.py + expected + check.sh/reproduce.sh + widget + check_widgets | done | b = 0.28, r = 0.05 verified in m4_control/config/controllers.yaml (the script re-reads the YAML and says whether it agrees). Expected `examples/month-4/expected/ctl-diff_drive.txt` (one copy; reproduce.sh diffs its run against it explicitly). Lesson: CodeSource + Real output + DiffDriveWidget after quizzes q2/q3 (so the script's quiz row does not give the answer away), zh + en. `diffDrive.ts` + 13 new check_widgets checks (190 -> 203). Widget default = worked example spin 1.0 rad/s. M4 check.sh run 1: 25 same incl. ctl-diff_drive, 1 DIFF ros-launch_remap (topic hz timing flake); run 2 hung in the Lesson 3 stop_display step before reaching it (timeout). Hand-written (opencode rate-limited again at 21:58) |
| 3 | generic fix for 390px overflow (lesson header cost line, code blocks) | done | real cause on so101/gripper: ResourceCard cost `<span class="ml-auto shrink-0">` (long cost text could not shrink or wrap). Fix in ResourceCard (flex-wrap, min-w-0, wrap anywhere), CodeBlock wrapper min-w-0/max-w-full, prose pre/table max-width 100%; hand-written |
| 4 | scan all pages at 390px (zh+en), fix, before/after counts | done | /workspace/pwtest/scan390.js over 86 pages (all zh/en lessons, month, index, about, resources). Before: 12 overflow, 0 console-error pages. Extra cause: long inline `code` in paragraphs (ros2-graph, python-terminal) -> `.prose-lesson` overflow-wrap + inline code `overflow-wrap:anywhere`. After: 0 overflow, 0 console-error pages. Committed together with item 3 (same CSS file) |

## opencode
- 21:51 and 21:53 (UTC+8): deepseek-v4.1-flash-free and glm-5.3-flash-free both "Rate limit exceeded" (opencode log); runs produced nothing.
- ~21:58 (UTC+8): deepseek retry for item 2 (diff_drive.py draft) sat at the prompt for 400 s with no output; killed. Everything in this PR is hand-written.
