# Month 5 follow-up PR3 (F5 + F6)

Base: main after observability PR2 (`61c7358`). Site was 71 / 16 800.

| Unit | Host | Before → After | Toy |
|---|---|---|---|
| F5 | 5.1 `control-modelling` | 240 → 420 | `sysid_pe_compare_toy.py` |
| F6 | 5.2 `state-space-lqr` | 240 → 420 | `lqr_model_error_toy.py` |

Month 5 total **1 260 → 1 620 min**. Together with F7 (+150 on Month 6): site **17 310 min**.

Locked teaching points: PE = regressor richness (not “2 params ⇒ step unidentifiable”); fair energy + shared noise; EE-OLS bias caveat; `oracle_fullstate` privileged ≠ equal-info; not H∞; Luenberger via CE295 Ch.2.
