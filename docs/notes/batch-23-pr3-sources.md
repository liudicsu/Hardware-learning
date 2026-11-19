# Batch-23 PR3 sources

Base `b2379b6ef2e03301c3ecd2de44edee4d35e930a1` (batch-23 PR2 #194 merged; site **40860**). This PR: site **40860→41220** (41220=40860+180+180), M9 **4110→4290**, M6 **3840→4020**, catalogue still **71**. Hosts: `llm-skill-planning` 240→420, `policy-evaluation` 540→720. Head of this branch is recorded at open time in the PR; locks check the note, not a later SHA.

## Sources actually opened

- ChatVLA-2 abstract https://arxiv.org/abs/2505.21906 — 200; title and five authors in abstract-page order; v2, submitted 28 May 2025, this version 29 May 2025.
- ChatVLA-2 HTML https://arxiv.org/html/2505.21906 — 200.
- ChatVLA-2 PDF https://arxiv.org/pdf/2505.21906 — 200; v2 body read (dynamic MoE, two-stage training, Tables 1–4, math-matching / toy placement).
- Hi Robot abstract https://arxiv.org/abs/2502.19417 — 200; title and 15 authors in abstract-page order; v2, submitted 26 Feb 2025, this version 15 Jul 2025.
- Hi Robot HTML https://arxiv.org/html/2502.19417 — 200.
- Hi Robot PDF https://arxiv.org/pdf/2502.19417 — 200; v2 body read (§4.1–4.2 hierarchy and interaction, §5.3–5.4 results and ablations, limitations).

Author order and contribution marks (以原文为准):

- ChatVLA-2 authors in abstract-page order, also the PDF order: Zhongyi Zhou, Yichen Zhu, Junjie Wen, Chaomin Shen, Yi Xu. The PDF marks Zhou and Zhu with an asterisk usually read as equal contribution, and marks Yichen Zhu with a dagger as corresponding author. Those asterisks are visible on the PDF; the arXiv HTML conversion shows both footnotes as a dagger and drops the asterisk; the order is still the same as the PDF. The abstract page lists the five names without those marks.
- Hi Robot authors in abstract-page order, also the PDF and HTML order: Lucy Xiaoyang Shi, Brian Ichter, Michael Equi, Liyiming Ke, Karl Pertsch, Quan Vuong, James Tanner, Anna Walling, Haohuan Wang, Niccolo Fusai, Adrian Li-Bell, Danny Driess, Lachy Groom, Sergey Levine, Chelsea Finn. No equal-contribution mark on the PDF or the HTML. Correspondence is to Physical Intelligence at research@physicalintelligence.company, not a personal corresponding-author mark on one name. Affiliations Physical Intelligence / Stanford / UC Berkeley appear on the PDF and do not change the order.

Cards: `chatvla2-paper`, `hirobot-paper`. Paper figures are 以原文为准. Real-robot, GPU, and paper-task success rates: 本页未运行.

## Toys and first-run results

Common random numbers; five seeds; stdlib; declared toy parameter header includes every setup value used in the lesson prose.

ChatVLA-2 (`chatvla2_reasoning_following_toy.py`):

- Declared header: `seeds=5 a_min=1 a_max=9 b_min=1 b_max=9 n_id_eq=12 n_ood_eq=20 n_cards=5 n_arith=40 n_add_pairs=81 untrained_y=-100.0000 hand_a=7 hand_b=5 (declared)`
- in_domain: A and B tie on pick_acc and reason_then_pick (identical on every seed, both 1.0000). The pre-declared "may near-tie" came back as a tie and is kept.
- ood: B−A pick_acc +0.6100±0.0548 and reason_then_pick +0.9800±0.0447, clear, 5/5 (held). C loses on OOD versus B: pick_acc −0.9000±0.0791 and reason_then_pick −1.0000±0.0000, clear, 5/5 (held).

Hi Robot (`hi_robot_hierarchical_feedback_toy.py`):

- Declared header: `seeds=5 n_scenes=8 n_steps=6 n_atomic_steps=3 interrupt_after=2 replan_every=1 n_true_trash=2 n_forbidden=1 n_objects=4 hand_trash=2 hand_forbidden=1 (declared)`
- atomic_no_interrupt: A and B tie on instruction_acc and task_progress (identical on every seed, both 1.0000). The pre-declared "may near-tie" came back as a tie and is kept.
- mid_task_correction: B−A instruction_acc +1.0000±0.0000 and task_progress +0.3333±0.0000, clear, 5/5 (held). C loses the same way (held). A and C tie (both ignore the mid-task line).

## Declared expectations that did not hold

None.

## Post-hoc choices

None. No constant, arm, metric or regime was changed after the first run.

## Code changes after the first run

After the first run, only the SimOutput fence and the source="model" label were changed, and a print-only line `hand_calc card range = 2 to 18` was added to the ChatVLA-2 toy and expected/ header; result blocks were not changed. No retune.

## Mismatch with §9

None on the pre-declared cells. The in-domain / atomic "may near-tie" cells came back as identical ties; they are kept, not retuned.

## Lock changes

New batch-23 PR3 block in `tools/check_diagrams.mjs` (toys, expected, CRN, label order, difference directions, sources, plans, README, declared regimes, post-first-run code change) plus `tools/test_b23p3_chatvla2_hi_robot_toys.py`. Tipped site-total, host-minute, month-total and Current-header locks only (40860→41220, M9 4110→4290, M6 3840→4020, llm-skill-planning 240→420, policy-evaluation 540→720). No lock relaxed.

- README `/40 860/` and `约 40 860 分钟` → `/41 220/` and `约 41 220 分钟`.
- Curriculum sum checks `40860` → `41220`; the current month-total table and the live M6/M9 sum checks 3840→4020 and 4110→4290 (including the obs3 / b17p3 host-minute 540→720 on policy-evaluation, and the m8 presence check 180/240/300→180/420/300 after the last 240-minute host moved).
- Tightened the b17p3 Summary number lock the same way OpenVLA-OFT was scoped: the Hi Robot Summary bullet is checked against `hi_robot_hierarchical_feedback_toy.txt`; Magma numbers still have to appear in the Magma expected output.
