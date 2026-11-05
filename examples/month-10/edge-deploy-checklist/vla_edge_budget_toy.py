#!/usr/bin/env python3
"""vla_edge_budget_toy.py: weights-only memory and chunk timing for compact VLAs (stdlib).

Part 1, memory. weights_GB = params x bytes_per_param / 1e9, for three model
sizes whose parameter counts are taken from their papers (labelled; not
measured here):
  SmolVLA        0.45e9  (arXiv 2506.01844: "450 million parameters")
  pi0-class      3.3e9   (arXiv 2410.24164: 3B PaliGemma + 300M action expert)
  OpenVLA-class  7e9     (arXiv 2406.09246: "7B-parameter")
WEIGHTS ONLY. Activations, the KV cache, vision-encoder / image buffers, the
framework / CUDA context and the OS are EXCLUDED and not estimated: a weights
number is a lower bound, never "it fits".

Part 2, timing. Chunk of n actions at control period dt lasts n * dt. Sync
inference idles l_S per chunk; async (6.3, g = remaining-queue fraction that
triggers the next request) avoids idling when g >= (l_S / dt) / n. If that
g_min exceeds 1, even a request every tick cannot keep the queue fed. The
l_S values are lesson-chosen what-ifs, not device measurements; Jetson / Pi
runs are not done on this page (本页未运行).
usage: python3 vla_edge_budget_toy.py
"""
from __future__ import annotations

MODELS = (                       # label, params, source
    ("SmolVLA", 0.45e9, "2506.01844"),
    ("pi0-class", 3.3e9, "2410.24164"),
    ("OpenVLA-class", 7.0e9, "2406.09246"),
)
PRECISIONS = (("fp32", 4.0), ("bf16", 2.0), ("int8", 1.0), ("int4", 0.5))
EXCLUDED = ("activations", "KV cache", "vision-encoder / image buffers", "framework + CUDA context", "OS")
N_CHUNK = 50
RATES_HZ = (30, 50)
LATENCIES_S = (0.05, 0.293, 0.8, 2.0)   # what-if l_S; 0.293 s is the 6.3 toy's mean draw


def main() -> None:
    print("part 1: weights-only memory (GB = params x bytes / 1e9); parameter counts from the papers")
    print(f"{'model':<14} {'params':>7} {'arXiv':>10} " + " ".join(f"{p:>6}" for p, _ in PRECISIONS))
    for name, n, src in MODELS:
        print(f"{name:<14} {n / 1e9:6.2f}B {src:>10} " + " ".join(f"{n * b / 1e9:6.2f}" for _, b in PRECISIONS))
    print("EXCLUDED (not estimated): " + ", ".join(EXCLUDED))
    print()
    print(f"part 2: chunk timing, n={N_CHUNK}; g_min = (l_S / dt) / n (6.3); l_S values are what-ifs")
    print(f"{'Hz':>3} {'chunk_s':>7} {'l_S_s':>6} {'sync_idle_%':>11} {'g_min':>6}  verdict")
    for hz in RATES_HZ:
        dt = 1.0 / hz
        for lat in LATENCIES_S:
            chunk_s = N_CHUNK * dt
            idle = lat / (lat + chunk_s)
            g_min = (lat / dt) / N_CHUNK
            if g_min <= 1.0:
                verdict = f"async can hide it with g >= {g_min:.3f}"
            else:
                verdict = "even g = 1 underruns: shorter l_S, longer chunk or lower Hz"
            print(f"{hz:3d} {chunk_s:7.3f} {lat:6.3f} {100 * idle:11.1f} {g_min:6.3f}  {verdict}")
    g_check = (0.293 / (1 / 30)) / N_CHUNK
    assert abs(g_check - 0.176) < 5e-4, g_check
    assert MODELS[2][1] * 2.0 / 1e9 == 14.0
    print(f"check: 30 Hz, l_S=0.293 s, n=50 -> g_min={g_check:.3f} (matches the 6.3 toy); "
          "weights only, no device measured, Jetson / Pi 本页未运行")


if __name__ == "__main__":
    main()
