# ros2-hardware-interface (8.4)

CPU toys (stdlib):

- `servo_bus_sim.py` — bus jitter timeouts; budget guard 122→0.
- `lifecycle_sm_toy.py` — **managed ROS lifecycle node** SM only (design.ros2.org). Not HardwareComponentInterface. Illegal activate rejects then recovers via configure→activate.
- `so101_hw/` — C++ skeleton for your Jazzy workspace（本页未运行）. LTTng / live plugin load = 本页未运行.

```bash
python3 servo_bus_sim.py
python3 lifecycle_sm_toy.py
```

## Batch-6 PR2: generic Classic CAN diagnostics / 通用 CAN 诊断

`python3 can_fault_confinement_toy.py` is a separate event-level backend toy, not a claim that SO-101's serial bus uses CAN. Opened Bosch/NXP rules, TEC/REC +8 exceptions, >127 passive, TEC>255 bus-off, 128×11 recessive recovery gate; no SocketCAN/transceiver run. Not CiA402/EtherCAT/e-stop. / 已打开原始资料；真实网络本页未运行，不绕过执行器锁存。

Expected: `../expected/can_fault_confinement_toy.txt`, compared by `../check.sh`; independent physical tests in `tools/test_b6_can_ft_toys.py`. Lesson/source audit explains qualified inputs, RX high-counter reset, two no-increment TX exceptions and controller-policy simplifications.


`python3 joint_saturation_limiter_toy.py` is a labeled stdlib contract stand-in of the opened Jazzy userdoc / JointSaturationLimiter doxygen wording: command passthrough when limits are not enforced, a naive independent box clamp, and remaining-distance coupled saturation. Official plugin / controller manager 本页未运行. Official concept-page algorithm sections remain tba and are not invented. / 已打开的 Jazzy userdoc 与 doxygen 契约替身；官方插件本页未运行，不编造仍为 tba 的算法节。

Expected: `../expected/joint_saturation_limiter_toy.txt`, compared by `../check.sh`.
