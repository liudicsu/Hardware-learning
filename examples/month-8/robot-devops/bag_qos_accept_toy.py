#!/usr/bin/env python3
"""bag_qos_accept_toy.py: synthetic rosbag2/MCAP *acceptance* gate (stdlib).

Acceptance ≠ "the bag folder exists". A recording is accepted only when:
  1. every required topic is present with n > 0 messages
  2. inter-arrival gaps stay within max_gaps_allowed (1.5× nominal period)
  3. per-topic message counts meet a fixed message budget (n >= budget_min)

QoS override YAML keys are taken from the ros2/rosbag2 **jazzy** README
section "Overriding QoS Profiles":
  https://github.com/ros2/rosbag2/blob/jazzy/README.md
  (raw: https://raw.githubusercontent.com/ros2/rosbag2/jazzy/README.md)
That README verifies the YAML *keys*; it does **not** document
transient_local compatibility / matching boundaries — flagged below.

MCAP ROS 2 getting-started: https://mcap.dev/guides/getting-started/ros-2
docs.ros.org QoS How-To HTML: unresolved / optional for this batch (fetch
providers often 403); do not invent a "open in browser" workaround.

No binary .mcap / real bags in CI — JSON timeline fixtures only.
Live bag record, Foxglove, Rerun, wandb = 本页未运行.

usage: python3 bag_qos_accept_toy.py
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "accept_fixtures")
QOS_YAML = os.path.join(FIX, "qos_override.yaml")

# Keys from jazzy README example under "Overriding QoS Profiles".
JAZZY_README_QOS_KEYS = (
    "history",
    "depth",
    "reliability",
    "durability",
    "deadline",
    "lifespan",
    "liveliness",
    "liveliness_lease_duration",
    "avoid_ros_namespace_conventions",
)

REQUIRED_TOPICS = (
    "/joint_states",
    "/camera/color/image_raw",
    "/tf",
)

# Fixed message-budget table — do NOT swap the pass/fail comparisons.
# pass example: n=100 >= budget_min=90 → PASS
# fail example: n=10  >= budget_min=50 → FAIL (reject)
FIXED_BUDGET_PASS = {"label": "fixed_ok", "n": 100, "budget_min": 90}
FIXED_BUDGET_FAIL = {"label": "fixed_fail", "n": 10, "budget_min": 50}

# Per-topic budgets applied to fixture bags (messages over the recording).
TOPIC_BUDGET_MIN = {
    "/joint_states": 90,
    "/camera/color/image_raw": 20,
    "/tf": 50,
}

MAX_GAPS_ALLOWED = 2
GAP_FACTOR = 1.5


def count_gaps(stamps_ns: list[int], nominal_hz: float) -> int:
    if len(stamps_ns) < 2 or nominal_hz <= 0:
        return 0
    period = 1e9 / nominal_hz
    gaps = 0
    for a, b in zip(stamps_ns, stamps_ns[1:]):
        if (b - a) > GAP_FACTOR * period:
            gaps += 1
    return gaps


def load_qos_keys(path: str) -> list[str]:
    """Parse top-level per-topic keys from the override YAML (no PyYAML)."""
    keys: list[str] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            raw = line.rstrip("\n")
            if not raw or raw.lstrip().startswith("#"):
                continue
            # topic header: "/name:" at column 0
            if raw.startswith("/") and raw.endswith(":"):
                continue
            # policy line: two-space indent, "key:" or "key: value"
            if raw.startswith("  ") and not raw.startswith("    "):
                key = raw.strip().split(":", 1)[0]
                if key not in keys:
                    keys.append(key)
    return keys


def accept_bag(bag: dict) -> tuple[str, str, dict]:
    """Return (decision, reason, detail). folder_exists alone never accepts."""
    detail: dict = {
        "folder_exists": bool(bag.get("folder_exists")),
        "uri": bag.get("uri"),
    }
    if not bag.get("folder_exists"):
        return "REJECT", "folder_missing", detail

    by_name = {t["name"]: t for t in bag.get("topics", [])}

    for req in REQUIRED_TOPICS:
        topic = by_name.get(req)
        n = 0 if topic is None else len(topic.get("stamps_ns", []))
        detail[f"n:{req}"] = n
        if topic is None or n == 0:
            detail["missing_topic"] = req
            return "REJECT", "missing_required_topic", detail

    for req in REQUIRED_TOPICS:
        topic = by_name[req]
        gaps = count_gaps(topic["stamps_ns"], float(topic["nominal_hz"]))
        detail[f"gaps:{req}"] = gaps
        if gaps > MAX_GAPS_ALLOWED:
            detail["gap_topic"] = req
            return "REJECT", "gap_exceeded", detail

    for req in REQUIRED_TOPICS:
        n = len(by_name[req]["stamps_ns"])
        budget = TOPIC_BUDGET_MIN[req]
        detail[f"budget:{req}"] = budget
        if n < budget:
            detail["budget_topic"] = req
            return "REJECT", "below_message_budget", detail

    return "ACCEPT", "ok", detail


def fixed_budget_demo() -> None:
    """Pinned comparisons — swapping pass/fail numbers must not be done."""
    ok = FIXED_BUDGET_PASS
    bad = FIXED_BUDGET_FAIL
    ok_pass = ok["n"] >= ok["budget_min"]
    bad_pass = bad["n"] >= bad["budget_min"]
    print(
        f"fixed_budget_examples "
        f"{ok['label']}: n={ok['n']} budget_min={ok['budget_min']} "
        f"cmp=ge → {'PASS' if ok_pass else 'FAIL'}; "
        f"{bad['label']}: n={bad['n']} budget_min={bad['budget_min']} "
        f"cmp=ge → {'PASS' if bad_pass else 'FAIL'} "
        f"(do not swap comparisons)"
    )
    assert ok_pass and not bad_pass
    # Guard against accidental swap of the two example rows.
    assert ok["n"] > bad["n"]
    assert ok["budget_min"] > bad["budget_min"]


def main() -> None:
    qos_keys = load_qos_keys(QOS_YAML)
    print("bag_qos_accept_toy fixtures=accept_fixtures seed=n/a (deterministic)")
    print(f"qos_override_keys={','.join(qos_keys)}")
    missing = [k for k in JAZZY_README_QOS_KEYS if k not in qos_keys]
    extra = [k for k in qos_keys if k not in JAZZY_README_QOS_KEYS]
    assert not missing and not extra, (missing, extra)
    print(
        "qos_source=ros2/rosbag2 jazzy README Overriding QoS Profiles; "
        "transient_local compatibility boundary NOT documented there "
        "(uncertainty flagged; not claimed verified)"
    )
    print(
        f"required_topics={','.join(REQUIRED_TOPICS)} "
        f"max_gaps_allowed={MAX_GAPS_ALLOWED} gap_factor={GAP_FACTOR}"
    )
    fixed_budget_demo()

    cases = [
        "pass_clean.json",
        "missing_topic.json",
        "gap_heavy.json",
        "budget_short.json",
        "empty_folder.json",
    ]
    accept_n = 0
    reject_n = 0
    for name in cases:
        with open(os.path.join(FIX, name), encoding="utf-8") as f:
            bag = json.load(f)
        decision, reason, detail = accept_bag(bag)
        if decision == "ACCEPT":
            accept_n += 1
        else:
            reject_n += 1
        extra = ""
        if reason == "missing_required_topic":
            extra = f" topic={detail.get('missing_topic')} n=0"
        elif reason == "gap_exceeded":
            t = detail["gap_topic"]
            extra = f" topic={t} gaps={detail[f'gaps:{t}']}"
        elif reason == "below_message_budget":
            t = detail["budget_topic"]
            extra = (
                f" topic={t} n={detail[f'n:{t}']} "
                f"budget_min={detail[f'budget:{t}']}"
            )
        print(
            f"case={bag['uri']} folder_exists={detail['folder_exists']} "
            f"decision={decision} reason={reason}{extra}"
        )

    print(f"summary accept={accept_n} reject={reject_n}")
    assert accept_n == 1 and reject_n == 4
    print(
        "ok: acceptance ≠ folder_exists; synthetic fixtures only "
        "(no binary mcap; live bag/Foxglove/Rerun/wandb 本页未运行)"
    )


if __name__ == "__main__":
    main()
