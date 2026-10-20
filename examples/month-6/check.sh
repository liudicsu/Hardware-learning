#!/usr/bin/env bash
# Run the Month 6 examples exactly as the lessons do and compare with the quoted output in expected/.
# These are standard-library Python toy models with fixed seeds (quoted as "simulated output / 仿真输出").
# Needs python3 (3.9+), no packages.
# Usage: examples/month-6/check.sh        UPDATE=1 examples/month-6/check.sh rewrites expected/
set -uo pipefail
M6="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export PYTHONDONTWRITEBYTECODE=1   # eval_report.py imports bc_reach.py; keep __pycache__ out of the tree
fail=0
check() {   # check <name> <command...>: run in $TMP, compare with expected/<name>
  local name="$1"; shift
  (cd "$TMP" && "$@") > "$TMP/$name" 2>&1
  if [[ -n "${UPDATE:-}" ]]; then cp "$TMP/$name" "$M6/expected/$name"; echo "wrote $name"; return; fi
  if diff -u "$M6/expected/$name" "$TMP/$name" > "$TMP/$name.diff"; then echo "same  $name"
  else echo "DIFF  $name"; cat "$TMP/$name.diff"; fail=1; fi
}

# ---- Lesson 1: behaviour cloning, covariate shift and DAgger --------------------------------------
check bc_reach.txt python3 "$M6/behaviour-cloning/bc_reach.py" demos.csv
check bc_demos_head.txt head -4 demos.csv

# ---- Lesson 2: multimodal demonstrations, action chunks and diffusion ------------------------------
check multimodal.txt python3 "$M6/act-diffusion/multimodal.py"

# ---- Lesson 3: VLA action tokens, per-step bins versus a DCT of the chunk -------------------------
check action_tokens.txt python3 "$M6/vla-models/action_tokens.py"

# ---- Lesson 4: evaluating a policy (Wilson intervals, paired trials, trials needed, failure table) -
check eval_report.txt python3 "$M6/policy-evaluation/eval_report.py"
exit $fail
