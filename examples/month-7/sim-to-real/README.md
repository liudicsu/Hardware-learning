# sim-to-real

- `sysid_fit.py` — fit a 1st-order lag τ from a synthetic step response (rel err < 5 %).
- `randomize_eval.py` — domain-randomisation scan over friction × delay × z-bias with Wilson intervals.
- `contact_dr_toy.py` — contact-parameter DR (friction µ, mass) vs latency-only randomisation: both arms tune the same push speed with the same budget and seed stream, then are scored at nominal and shifted µ / mass. Not sysid; toy friction ≠ MuJoCo. 接触参数域随机化与仅延迟随机化的公平对比；非系统辨识；玩具摩擦 ≠ MuJoCo；真机本页未运行。

Hardware steps in the lesson are marked「需硬件」/ "needs hardware".
