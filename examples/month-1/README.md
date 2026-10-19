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

These are real runs on a computer, not simulations. / 这些是电脑上的真实运行结果，不是仿真。
