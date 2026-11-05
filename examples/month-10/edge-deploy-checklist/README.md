# 10.3 edge-deploy-checklist

- `int8_quant_toy.py` — symmetric / asymmetric, per-tensor / per-channel int8 maths from the ONNX Runtime docs, with and without one outlier.
- `latency_budget.py` — published latency components (π0 Table I, RTC paper Table 2) plus a 30 fps camera frame age → inference delay `d` at 50 Hz and 30 Hz.

```bash
python3 int8_quant_toy.py    # ../expected/int8_quant_toy.txt
python3 latency_budget.py    # ../expected/latency_budget.txt
```

Not run here / 本页未运行 (CI installs nothing extra): ONNX Runtime `quantize_dynamic` / `quantize_static`, TensorRT export, any Jetson measurement. Sketch only:

```python
from onnxruntime.quantization import quantize_dynamic, QuantType
quantize_dynamic("model.onnx", "model.int8.onnx", weight_type=QuantType.QInt8)
```
