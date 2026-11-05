#!/usr/bin/env python3
"""actuator_fault_monitor_toy.py: device/bus fault latch + operator ack (stdlib).

watchdog_sim.py (same lesson) guards the COMMAND path: our outgoing commands
stop arriving. This toy guards the DEVICE/BUS side: the drive's own status
frames report a fault, or status frames stop arriving on the bus.

Status word bits are read BY NAME from the public ros2_canopen table
State402::StatusWord (canopen_402_driver/include/canopen_402_driver/state.hpp,
commit 52327f9b): standard bits 0-7 and 9-11. The decision logic reads only
bit 3 (Fault) and bit 7 (Warning). Bit 8 and bits 14-15 are manufacturer-
specific and bits 12-13 are operation-mode-specific in that table: here they
carry seeded random noise, are masked out, and are never used in a decision
or an assertion. The official CiA 402 text is a paid standard; not linked.

Three arms share one synthetic status stream:
  ignore      forward motion whatever the status says
  latch_only  latch safe (inhibit motion) while the fault bit is set or the
              status timeout has elapsed, then release AUTOMATICALLY once the
              bit is clear and frames are back -- the auto-reset anti-pattern
  latch_ack   latch safe; stay latched when the bit clears; re-enable only
              when operator_ack is True AND fault bit clear AND at least
              RECOVER_FRAMES consecutive good frames have arrived

Ground truth for scoring: a fault episode is unresolved from the tick the
monitor can see it (fault bit in a received frame, or STATUS_TIMEOUT_TICKS
missed frames) until the first QUALIFYING ack (ack + both preconditions).
  unsafe_motion_ticks   motion forwarded while an episode is unresolved
  false_auto_reenables  episodes after which motion resumed with no qualifying
                        ack (must be 0 on latch_ack)
  blind_ticks           missed frames before the timeout fires -- identical in
                        every arm; a software monitor cannot see them, which is
                        one reason the hardware e-stop path stays separate
Bus-off recovery or a drive soft reset is NOT an e-stop: neither removes
motor power. Numbers are lesson-chosen; no SIL / PL claims.
usage: python3 actuator_fault_monitor_toy.py
"""
from __future__ import annotations

import random

SEED = 85
HORIZON = 110
STATUS_TIMEOUT_TICKS = 3
RECOVER_FRAMES = 5

# Bit indices named as in ros2_canopen State402::StatusWord.
SW_READY_TO_SWITCH_ON = 0
SW_SWITCHED_ON = 1
SW_OPERATION_ENABLED = 2
SW_FAULT = 3
SW_VOLTAGE_ENABLED = 4
SW_QUICK_STOP = 5
SW_SWITCH_ON_DISABLED = 6
SW_WARNING = 7
SW_REMOTE = 9
SW_TARGET_REACHED = 10
SW_INTERNAL_LIMIT = 11
STANDARD_BITS = (0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 11)
NONSTANDARD_BITS = (8, 12, 13, 14, 15)  # manufacturer- / mode-specific: masked
STANDARD_MASK = sum(1 << b for b in STANDARD_BITS)

# Lesson-chosen synthetic words (the monitor only reads bits 3 and 7).
WORD_RUNNING = (1 << SW_READY_TO_SWITCH_ON) | (1 << SW_SWITCHED_ON) | (
    1 << SW_OPERATION_ENABLED) | (1 << SW_VOLTAGE_ENABLED) | (1 << SW_QUICK_STOP)
WORD_FAULT = (1 << SW_FAULT) | (1 << SW_VOLTAGE_ENABLED)
WORD_CLEARED = (1 << SW_SWITCH_ON_DISABLED) | (1 << SW_VOLTAGE_ENABLED)

WARNING_TICKS = range(20, 25)
FAULT_TICKS = range(30, 42)        # fault bit set in received frames
CLEARED_TICKS = range(42, 60)      # drive reports fault bit clear, not running
GAP_TICKS = range(75, 83)          # no status frames at all (bus silence)
ACK_TICKS = (36, 60, 85, 95)       # synthetic operator presses ack

# DiagnosticStatus levels (diagnostic_msgs/msg/DiagnosticStatus: OK=0 WARN=1
# ERROR=2; STALE=3 also exists but this toy does not use it).
OK, WARN, ERROR = 0, 1, 2
LEVEL_NAME = {OK: "OK", WARN: "WARN", ERROR: "ERROR"}


def build_stream(noise_seed: int) -> list[dict]:
    """Per tick: frame (status word or None) and operator_ack flag."""
    rng = random.Random(noise_seed)
    stream = []
    for t in range(HORIZON):
        noise = sum(1 << b for b in NONSTANDARD_BITS if rng.random() < 0.5)
        if t in GAP_TICKS:
            word = None
        elif t in FAULT_TICKS:
            word = WORD_FAULT | noise
        elif t in CLEARED_TICKS:
            word = WORD_CLEARED | noise
        else:
            word = WORD_RUNNING | noise
            if t in WARNING_TICKS:
                word |= 1 << SW_WARNING
        stream.append({"t": t, "word": word, "ack": t in ACK_TICKS})
    return stream


def bit(word: int, idx: int) -> bool:
    return bool((word & STANDARD_MASK) >> idx & 1)


