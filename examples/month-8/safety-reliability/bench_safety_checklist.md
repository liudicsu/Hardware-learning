# SO-101 bench safety checklist

Print this; tick before every powered session. Principles only — not a substitute for ISO 10218-1 or ISO/TS 15066 (those target industrial systems; 15066 **does not apply** to non-industrial robots).

## Before power
- [ ] Clear clamp points (fingers, cables, table edge) within the reachable workspace
- [ ] Soft software joint limits loaded and verified against a slow jog
- [ ] Physical e-stop or power interrupt within arm's reach of the operator (cutting motor power — **not** only a software topic)
- [ ] Watchdog / command-timeout behaviour confirmed in sim or a dry run
- [ ] No unattended power: someone stays at the bench while motors are enabled

## Power-up order
1. Host PC and cameras
2. Arm power with e-stop ready
3. Enable controllers / teleop
4. Slow jog each joint through the planned workspace

## During a policy rollout
- [ ] Hand near e-stop on the first 3 rollouts of a new checkpoint
- [ ] Human intervention path agreed (who grabs the e-stop; who resets)
- [ ] Stop on NaN commands, repeated watchdog holds, or unexpected contact

## After
- [ ] Disable motors before leaving the bench
- [ ] Log any e-stop / collision / watchdog event in the failure table
