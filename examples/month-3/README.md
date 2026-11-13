# Month 3 examples / 第 3 个月示例

One folder per lesson. Each folder's README lists what you need and how to run it.
每课一个目录，目录里的 README 写明需要什么、怎样运行。

| Lesson / 课程 | Folder / 目录 | What / 内容 | Checked by / 验证方式 |
| --- | --- | --- | --- |
| 1 CAD & parametric design / CAD 与参数化设计 | [`cad-parametric/`](cad-parametric/) | SG90 servo bracket (OpenSCAD), STL checker / SG90 舵机支架、STL 检查脚本 | `check.sh` (real runs / 真实运行) |
| 2 3D printing / 3D 打印 | [`fdm-printing/`](fdm-printing/) | snap-fit calculator, two-part ESP32 case / 卡扣计算、两件式 ESP32 外壳 | `check.sh` |
| 3 Transmissions & backlash / 传动与回差 | [`transmissions/`](transmissions/) | gear-ratio calculator / 减速比计算 | `check.sh`; backlash model in `tools/sim/` / 回差模型见 `tools/sim/` |
| 4 PID & control / PID 与控制 | [`pid-control/`](pid-control/) | balancer with a cascade outer loop (Uno) / 带串级外环的平衡车（Uno） | `tools/sim/reproduce.sh` (simavr + models / simavr 与模型) |
| 5 SO-101 arm / SO-101 机械臂 | [`so101-arm/`](so101-arm/) | STS3215 packet builder, SDK comparison / STS3215 数据包、与官方 SDK 对比 | `check.sh` |
| 6 Gripper fingers / 夹爪手指 | [`gripper-fingers/`](gripper-fingers/) | fin-ray finger (OpenSCAD), grip-force calculator / 鳍条手指、夹紧力计算 | `check.sh` |

## Run the checks / 运行检查

```bash
sudo apt install openscad python3        # tested with OpenSCAD 2021.01 / 测试版本 OpenSCAD 2021.01
examples/month-3/check.sh                # real runs: prints "same <file>" for each quoted output
pip install -r examples/month-3/requirements.txt   # pinned feetech-servo-sdk==1.0.0: check.sh then also compares packets with Feetech's SDK (12 same instead of 11 + 1 skip) / 安装固定版本的飞特 SDK 后 check.sh 也会与官方 SDK 对比
tools/sim/reproduce.sh                   # simulated outputs (Month 2 and Month 3) / 全部仿真输出
examples/month-3/render_previews.sh      # re-renders the pictures in public/m3/ / 重新渲染课程配图
```

Legacy calculator outputs from `check.sh` are ordinary programs run on a computer. Nothing in this month was printed or run on a real robot by the site editor: the parts were rendered and checked in software, and the printed fit is for you to find out.
`check.sh` 原计算器输出是电脑上直接运行的普通程序。本月的零件和程序都没有被本站编者打印或装到真机上：零件只在软件中渲染和检查过，打印后能不能装上，要靠你自己验证。

Different OpenSCAD versions write a different number of triangles; `check.sh` ignores that one number.
不同版本的 OpenSCAD 生成的三角形数量不同，`check.sh` 会忽略这个数。

## Batch-5 PR1 / 第5批 PR1

`transmissions/backlash_loop_toy.py`: standard-library synthetic simulation, no hardware; expected output in `expected/backlash_loop_toy.txt`, included in `check.sh`. / 标准库合成仿真，不是硬件测量，输出由 `check.sh` 核对。

## Batch-20 PR1 / 第20批 PR1

`transmissions/leadscrew_self_locking_toy.py`: standard-library synthetic square-thread statics (steep vs fine vs vibrated lead), no hardware; expected output in `expected/leadscrew_self_locking_toy.txt`, included in `check.sh`. Real jack 本页未运行. / 标准库合成的方螺纹丝杠静力学（粗导程、细导程、振动），不是硬件测量，输出由 `check.sh` 核对。

## Batch-21 PR1 / 第21批 PR1

`fdm-printing/fdm_build_orientation_anisotropy_toy.py`: standard-library synthetic three-point-bending beam (flatwise vs upright vs an isotropic guess vs edgewise), no hardware; expected output in `expected/fdm_build_orientation_anisotropy_toy.txt`, included in `check.sh`. Real printer / Instron 本页未运行. / 标准库合成的三点弯曲梁（平放、直立、各向同性猜测、侧放），不是实验室测量，输出由 `check.sh` 核对。

## so101-arm/ — Voltage sag on the shared servo rail / 共享舵机电源轨的电压跌落

`so101-arm/so101_shared_rail_sag_toy.py`: standard-library synthetic DC resistor chain for the SO-101's daisy-chained 5 V servo rail (ideal wiring vs declared thin wiring vs thicker wiring, four stall regimes) on shared resistance and current draws; no hardware; expected output in `expected/so101_shared_rail_sag_toy.txt`, included in `check.sh`. Real arm / PSU / stall test 本页未运行. / 标准库合成的 SO-101 菊花链 5 V 舵机电源轨直流电阻链（理想布线、声明的细线、粗线，四种堵转情形），不是实测，输出由 `check.sh` 核对。

## pid-control/ — Ziegler–Nichols tuning from the ultimate gain / 从临界增益出发的 Ziegler–Nichols 整定

`pid-control/ziegler_nichols_ultimate_gain_toy.py`: standard-library synthetic first-order lag with pure delay; the ultimate gain and period found by a P-only oscillation test, then classic Ziegler–Nichols PID vs the no-overshoot row vs P only, on shared load steps and measurement noise (three regimes); no hardware; expected output in `expected/ziegler_nichols_ultimate_gain_toy.txt`, included in `check.sh`. Real plant / autotune 本页未运行. / 标准库合成的一阶滞后加纯滞后对象：先用只有 P 的振荡试验找出临界增益与周期，再在共用负载阶跃和测量噪声下比较经典 Ziegler–Nichols PID、no overshoot 行和只用 P（三种情形），不是实测，输出由 `check.sh` 核对。
