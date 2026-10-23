# Month 6 wording pass — report

## Section A: replacements

| file:line | old phrase | new wording (short) |
|---|---|---|
| src/content/m6/act-diffusion/zh.mdx:1 | 人不是这样；会错得很厉害 | 人的操作不是这样；会产生系统性错误 |
| src/content/m6/act-diffusion/en.mdx:1 | People don't; gets this badly wrong | Human operators do not; fails in a systematic way |
| src/content/m6/act-diffusion/zh.mdx:238 | 活下来的那些 | 其余运行之所以成功 |
| src/content/m6/act-diffusion/en.mdx:238 | The ones that survive | The remaining runs succeed |
| src/content/m6/act-diffusion/zh.mdx:240 | 夹爪在两种抓法中间犹豫不决 | 夹爪停在两种抓法之间的中间位置 |
| src/content/m6/act-diffusion/en.mdx:240 | hesitates halfway between two grasps | stops at an intermediate pose halfway between two grasps |
| src/content/m6/act-diffusion/zh.mdx:298 | 像玩具模型那样比较它们 | 按玩具模型的方式比较它们 |
| src/content/m6/act-diffusion/zh.mdx:302 | 慢慢往两个选项的中间挪，或者犹豫不决 | 逐渐移向两个选项的中间，或在两者之间停留 |
| src/content/m6/act-diffusion/en.mdx:302 | creeps slowly towards the middle … or hesitates | moves gradually towards the middle … or stalls between them |
| src/content/m6/behaviour-cloning/zh.mdx:1 | 就不知道该怎么办了 | 就没有可用的动作输出 |
| src/content/m6/behaviour-cloning/en.mdx:1 | it has no idea what to do | it has no learned action for that state |
| src/content/m6/behaviour-cloning/zh.mdx:15 | 它扮演拿着主臂的你；像一个慢慢操作、非常仔细的人 | 示范由你操作主臂录制；本课模型无执行器噪声录制，各帧在中心线附近，不含恢复动作 |
| src/content/m6/behaviour-cloning/en.mdx:15 | plays the role of you; like a careful operator moving slowly | demos recorded by you moving the leader arm; this model has no actuator noise, frames on the centre line, no recovery actions |
| src/content/m6/behaviour-cloning/zh.mdx:289 | 就像上面用 100 次固定种子的运行那样 | 如上面的 100 次固定种子运行 |
| src/content/m6/behaviour-cloning/zh.mdx:291 | 先看是哪里（就像 "wall hits at" 那一行） | 先确定失败位置（"wall hits at" 那一行） |
| src/content/m6/behaviour-cloning/en.mdx:291 | look at where (like the "wall hits at" line) | identify where it fails (the "wall hits at" line) |
| src/content/m6/policy-evaluation/zh.mdx:1 | 100 次试验不是白来的；诚实的数字 | 100 次试验需要成本；可靠的估计 |
| src/content/m6/policy-evaluation/en.mdx:1 | not get 100 trials for free; honest numbers | 100 trials are not without cost; reliable estimates |
| src/content/m6/policy-evaluation/zh.mdx:132 | 同一个策略，不同的日子 | 同一个策略，不同的会话 |
| src/content/m6/policy-evaluation/en.mdx:132 | The same policy on different days | The same policy across sessions |
| src/content/m6/policy-evaluation/zh.mdx:134 | 就像在十个不同的下午测试它 | 即十次独立的评估会话 |
| src/content/m6/policy-evaluation/en.mdx:134 | as if you tested it on ten different afternoons | i.e. ten independent evaluation sessions |
| src/content/m6/policy-evaluation/zh.mdx:145 | 策略一点没变；恰好在其中两组之间改了点什么 | 策略并未改变；如果在两次会话之间做了改动 |
| src/content/m6/policy-evaluation/en.mdx:145 | never changed; you would be convinced it mattered either way | did not change; you would attribute the difference to it |
| src/content/m6/policy-evaluation/zh.mdx:163 | 每次不一致都像抛硬币；这么一边倒；毫无疑问更好 | 每次不一致相互独立且落在任一边的概率相等；如此不对称；显著更好 |
| src/content/m6/policy-evaluation/en.mdx:163 | a coin flip; a split this lopsided; better beyond doubt | independent and equally likely; a split this asymmetric; significantly better |
| src/content/m6/policy-evaluation/zh.mdx:183 | 像第 1 课 67 % 对 99 % 这样大的差别；好几天的手动复位 | 第 1 课 67 % 对 99 % 这样大的差别；数天的手动复位 |
| src/content/m6/policy-evaluation/en.mdx:183 | shows up in about 20 trials; days of resetting by hand | detectable with about 20 trials; several days of manual resets |
| src/content/m6/policy-evaluation/zh.mdx:209 | 用陌生人也能照着判断的话写 | 写成其他人无需了解实现也能照着执行的判定标准 |
| src/content/m6/policy-evaluation/en.mdx:209 | in words a stranger could apply | as an operational criterion another person can apply without knowing the implementation |
| src/content/m6/policy-evaluation/zh.mdx:218 | “差一点就成了”在这一组算成功 | 同一个接近成功的结果在一组算成功 |
| src/content/m6/policy-evaluation/en.mdx:218 | "It nearly got it" counted as success | If the same near-miss counts as success |
| src/content/m6/specialisation-portfolio/zh.mdx:1 | 啃过控制与运动学的数学 | 学过控制与运动学的数学 |
| src/content/m6/specialisation-portfolio/zh.mdx:15 | 哪个领域最火；能熬过枯燥部分 | 哪个领域需求最大；能坚持学完枯燥部分 |
| src/content/m6/specialisation-portfolio/en.mdx:15 | which field is hottest | which field is most in demand |
| src/content/m6/specialisation-portfolio/zh.mdx:135 | 藏起了最有意思的部分 | 省略了最有价值的部分 |
| src/content/m6/specialisation-portfolio/en.mdx:135 | hides the most interesting part | omits the most informative part |
| src/content/m6/specialisation-portfolio/zh.mdx:157 | 能让你待在机器人旁边 | 能让你直接接触机器人 |
| src/content/m6/specialisation-portfolio/en.mdx:157 | put you next to the robots | give you hands-on access to robots |
| src/content/m6/specialisation-portfolio/zh.mdx:165 | 藏起失败；看起来像是很多次里挑出的那一次 | 只展示成功片段；一段只含成功片段的视频无法说明成功率 |
| src/content/m6/specialisation-portfolio/en.mdx:165 | Hiding failures; looks like the one good take out of many | Showing only successful takes; does not show the success rate |
| src/content/m6/vla-models/zh.mdx:9 | 让它像写字一样一个接一个地写出动作 | 让它以自回归方式逐个生成动作词元 |
| src/content/m6/vla-models/en.mdx:9 | write actions the way it writes words | generate action tokens autoregressively |
| src/content/m6/vla-models/zh.mdx:145 | 分词器根本无法表达 | 分词器无法表达 |
| src/content/m6/vla-models/en.mdx:145 | the tokeniser simply cannot express | the tokeniser cannot express |
| src/content/m6/vla-models/zh.mdx:172 | 长度与精度之间的旋钮 | 决定长度与精度之间的取舍 |
| src/content/m6/vla-models/en.mdx:172 | the knob between length and accuracy | sets the trade-off between length and accuracy |
| src/content/m6/vla-models/zh.mdx:201 | 只是把它挪了个地方 | 只是把工作转移到另一个环节 |
| src/content/m6/vla-models/en.mdx:201 | it moves it | it relocates it |
| src/content/m6/vla-models/zh.mdx:209 | 就像上面 6.2 度的误差那样 | 如上面 6.2 度的误差所示 |

