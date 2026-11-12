# 10.3 edge-deploy-checklist

- `int8_quant_toy.py` — symmetric / asymmetric, per-tensor / per-channel int8 maths from the ONNX Runtime docs, with and without one outlier.
- `vla_edge_budget_toy.py` — weights-only memory (params × bytes) for SmolVLA / π0-class / OpenVLA-class with parameter counts from their papers (activations, KV cache and vision buffers excluded), plus chunk / Hz / sync idle and the 6.3 async threshold g ≥ (ℓ_S / Δt) / n. 仅权重显存与动作块时序；无设备实测，Jetson / Pi 本页未运行。
- `latency_budget.py` — published latency components (π0 Table I, RTC paper Table 2) plus a 30 fps camera frame age → inference delay `d` at 50 Hz and 30 Hz.

```bash
python3 int8_quant_toy.py    # ../expected/int8_quant_toy.txt
python3 latency_budget.py    # ../expected/latency_budget.txt
python3 vla_edge_budget_toy.py    # ../expected/vla_edge_budget_toy.txt
python3 vla_adapter_bridge_attention_toy.py    # ../expected/vla_adapter_bridge_attention_toy.txt
```

Not run here / 本页未运行 (CI installs nothing extra): ONNX Runtime `quantize_dynamic` / `quantize_static`, TensorRT export, any Jetson measurement. Sketch only:

```python
from onnxruntime.quantization import quantize_dynamic, QuantType
quantize_dynamic("model.onnx", "model.int8.onnx", weight_type=QuantType.QInt8)
```

## Batch-18 PR3: `vla_adapter_bridge_attention_toy.py`

Standard-library VLA-Adapter Bridge Attention stand-in: a larger plain concat-MLP head vs a tiny backbone with Bridge Attention vs the same tiny policy with shuffled VL conditions, on shared demonstrations (five seeds). Size and a multiply-add FLOP / latency proxy are printed; paper 0.5B / 8 h / LIBERO numbers 以论文为准. GPU / 0.5B training 本页未运行. Not SmolVLA, not the weights-only budget table, not OpenVLA-OFT. First-run architecture is replayed by `_vla_adapter_firstrun.py` and printed as an alternative. / 标准库 VLA-Adapter Bridge Attention 替身：大的普通头、小主干 + Bridge Attention、打乱条件对照；参数量与乘加代理；论文数字以论文为准。
