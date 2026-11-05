"""latency_budget.py: end-to-end latency -> inference delay d (stdlib).

d = floor(delta / dt) as defined in the RTC paper (arXiv 2506.07339), where
delta is the time from observation to a usable action chunk and dt is the
control period. We also print ceil(delta / dt) as a conservative choice for
LeRobot's inference_delay. Component numbers are copied from published
tables (RTX 4090, not measured on this site); the camera row is the worst-case
age of a frame at 30 fps.
"""

import math

H, S_MIN = 50, 25  # pi0 / pi0.5 horizon and the paper's minimum execution horizon
CAMERA_30FPS = 1000.0 / 30.0

SCENARIOS = (
    ("pi0 on-board", (("image encoders", 14.0), ("observation fwd", 32.0), ("10x action fwd", 27.0))),
    ("pi0 off-board", (("on-board total", 73.0), ("network", 13.0))),
    ("pi0.5+RTC LAN", (("model", 97.43), ("network", 6.89), ("image resize", 1.44), ("other", 3.00))),
    ("pi0.5+RTC +100ms", (("measured total", 108.76), ("injected", 100.0))),
)


def main() -> None:
    print(f"H={H}  s_min={S_MIN}  constraint d <= H - s  ->  d <= {H - S_MIN}")
    print(f"camera frame age at 30 fps: up to {CAMERA_30FPS:.1f} ms (added in the +cam rows)")
    print(f"{'scenario':<22} {'delta_ms':>8} {'d@50Hz':>7} {'ceil':>5} {'d@30Hz':>7} {'ceil':>5} {'fits':>5}")
    for name, parts in SCENARIOS:
        base = sum(ms for _, ms in parts)
        for label, delta in ((name, base), (name + " +cam", base + CAMERA_30FPS)):
            d50 = math.floor(delta / 20.0)
            d30 = math.floor(delta / CAMERA_30FPS)
            c50 = math.ceil(delta / 20.0)
            c30 = math.ceil(delta / CAMERA_30FPS)
            fits = c50 <= H - S_MIN
            print(f"{label:<22} {delta:>8.1f} {d50:>7} {c50:>5} {d30:>7} {c30:>5} {str(fits):>5}")
    print("sync inference would idle about d control steps per chunk; async/RTC hides them.")


if __name__ == "__main__":
    main()
