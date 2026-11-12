# Month 1 examples / 第 1 个月示例

## python-terminal/

`ohm.py`, `resistors.py` and `log.py` from the lesson **Python & the terminal** (Python 与终端). Plain Python 3.9+, no packages, no hardware.
无需安装任何包，也不需要硬件，Python 3.9 及以上即可。

```bash
cd examples/month-1/python-terminal
python3 ohm.py current --volts 5 --ohms 220            # 22.7 mA
python3 ohm.py divider --vin 5 --r1 10000 --r2 4700    # 1.599 V
python3 resistors.py
python3 log.py                                         # writes measurements.json here
```

Check every quoted output at once (runs in a temporary folder, leaves nothing behind):
一次性核对课程里引用的全部输出（在临时目录运行，不留文件）：

```bash
examples/month-1/check.sh
```

The legacy python-terminal examples are real program runs. / 原 python-terminal 示例是电脑上的程序运行。

## Batch-5 PR1 / 第5批 PR1

`bench-multimeter/dmm_uncertainty_toy.py`: standard-library synthetic simulation, no hardware; expected output in `expected/dmm_uncertainty_toy.txt`, included in `check.sh`. / 标准库合成仿真，不是硬件测量，输出由 `check.sh` 核对。

## bench-multimeter/ — Kelvin four-wire / 开尔文四线

`bench-multimeter/kelvin_four_wire_sense_toy.py`: standard-library synthetic DC model of two-wire vs Kelvin (four-terminal) resistance measurement, no hardware; expected output in `expected/kelvin_four_wire_sense_toy.txt`, included in `check.sh`. / 标准库合成直流模型，对比两线法与开尔文四线法，不是硬件测量，输出由 `check.sh` 核对。

## python-terminal/ — Nyquist and aliasing / 奈奎斯特与混叠

`python-terminal/nyquist_aliasing_toy.py`: standard-library synthetic sampling model (ideal samples, plain DFT) comparing a 50 Hz rate, 200 Hz with an anti-alias prefilter and 200 Hz without one; no hardware; expected output in `expected/nyquist_aliasing_toy.txt`, included in `check.sh`. / 标准库合成采样模型（理想采样、普通 DFT），比较 50 Hz、带抗混叠前置滤波的 200 Hz 与不滤波的 200 Hz；不是硬件测量，输出由 `check.sh` 核对。

## components/ — Bridge rectifier and ripple / 整流桥与纹波

`components/bridge_rectifier_ripple_toy.py`: standard-library synthetic model of a half-wave rectifier, a four-diode bridge and the bridge without its smoothing capacitor (ideal diodes plus forward drop, forward Euler on the capacitor node); no mains or hardware; expected output in `expected/bridge_rectifier_ripple_toy.txt`, included in `check.sh`. / 标准库合成模型，比较半波整流、四二极管整流桥和不接滤波电容的整流桥（理想二极管加正向压降，电容节点用前向欧拉积分）；不接市电、不是硬件测量，输出由 `check.sh` 核对。

## bench-multimeter/ — True RMS vs average-responding / 真有效值与平均值响应

`bench-multimeter/true_rms_vs_average_responding_toy.py`: standard-library synthetic sampled-waveform model of a true-RMS estimator, a sine-calibrated average-responding meter and a peak/sqrt(2) sine assumption; no hardware; expected output in `expected/true_rms_vs_average_responding_toy.txt`, included in `check.sh`. / 标准库合成采样波形模型，比较真有效值、按正弦校准的平均值响应表和峰值/√2 的正弦假设；不是硬件测量，输出由 `check.sh` 核对。

## components/ — Zener shunt and LDO headroom / 齐纳并联稳压与 LDO 压差裕量

`components/zener_shunt_ldo_headroom_toy.py`: standard-library synthetic DC model of a Zener shunt regulator, an LDO stand-in with a declared headroom, and an uncapped shunt; no hardware; expected output in `expected/zener_shunt_ldo_headroom_toy.txt`, included in `check.sh`. / 标准库合成直流模型，比较齐纳并联稳压、带声明压差裕量的 LDO 替身和无串联电阻的齐纳；不是硬件测量，输出由 `check.sh` 核对。

## Batch-21 PR1 / 第21批 PR1

`components/peukert_rate_capacity_toy.py`: standard-library synthetic constant-current discharge (nameplate clock vs Peukert vs k = 1 vs a high-current cap) on a shared 100 Ah / 20 h rating, no hardware; expected output in `expected/peukert_rate_capacity_toy.txt`, included in `check.sh`. Real pack 本页未运行. / 标准库合成的恒流放电（铭牌时钟、Peukert、k = 1、大电流上限），不是电池实测，输出由 `check.sh` 核对。

## soldering/ — Crimp or solder, and strain relief / 压接还是焊接，以及应力释放

`soldering/crimp_vs_solder_strain_relief_toy.py`: standard-library synthetic strand-fatigue and contact-resistance stand-in comparing an unrelieved solder joint, a correctly sized crimp, an under-crimp and a solder joint with strain relief on shared strand and contact draws; no hardware; expected output in `expected/crimp_vs_solder_strain_relief_toy.txt`, included in `check.sh`. Real crimp tool / IPC-A-610 inspection 本页未运行. / 标准库合成的线股疲劳与接触电阻替身，比较无应力释放的焊点、尺寸合适的压接、压接不足和加应力释放的焊点；不是压接实测，输出由 `check.sh` 核对。