False positives left unchanged: the quiz option "它像均值策略一样平均…" in `act-diffusion/zh.mdx:281` (literal comparison, and Quiz options are off limits), the literal similarity statements "形状类似 SO-101" / "shaped like teleoperation" in `vla-models`, and the code-block docstrings that contain "like a teleoperated dataset" / "like a person moving a leader arm" (`behaviour-cloning/en.mdx:28`, `vla-models/en.mdx:34,44`), since code blocks must not be edited.

## Section B: sections that stated a conclusion without the background or intermediate steps (closed in #70)

| file | heading | what is missing |
|---|---|---|
| src/content/m6/act-diffusion/zh.mdx, en.mdx | 动作分块：ACT 多了什么 / Action chunks: what ACT adds | The three benefits (fewer decisions, internal consistency, timing) are asserted; there is no step-by-step account of how errors compound over decisions, and temporal ensembling is named with "exponential weights" without giving the weights, the query rate or how overlapping chunks are combined. |
| src/content/m6/act-diffusion/zh.mdx, en.mdx | 扩散策略 / Diffusion policy | The exact denoiser is said to be a weighted average and to converge on one data point with 10 points, but neither the Gaussian weights nor the convergence argument is derived; both remain implicit in the code. |
| src/content/m6/behaviour-cloning/zh.mdx, en.mdx | 走廊任务 / The corridor task | The claim that a neural network trained with the squared loss behaves like 1-NN "where it matters here" is not justified; the reader is not shown the piecewise-constant/nearest-neighbour partition argument. |
| src/content/m6/behaviour-cloning/zh.mdx, en.mdx | 协变量偏移 / Covariate shift | "Each small error moves the policy further from its data … errors compound" is qualitative; there is no per-step recurrence linking actuator noise, the nearest recorded frame, the replayed action and the resulting drift. |
| src/content/m6/policy-evaluation/zh.mdx, en.mdx | 需要多少次试验 / How many trials | The table of 21/82/199/435 trials is given without the formula's intermediate terms (pooled proportion, z95, z80, squared difference) or a worked example; the formula exists only in `trials_needed` in the code block. |
| src/content/m6/policy-evaluation/zh.mdx, en.mdx | 失败分析 / Failure analysis | The mean failure step of 41.3 is described as "after the demonstrations stop", but the link to the 38–39-frame episode length and the 5 cm goal radius is not shown, so the number is not derived. |
| src/content/m6/policy-evaluation/zh.mdx, en.mdx | 同一个策略，不同的会话 / The same policy across sessions | The 4–9 spread over ten 10-trial sessions is presented as the reason a single session is insufficient, but no binomial standard deviation or expected spread calculation shows that this spread is consistent with a single underlying success rate. |
| src/content/m6/specialisation-portfolio/zh.mdx, en.mdx | 三层追问 / Three levels of follow-up questions | The answer states that 3061 frames is fine and a million is not, and that a k-d tree fixes it, without a complexity estimate or timing measurement for either the linear scan or the tree. |
| src/content/m6/specialisation-portfolio/zh.mdx, en.mdx | 三个作品集项目 / Three portfolio projects | The metric types are listed (success on a fixed start list, failure table), but the section does not say how to choose or size that start-position list or how many trials the metric needs; it only refers forward to lesson 4. |
| src/content/m6/vla-models/zh.mdx, en.mdx | 把动作写成词元：256 个区间 / Actions as tokens: 256 bins | The values 256 bins and 1st/99th percentiles are stated without explaining where 256 comes from (vocabulary/token budget) or the trade-off between percentile clipping and min/max normalisation. |
| src/content/m6/vla-models/zh.mdx, en.mdx | 用 DCT 压缩一个动作块 / Compressing a chunk with the DCT | "Smooth motion is mostly low frequencies" and the length/accuracy trade-off are given as results; there is no derivation of why the DCT concentrates smooth signals or how the rounding step depends on the scale. |
| src/content/m6/vla-models/zh.mdx, en.mdx | VLA 是什么 / What a VLA is | "The robot-specific learning is mostly in the third part and in the fine-tuning" is a conclusion with no ablation or evidence; the reader is not told how that split was established. |
