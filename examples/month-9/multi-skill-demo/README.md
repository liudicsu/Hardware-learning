# multi-skill-demo (Month 9.7)

Thin system demo gate — **does not replace** the Month 8.7 capstone.

## Reproduce

```bash
cd ~/Hardware-learning/examples/month-9/multi-skill-demo
python3 demo_gate.py --scenario=table     # or contact / nav
python3 demo_gate.py --all                # CI path: all three, fixed seed=9
```

CI compares `--all` output with `../expected/demo_gate.txt`.

## Gates (3/3)

1. `skill_graph_legal` — every edge endpoint is a node; seq-edges form a DAG
2. `recovery_edge_fired` — at least one recovery edge was taken
3. `report_fields_complete` — scenario / seed / status / recovery_edge present

## Safety checklist ticks (reuse Month 8 notions — do not rewrite that lesson)

- [ ] E-stop / 急停 reachable before any real-robot path
- [ ] Watchdog covers command timeout / illegal commands (Month 8)
- [ ] Semantic failures use detect → retry / backup (Month 9.5), not the watchdog alone
- [ ] No paid LLM keys in the repo; fake scores only for planning stubs
- [ ] CI runs in *your* student repository (Month 8 devops convention)

## 30s screen-rec note

Optional: record ≤30 s of the terminal run (`demo_gate.py --scenario=…`) or a sim window.
**本页未强制真机** — a CPU terminal capture is enough for the thin demo.
