# safety-reliability (8.5)

CPU toys (stdlib):

- `watchdog_sim.py` — command-path watchdog: max overshoot 0.6500 without, 0.0000 with clamp.
- `actuator_fault_monitor_toy.py` — device/bus side: drive status Fault bit or status-frame timeout latches safe; a cleared bit never auto re-enables; re-enable needs `operator_ack` + bit clear + `RECOVER_FRAMES` good frames. Arms ignore / latch_only / latch_ack. Status-word bit names from the public ros2_canopen `State402::StatusWord` table (standard bits 0–7, 9–11); bits 8, 12–13, 14–15 masked and not asserted. Real drives / CANopen / SocketCAN 本页未运行; bus-off or a soft reset is not an e-stop.
- `bench_safety_checklist.md` — print before powered sessions.

```bash
python3 watchdog_sim.py
python3 actuator_fault_monitor_toy.py
```
