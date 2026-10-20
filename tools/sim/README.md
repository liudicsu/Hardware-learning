# tools/sim: simulations behind the lesson outputs / 课程输出背后的仿真

Every output in the lessons that is labelled **Simulated output / 仿真输出** was produced by something in this folder. Nothing here is a hardware measurement: real boards, motors and sensors will give different numbers.
课程中所有标注“仿真输出”的结果都来自本目录。这里没有任何硬件实测数据，真实的开发板、电机和传感器会给出不同的数值。

| Path / 路径 | What / 内容 |
| --- | --- |
| `avrrun/avrrun.c` | A small [simavr](https://github.com/buserror/simavr) harness: runs an ATmega328P (Uno) ELF, prints its serial output and injects pin or ADC events. Optional simulated parts: a TB6612FNG + gearmotor + quadrature encoder (`MOTOR`) and an MPU-6050 (`MPU`). / 基于 simavr 的小工具：运行 Uno 固件、打印串口输出、注入引脚/ADC 事件；可选模拟电机与编码器、MPU-6050 |
| `models/*.py` | Python toy models quoted in the lessons. Month 2: debounce, one revolution, complementary filter, line follower, balancer. Month 3: backlash, PID on one arm joint, balancer cascade. Month 5: the arm joint modelled and read in the frequency domain, state space with LQR and MPC, kinematics. Standard library only. / 课程中引用的 Python 玩具模型（第 2 个月：消抖、一圈、互补滤波、循线、平衡车；第 3 个月：回差、单关节 PID、平衡车串级；第 5 个月：关节建模与频域分析、状态空间与 LQR、MPC、运动学），只用标准库 |
| `expected/*.txt` | The exact outputs quoted in the lessons. / 课程中引用的原样输出 |
| `ros/run.sh` | Month 4: real ROS 2 software on the simulated m4bot (Gazebo, ros2_control mock hardware, SLAM and Nav2), compared with `expected/m4-ros-*.txt` within a tolerance. Needs ROS 2 Jazzy (`examples/month-4/pixi.toml`); skipped otherwise. / 第 4 个月：真实 ROS 2 软件驱动仿真的 m4bot，按容差与 `expected/m4-ros-*.txt` 比对；需要 ROS 2 Jazzy，否则跳过 |
| `m5/run.sh` | Month 5: OpenCV calibration on synthetic photos (`expected/m5-cam_*.txt`) and MoveIt 2 pick and place on the Panda's mock hardware (`expected/m5-moveit_*.txt`, random planner details masked). Needs `examples/month-5/pixi.toml`; skipped otherwise. / 第 5 个月：在合成照片上做 OpenCV 标定，在 Panda 的 mock 硬件上用 MoveIt 2 抓放（随机规划器的细节被屏蔽）；需要 `examples/month-5/pixi.toml`，否则跳过 |
| `reproduce.sh` | Builds the harness, compiles the sketches in `examples/month-2/` and `examples/month-3/`, runs everything and diffs against `expected/`. / 一键编译、运行并与 `expected/` 比对 |

## Prerequisites / 依赖

Tested on Debian/Ubuntu Linux (x86-64). / 在 Debian/Ubuntu Linux 上测试。

```bash
sudo apt install gcc make libsimavr-dev libelf-dev python3
# arduino-cli: https://arduino.github.io/arduino-cli/latest/installation/
arduino-cli core update-index
arduino-cli core install arduino:avr          # tested with 1.8.8
# only for --compile-only-too / 仅 --compile-only-too 需要:
arduino-cli core install esp32:esp32          # tested with 3.3.12
arduino-cli lib install QTRSensors            # tested with 4.0.0
```

## Reproduce everything / 一键复现

From a clean checkout / 在全新克隆的仓库中:

```bash
git clone https://github.com/liudicsu/Hardware-learning.git
cd Hardware-learning
tools/sim/reproduce.sh                  # about 1 min; prints "same <file>" for each of the 22 outputs
tools/sim/reproduce.sh --compile-only-too   # also compiles the ESP32 and line-follower sketches
```

Exit code 0 means every output matched `expected/`. Build products go to `tools/sim/build/` and outputs to `tools/sim/out/`; both are git-ignored.
退出码为 0 表示全部与 `expected/` 一致。编译产物在 `tools/sim/build/`，输出在 `tools/sim/out/`，都已加入 .gitignore。

## Run one case by hand / 手动运行单个用例

```bash
gcc -O2 -o /tmp/avrrun tools/sim/avrrun/avrrun.c -lsimavr -lelf -lm
arduino-cli compile -b arduino:avr:uno examples/month-2/arduino-io/pot_pwm --output-dir /tmp/pot_pwm
/tmp/avrrun /tmp/pot_pwm/pot_pwm.ino.elf 2500 0:A0=0 500:A0=1000 1000:A0=2500 1500:A0=4000 2000:A0=5000 | grep -v '^Loaded' | tr -d '\r' | uniq

python3 tools/sim/models/line_sim.py
```

`avrrun <elf> <end_ms> [event ...]`
- `<ms>:D2=0` / `<ms>:B5=1`: drive a pin low or high at that time (port letter + bit; D2 = PORTD bit 2). / 在该时刻把引脚拉低或拉高
- `<ms>:A0=<mV>`: put a voltage on an analog input. / 给模拟输入加电压
- `WATCH=B5,D2`: log pin changes to stderr. / 把引脚变化打印到 stderr
- `MOTOR=<battery volts>`: TB6612FNG on PWMA = D5, AIN1 = D7, AIN2 = D8 driving a toy gearmotor (0.8 V dead band, 260 counts/s per volt, time constant 50 ms, 10 ms when short-braking) with a quadrature encoder on D2/D3. / 玩具电机 + 编码器模型
- `MPU=1`: MPU-6050 at 0x68: flat, tilted to 30° between 3 and 4 s, held, flat again between 7 and 8 s; gyro bias +1.5 °/s; deterministic noise; I2C bus time is not modelled. / 模拟 MPU-6050，脚本化倾斜，陀螺仪零偏 +1.5 °/s；不模拟 I2C 总线耗时
- VCC, AVCC and AREF are 5.0 V. / 电源与参考电压均为 5.0 V
- Pins with the internal pull-up on read high unless an event drives them; that is why the Month 3 cascade run only pulses the A channels (D2, D3) and the B channels (D10 = B2, D11 = B3) stay high, which the sketch counts as rolling backwards. / 开了内部上拉的引脚在没有事件驱动时读为高电平，所以第 3 个月串级程序的运行只给 A 相（D2、D3）发脉冲，B 相保持高电平，程序把它当作向后滚动

The real (non-simulated) Month 3 outputs, from OpenSCAD and Python calculators, are checked by `examples/month-3/check.sh` instead.
第 3 个月中非仿真的输出（OpenSCAD 与 Python 计算脚本）由 `examples/month-3/check.sh` 检查。

## Adding a new month / 新增月份时

Put sketches in `examples/month-N/<lesson>/`, models here in `models/`, add the run to `reproduce.sh` and the quoted output to `expected/`, and label the output in the lesson with the simulated-output component.
把程序放进 `examples/month-N/<课程>/`，模型放进 `models/`，在 `reproduce.sh` 中加入运行步骤、在 `expected/` 中加入引用的输出，并在课程中用“仿真输出”组件标注。