def observe(stream: list[dict]) -> list[dict]:
    """Monitor view per tick, shared by every arm."""
    out, missed, good_run, fault_seen = [], 0, 0, False
    for s in stream:
        w = s["word"]
        if w is None:
            missed += 1
            good_run = 0
        else:
            missed = 0
            fault_seen = bit(w, SW_FAULT)
            good_run = 0 if fault_seen else good_run + 1
        stale = missed >= STATUS_TIMEOUT_TICKS
        fault_visible = stale or (w is not None and fault_seen)
        level = ERROR if fault_visible else (
            WARN if w is not None and bit(w, SW_WARNING) else OK)
        out.append({
            "t": s["t"], "ack": s["ack"], "frame": w is not None,
            "fault_bit": w is not None and fault_seen, "stale": stale,
            "blind": w is None and not stale, "fault_visible": fault_visible,
            "good_run": good_run, "level": level,
            "qualifying_ack": s["ack"] and not fault_visible and w is not None
            and good_run >= RECOVER_FRAMES,
        })
    return out


def run_arm(arm: str, obs: list[dict]) -> tuple[list[bool], int]:
    """Return per-tick 'motion forwarded?' and the number of rejected acks."""
    latched, motion, ack_rejects = False, [], 0
    for o in obs:
        if arm == "latch_only":
            latched = o["fault_visible"] or (latched and not o["frame"])
        elif arm == "latch_ack":
            if o["fault_visible"]:
                latched = True
            if o["ack"] and latched:
                if o["qualifying_ack"]:
                    latched = False
                else:
                    ack_rejects += 1
        elif arm != "ignore":
            raise ValueError(arm)
        motion.append(not latched)
    return motion, ack_rejects


def score(obs: list[dict], motion: list[bool]) -> dict:
    unresolved, reenabled = False, False
    unsafe = false_reenables = 0
    for o, m in zip(obs, motion):
        if o["fault_visible"] and not unresolved:
            unresolved, reenabled = True, False
        if unresolved and o["qualifying_ack"]:
            unresolved = False
        if unresolved and m:
            unsafe += 1
            # motion after the bit cleared / frames returned, without ack
            if not o["fault_visible"] and not reenabled:
                false_reenables += 1
                reenabled = True
    return {"unsafe": unsafe, "false": false_reenables,
            "blind": sum(1 for o in obs if o["blind"]),
            "latched": sum(1 for m in motion if not m)}


def main() -> None:
    stream = build_stream(SEED)
    obs = observe(stream)
    levels = {name: sum(1 for o in obs if o["level"] == lv)
              for lv, name in LEVEL_NAME.items()}
    print(f"seed={SEED} horizon={HORIZON} status_timeout_ticks={STATUS_TIMEOUT_TICKS} "
          f"recover_frames={RECOVER_FRAMES}")
    print("statusword: decisions read bit 3 Fault, bit 7 Warning "
          "(ros2_canopen State402::StatusWord standard bits 0-7, 9-11)")
    print("masked_not_asserted: bit 8, 14, 15 manufacturer-specific; "
          "bits 12-13 mode-specific")
    print("stream: warning t20-24 | fault_bit t30-41 | bit_clear t42-59 | "
          "frame_gap t75-82 | operator_ack t36,60,85,95")
    print(f"diag_levels OK={levels['OK']} WARN={levels['WARN']} ERROR={levels['ERROR']}")
    print(f"{'arm':<11} {'unsafe_motion_ticks':>19} {'false_auto_reenables':>20} "
          f"{'ack_rejects':>11} {'latched_ticks':>13} {'blind_ticks':>11}")
    results = {}
    for arm in ("ignore", "latch_only", "latch_ack"):
        motion, rejects = run_arm(arm, obs)
        s = score(obs, motion)
        results[arm] = (motion, s)
        print(f"{arm:<11} {s['unsafe']:>19d} {s['false']:>20d} "
              f"{rejects:>11d} {s['latched']:>13d} {s['blind']:>11d}")
    probe = obs[45]
    state = "ENABLED" if results["latch_ack"][0][45] else "LATCHED_SAFE"
    print(f"bit_clear_no_ack: t={probe['t']} fault_bit={int(probe['fault_bit'])} "
          f"frame={int(probe['frame'])} operator_ack={int(probe['ack'])} state={state}")
    for t in ACK_TICKS:
        o = obs[t]
        why = ("accepted" if o["qualifying_ack"] else
               "rejected:fault_visible" if o["fault_visible"] else
               f"rejected:good_frames={o['good_run']}<{RECOVER_FRAMES}")
        print(f"ack t={t} -> {why}")
    # Flip only the masked manufacturer/mode bits: decisions must not change.
    alt = observe(build_stream(SEED + 1000))
    changed = sum(1 for arm in results
                  if run_arm(arm, alt)[0] != results[arm][0])
    print(f"nonstandard_bit_noise_changes_decisions={changed}")
    s_ack = results["latch_ack"][1]
    assert s_ack["unsafe"] == 0 and s_ack["false"] == 0
    assert state == "LATCHED_SAFE" and changed == 0
    assert results["latch_only"][1]["false"] > 0 and results["ignore"][1]["unsafe"] > 0
    print("ok: latch_ack unsafe_motion_ticks=0 false_auto_reenables=0; "
          "bus-off / soft reset is not an e-stop (hardware path 本页未运行)")


if __name__ == "__main__":
    main()
