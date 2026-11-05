# ros2-hardware-interface (8.4)

CPU toys (stdlib):

- `servo_bus_sim.py` — bus jitter timeouts; budget guard 122→0.
- `lifecycle_sm_toy.py` — **managed ROS lifecycle node** SM only (design.ros2.org). Not HardwareComponentInterface. Illegal activate rejects then recovers via configure→activate.
- `so101_hw/` — C++ skeleton for your Jazzy workspace（本页未运行）. LTTng / live plugin load = 本页未运行.

```bash
python3 servo_bus_sim.py
python3 lifecycle_sm_toy.py
```
