# Examples / 示例代码

Every program quoted in a lesson lives here, byte for byte the same as the code block on the site. Each lesson's code block links to its file here.
课程里引用的每一段程序都放在这里，与网站代码块逐字节一致；课程中的代码块都链接到这里的对应文件。

| Folder / 目录 | What / 内容 | How it was checked / 如何验证 |
| --- | --- | --- |
| [`month-1/`](month-1/) | Python command-line tools (Lesson: Python & the terminal) / Python 命令行小工具 | Run on a computer; `month-1/check.sh` compares with the lesson / 在电脑上直接运行，`month-1/check.sh` 与课程输出对比 |
| [`month-2/`](month-2/) | Arduino Uno and ESP32 sketches, one folder per lesson / Arduino Uno 与 ESP32 程序，每课一个目录 | Uno sketches run in the simavr simulator, ESP32 and line-follower sketches compiled only; see [`../tools/sim/`](../tools/sim/) / Uno 程序在 simavr 模拟器中运行；ESP32 与循线程序只编译 |
| [`month-3/`](month-3/) | OpenSCAD parts, Python calculators and the balancer cascade sketch, one folder per lesson / OpenSCAD 零件、Python 计算脚本和平衡车串级程序，每课一个目录 | Parts and calculators run on a computer, `month-3/check.sh` compares with the lessons; the control models and the sketch go through `tools/sim/reproduce.sh` / 零件和计算脚本在电脑上运行，由 `month-3/check.sh` 比对；控制模型与程序由 `tools/sim/reproduce.sh` 复现 |

**The standard for every month / 每个月都遵循的规范**
- `examples/month-N/<lesson-slug>/` holds the code of that lesson, with a `README.md` (hardware, wiring, how to build).
  `examples/month-N/<课程 slug>/` 存放该课代码，并附 `README.md`（硬件、接线、如何编译）。
- Simulations, models and harnesses live in `tools/sim/`; `tools/sim/reproduce.sh` re-creates every simulated output and diffs it against `tools/sim/expected/`.
  仿真脚本、模型与测试工具放在 `tools/sim/`；`tools/sim/reproduce.sh` 重新生成所有仿真输出并与 `tools/sim/expected/` 比对。
- Outputs from a simulator or toy model are labelled **Simulated output / 仿真输出** in the lessons. Real hardware will give different numbers.
  课程中来自模拟器或玩具模型的输出都标注为“仿真输出”，真实硬件上的数值会不同。
