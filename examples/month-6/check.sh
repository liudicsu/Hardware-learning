#!/usr/bin/env bash
# Run the Month 6 examples exactly as the lessons do and compare with the quoted output in expected/.
# Lessons 1-4 are standard-library Python toy models with fixed seeds (quoted as "simulated output / 仿真输出");
# lesson 5's portfolio_check.py is an ordinary program run on two sample READMEs (not labelled).
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

# ---- Lesson 5: portfolio_check.py on a complete and a thin sample README (a real run, exit code 1) -
check portfolio_check.txt bash -c "cd '$M6/specialisation-portfolio' && python3 portfolio_check.py samples/arm-pick-place samples/line-follower; echo \"exit code \$?\""
# the lesson quotes that output without a <SimOutput> label (a real run), so check_quotes.py does not see it
python3 - "$M6/expected/portfolio_check.txt" "$M6/../../src/content/m6/specialisation-portfolio" <<'PY' || fail=1
import sys
want = open(sys.argv[1]).read().rsplit('exit code', 1)[0]
bad = 0
for lang in ('en', 'zh'):
    ok = want in open(f'{sys.argv[2]}/{lang}.mdx').read()
    print(('same  ' if ok else 'DIFF  ') + f'portfolio_check output quoted in {lang}.mdx')
    bad += not ok
sys.exit(1 if bad else 0)
PY
exit $fail
