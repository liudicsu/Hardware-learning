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
