#!/usr/bin/env bash
# Run the Month 8 examples and compare with expected/.
# 8 lessons complete / 8 课已齐 (8.1–8.8 Track B)
# Usage: examples/month-8/check.sh        UPDATE=1 examples/month-8/check.sh
set -uo pipefail
M8="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export PYTHONDONTWRITEBYTECODE=1
PY="${M8_PYTHON:-python3}"
fail=0
check() {
  local name="$1"; shift
  (cd "$TMP" && "$@") > "$TMP/$name" 2>&1
  local ec=$?
  if [[ $ec -ne 0 ]]; then echo "FAIL  $name (exit $ec)"; cat "$TMP/$name"; fail=1; return; fi
  if [[ -n "${UPDATE:-}" ]]; then cp "$TMP/$name" "$M8/expected/$name"; echo "wrote $name"; return; fi
  if diff -u "$M8/expected/$name" "$TMP/$name" > "$TMP/$name.diff"; then echo "same  $name"
  else echo "DIFF  $name"; cat "$TMP/$name.diff"; fail=1; fi
}

check dataset_audit.txt "$PY" "$M8/dataset-engineering/dataset_audit.py"
check chunk_latency_sim.txt "$PY" "$M8/async-deployment/chunk_latency_sim.py"
check watchdog_sim.txt "$PY" "$M8/safety-reliability/watchdog_sim.py"
check bag_stats.txt "$PY" "$M8/robot-devops/bag_stats.py"
check compute_budget.txt "$PY" "$M8/vla-finetune/compute_budget.py"
check servo_bus_sim.txt "$PY" "$M8/ros2-hardware-interface/servo_bus_sim.py"
check capstone_gate.txt "$PY" "$M8/capstone/capstone_gate.py" --demo
check suite_score_table.txt "$PY" "$M8/sim-benchmarks/suite_score_table.py"

check stream_sync_eval_toy.txt "$PY" "$M8/async-deployment/stream_sync_eval_toy.py"

check bag_qos_accept_toy.txt "$PY" "$M8/robot-devops/bag_qos_accept_toy.py"
check lifecycle_sm_toy.txt "$PY" "$M8/ros2-hardware-interface/lifecycle_sm_toy.py"
check actuator_fault_monitor_toy.txt "$PY" "$M8/safety-reliability/actuator_fault_monitor_toy.py"

check imagine_rank_toy.txt "$PY" "$M8/sim-benchmarks/imagine_rank_toy.py"

check safety_pl_assign_toy.txt "$PY" "$M8/safety-reliability/safety_pl_assign_toy.py" "$M8/safety-reliability/plr_inputs.json"

check can_fault_confinement_toy.txt "$PY" "$M8/ros2-hardware-interface/can_fault_confinement_toy.py"

check rpd_teacher_rl_toy.txt "$PY" "$M8/vla-finetune/rpd_teacher_rl_toy.py"
check vla_continual_er_toy.txt "$PY" "$M8/vla-finetune/vla_continual_er_toy.py"

check dataset_crc_integrity_toy.txt "$PY" "$M8/dataset-engineering/dataset_crc_integrity_toy.py"

exit $fail
