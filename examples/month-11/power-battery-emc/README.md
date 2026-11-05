# 11.1 power-battery-emc

`power_budget_toy.py` — one-way IR drop and raw fuse/peak ratio (stdlib).
`power_roundtrip_loss_toy.py` — round-trip IR, I²R loss, and fuse **data gates**
(`insufficient_data` / `reject_known_constraint` only; never `ok_slow_blow`).
Currents are **example assumptions**, not measured on this site.
Changing a real fuse is **not run here**.
