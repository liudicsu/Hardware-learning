# Lesson 2: 3D printing, materials, calibration & tolerances / 第 2 课：3D 打印，材料、校准与公差

**`snap_fit.py`**: strain and push-on force of a printed cantilever snap-fit arm (straight-beam formulas). The strain limits are cautious rules of thumb, not datasheet values.
打印悬臂卡扣的应变与扣合力（直梁公式）。应变上限是保守的经验值，不是材料手册数据。

```bash
python3 snap_fit.py
```

**`esp32_case.scad`**: a two-part snap-fit case for an ESP32-S3-DevKitC-1 with its headers soldered pins down. Board size from Espressif's v1.1 drawing (62.74 × 25.40 mm); clones differ, so measure yours. The snap arms use the numbers checked by `snap_fit.py`.
ESP32-S3-DevKitC-1（排针朝下焊接）的两件式卡扣外壳。板子尺寸来自乐鑫 v1.1 图纸（62.74 × 25.40 mm），兼容板尺寸不同，请自己测量。卡扣臂尺寸与 `snap_fit.py` 中检查过的一致。

```bash
openscad -o esp32_case.stl esp32_case.scad                     # both parts side by side / 两件并排
openscad -D 'part="base"' -o base.stl esp32_case.scad          # one part / 单件
openscad -D 'part="clash"' -o clash.stl esp32_case.scad        # interference check: "top level object is empty" = no clash
python3 ../cad-parametric/stl_info.py esp32_case.stl
```

Set `clearance` and `fit` to the numbers from your tolerance gauge first. The lid prints flat with its arms standing up, so they bend across the layers: if one snaps, print the lid on its side or use PETG.
先把 `clearance` 和 `fit` 改成你的公差测试件测出的数值。盖子平放打印时卡扣臂是竖着的，弯曲方向垂直于层线：如果断了，就把盖子侧放打印，或改用 PETG。

Rendered and checked in software only; not printed by the site editor. / 只在软件中渲染和检查过，本站编者没有打印过。
