# Batch-21 polish sources — learner-facing ROS wiki archive citation, OpenVLA-OFT card authors, process-label sweep

Base: `e84ac226cb8f0487471e67df5d8b61c4123dfc74` (batch-21 PR3 #187 merged; site **39060**, catalogue **71**).
This PR: site stays **39060**, catalogue stays **71**; **no minute count changed**. **No toy and no `expected/` file changed.**

## Sources

| id | URL | HTTP | What was used |
|---|---|---|---|
| ROS wiki urdf/XML/link, 2024-12-25 archived copy | https://web.archive.org/web/20241225111435/http://wiki.ros.org/urdf/XML/link | 200 | "URDF assumes a negative product of inertia convention", so ixy = −∫ x y dm, the tensor entry J_xy. Already read for batch-21 PR3; only the way the page cites it changed. 以原文为准. |
| openvla-oft-paper | https://arxiv.org/abs/2502.19645 | 200 | Author list on the abstract page: Moo Jin Kim, Chelsea Finn, Percy Liang (same three as `openvla-oft-pdf`). |

The live ROS wiki URL is still not cited on the page, in resources or in the curriculum.

## Item by item

1. **urdf-tf (m4) en/zh, sign-convention sentence**: the pointer to a development note is removed; the sentence now cites "the 2024-12-25 archived copy of the ROS wiki urdf/XML/link page (Wayback Machine)" / "ROS wiki urdf/XML/link 页面的 2024-12-25 存档（Wayback Machine）". The ixy = −∫ x y dm statement and its agreement with J_xy = −m R_x R_y are unchanged.
2. **urdf-tf (m4) en/zh, scope paragraph**: the old "not cited" sentence contradicted the citation above it. It now says the live page served a bot wall, so the live URL is not cited and is not in the lesson's resources, and that what is cited is the 2024-12-25 archived copy.
3. **openvla-oft-paper card**: author "Kim et al." → "Moo Jin Kim, Chelsea Finn, Percy Liang".
4. **Site-wide sweep of lesson prose** (all 142 `src/content/**/{en,zh}.mdx`, outside code blocks, simulated output, inline code and link targets):
   - m6/vla-models en/zh, code-change disclosure: "The batch-19 polish edited only a docstring line" / "batch-19 收尾只改了一行文档字符串" → "A later revision edited only a docstring line" / "后来的一次修订只改了一行文档字符串".
   - m8/async-deployment en/zh, code-change disclosure: "came in the batch-19 polish after review" / "来自审阅后的 batch-19 收尾" → "came in a later revision after review" / "来自审阅后的一次修订".
   - m1/components en/zh, code-change disclosure: "No label changed; the first-run output is kept in the sources note." / "没有标签改变；首次运行的输出保留在来源笔记里。" → "No label changed." / "没有标签改变。"
   - "this batch" / "本批" / "本批次" in prose about source checks:
     - m2/arduino-io en/zh: "could not be resolved during this batch's source check" / "本批次资料核对时未能解析" → "could not be resolved when this lesson's sources were checked" / "核对本课资料时未能解析".
     - m7/perception-to-grasp en/zh: "re-checked on the upstream LICENSE this batch" / "本批已对照上游 LICENSE" → "checked against the upstream LICENSE" / "已对照上游 LICENSE"; "`calib3d.hpp` this batch" / "本批从" → the same sentence without the label.
     - m7/sim-to-real en/zh: "Classic references (re-checked this batch)" / "经典来源（本批再核对）" → "Classic references (re-checked against the originals)" / "经典来源（已对照原文再核对）".
     - resources.ts: the SAM2 card ("re-checked this batch" / "本批核对" → "checked against the upstream LICENSE file" / "已对照上游 LICENSE 文件核对") and the TI SLVA689A card ("during this batch" / "本批次" → "when the sources were checked" / "核对资料时").
   - "this round" / "本轮" in prose about source checks:
     - m4/slam-nav en/zh (two sentences): "this round" / "本轮" → "when the sources were checked" / "核对资料时".
     - m3/gripper-fingers en/zh: "were not opened this round" / "本轮未打开" → "were not opened for this lesson" / "未为本课打开".
     - resources.ts octomap card: "this round" / "本轮" → "when checked" / "核对时".
   - Not changed: legitimate uses such as "LeRobot PR #4783" (an upstream pull request), "batch 8" / "Batch 1" (training batch sizes), `#120` STEP entity ids.
   - Not changed, because they sit inside embedded toy source or toy output that must stay byte-identical to the files: a comment in the m5/camera-calibration toy ("batch-13 lead-lag toy"), a docstring in the m8/async-deployment NORA toy, the "HTTP 500 this round" line printed by the m4/slam-nav OctoMap toy, and the "(polish addition)" / "(added in polish; …)" comment and printed line in the m7/mujoco-so101 toy.

## Toys

No toy edit, no `expected/` change, no number on any page changed. No difference direction changed.

## Lock changes

- New `b21pol` block (tightening):
  - the urdf-tf archive-citation and live-URL sentences (en/zh);
  - no "batch-21 PR3 sources" / "来源说明" / "sources note" on urdf-tf;
  - the live ROS wiki URL still absent from urdf-tf;
  - the openvla-oft-paper author list;
  - the three reworded disclosures;
  - a site-wide check that lesson prose carries no `batch-NN`, `PR N`, `bNNpN`, "sources note(s)", "来源说明" or "来源笔记".
- Two old locks asserted sentences that changed; they now assert the new wording:
  - the b6 polish I²C note (page and resources);
  - the b18pol gripper-fingers "not opened" sentence (en/zh).
- The `b21pol` sweep also rejects "this batch", "本批", "this round" and "本轮" in lesson prose and in resources.ts.
- The b19p2 M2-minutes check message now reads "tip after batch-21 PR2: 3570" (message text only; the asserted value is unchanged).
- The b21p2 marker "**not** cited here" / "**不**引用它" and the b21p2 bot-wall lock still hold unchanged.
- No lock relaxed.
