# Lesson 6: Design your own gripper fingers / 第 6 课：设计你自己的夹爪手指

**`grip_force.py`**: how hard a two-finger gripper must squeeze so an object does not slip, for PLA and TPU fingers. The friction values are rough guesses: measure yours with a tilted board (μ = tan angle).
两指夹爪需要多大夹紧力才不打滑（PLA 与 TPU 手指）。摩擦系数只是粗略估计，请用斜板法自己测（μ = tan 角度）。

```bash
python3 grip_force.py
```

**`finray_finger.scad`**: a parametric fin-ray style finger to print in TPU (two thin flanks joined by ribs). The mounting block is generic: measure the jaw you bolt it to. For the SO-101 itself, start from the STEP files in the [SO-ARM100 repository](https://github.com/TheRobotStudio/SO-ARM100).
可用 TPU 打印的参数化鳍条结构手指（两片薄侧壁由肋条相连）。安装块是通用的，请按你的夹爪实测修改。给 SO-101 设计手指时，请从 SO-ARM100 仓库里的 STEP 文件开始。

```bash
openscad -o finray_finger.stl finray_finger.scad
python3 ../cad-parametric/stl_info.py finray_finger.stl 1.21     # TPU density ≈ 1.21 g/cm³
```

Rendered and checked in software only; not printed by the site editor. / 只在软件中渲染和检查过，本站编者没有打印过。
