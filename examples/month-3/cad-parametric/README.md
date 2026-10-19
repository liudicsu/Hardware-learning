# Lesson 1: CAD, pick a tool, then design with parameters / 第 1 课：CAD，选好工具，用参数设计

**`servo_bracket.scad`**: a parametric L-bracket for an SG90-class micro servo. Every size is a named parameter at the top of the file.
参数化的 SG90 类微型舵机 L 形支架，所有尺寸都是文件开头的命名参数。

Sizes come from the common SG90 drawing (body 22.2 × 11.8 mm, 32.2 mm across the tabs). The tab hole spacing (27.5 mm) is **not** on that drawing and sources disagree: measure your own servo with calipers before printing.
尺寸来自常见的 SG90 图纸（机身 22.2 × 11.8 mm，含安装耳 32.2 mm）。安装孔距（27.5 mm）**不在**这张图上，各来源说法不一：打印前请用卡尺量你自己的舵机。

Hardware to print it / 打印所需: an SG90 (or clone), two M2 self-tapping screws for the tabs, two M3 screws for the foot.
一个 SG90（或兼容品），两颗 M2 自攻螺丝固定安装耳，两颗 M3 螺丝固定底座。

```bash
openscad -o servo_bracket.stl servo_bracket.scad                  # render
openscad -D clearance=0.15 -o b.stl servo_bracket.scad            # change one parameter / 改一个参数
python3 stl_info.py servo_bracket.stl                             # size, watertight, volume, mass
```

**`stl_info.py`**: checks an STL before slicing (size, watertight mesh, volume, solid mass). No packages needed.
切片前检查 STL（尺寸、网格是否封闭、体积、实心质量），不需要第三方库。

Rendered and checked in software only; not printed by the site editor. / 只在软件中渲染和检查过，本站编者没有打印过。
