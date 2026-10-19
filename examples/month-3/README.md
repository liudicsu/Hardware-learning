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
pip install feetech-servo-sdk            # optional: also compares packets with Feetech's SDK / 可选
tools/sim/reproduce.sh                   # simulated outputs (Month 2 and Month 3) / 全部仿真输出
examples/month-3/render_previews.sh      # re-renders the pictures in public/m3/ / 重新渲染课程配图
```

Outputs from `check.sh` are ordinary programs run on a computer, not simulations. Nothing in this month was printed or run on a real robot by the site editor: the parts were rendered and checked in software, and the printed fit is for you to find out.
`check.sh` 里的输出是电脑上直接运行的普通程序，不是仿真。本月的零件和程序都没有被本站编者打印或装到真机上：零件只在软件中渲染和检查过，打印后能不能装上，要靠你自己验证。

Different OpenSCAD versions write a different number of triangles; `check.sh` ignores that one number.
不同版本的 OpenSCAD 生成的三角形数量不同，`check.sh` 会忽略这个数。
