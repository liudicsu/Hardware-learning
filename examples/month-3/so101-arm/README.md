# Lesson 5: Build the SO-101 arm / 第 5 课：组装 SO-101 机械臂

**`sts_packet.py`**: builds and checks Feetech STS3215 bus-servo packets by hand (ping, torque on, goal position, read position, a reply with a checksum, a corrupted reply). Register addresses from the STS control table used by LeRobot (Torque_Enable 40, Goal_Position 42, Present_Position 56). No hardware needed.
手工构造并校验飞特 STS3215 总线舵机的数据包。寄存器地址来自 LeRobot 使用的 STS 控制表。不需要硬件。

```bash
python3 sts_packet.py
```

**`compare_sdk.py`**: sends the same packets through Feetech's own Python SDK into a fake serial port and checks that the bytes are identical. Needs `pip install feetech-servo-sdk` (tested with 1.0.0).
用飞特官方 Python SDK 把同样的数据包写进一个假串口，检查字节完全一致。需要 `pip install feetech-servo-sdk`（测试版本 1.0.0）。

```bash
python3 compare_sdk.py
```

Both are ordinary programs run on a computer. To talk to real servos, use LeRobot's `lerobot-setup-motors`, `lerobot-calibrate` and `lerobot-teleoperate` as shown in the lesson and in the [LeRobot SO-101 docs](https://huggingface.co/docs/lerobot/so101).
两者都是电脑上运行的普通程序。和真实舵机通信请使用课程中介绍的 LeRobot 命令。
