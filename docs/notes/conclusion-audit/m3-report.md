# Month 3 wording pass — report

Scope: `src/content/m3/*/zh.mdx` and `src/content/m3/*/en.mdx` (6 lessons × 2 languages).
Only prose was touched. Code blocks, `<SimOutput>`, `<CodeSource>`, `<Quiz>` answers/options,
links, component props and every number are unchanged; zh and en were edited in the same places.

Metaphors that *are* the physics (mass–spring–damper for PD, inverted pendulum, fin-ray geometry,
"elephant's foot", "watertight") were kept, but re-stated as models rather than as daily life.

## Section A — replacements

### cad-parametric

| file:line | old phrase | new wording (short) |
| --- | --- | --- |
| src/content/m3/cad-parametric/zh.mdx:9 | 装配和配合（mate）的行为像真实机器人关节 | 配合（mate）直接对应固定、转动、滑动这类真实关节 |
| src/content/m3/cad-parametric/en.mdx:9 | its assemblies and mates behave like real robot joints | its mates map directly onto fixed, revolute and slider joints |
| src/content/m3/cad-parametric/zh.mdx:32 | 毁掉你的一天…悄悄滑到一边，支架就变成了废件 | 自行移动…就滑到一边，支架尺寸随之改变 |
| src/content/m3/cad-parametric/en.mdx:32 | ruin your day…turning a bracket into a scrap part | move on its own…changing the size of the bracket |
| src/content/m3/cad-parametric/zh.mdx:51 | 几条实战习惯，都是吃过亏换来的： | 几条实战习惯： |
| src/content/m3/cad-parametric/en.mdx:51 | Practical habits, learned the hard way: | Practical habits that pay off: |
| src/content/m3/cad-parametric/zh.mdx:57 | 两条约束互相打架，工具变红或直接拒绝，你怎么改都不满意 | 两条约束对同一自由度提出矛盾要求，工具会标红或直接拒绝该约束 |
| src/content/m3/cad-parametric/en.mdx:57 | two constraints fight each other…nothing you do makes it happy | two constraints impose contradictory requirements on the same degree of freedom…refuses the constraint |
| src/content/m3/cad-parametric/zh.mdx:231 | 只留 STL，等于留下复印件、扔掉原件。 | 只留 STL，就等于丢掉了带参数的几何源文件，只剩下一份无法回溯的网格。 |
| src/content/m3/cad-parametric/en.mdx:231 | you have kept the photocopy and thrown away the document | you have thrown away the parametric source and are left with a mesh you cannot trace back to its dimensions |

### fdm-printing

| file:line | old phrase | new wording (short) |
| --- | --- | --- |
| src/content/m3/fdm-printing/zh.mdx:17 | 而不是折腾机器 | 而不是调机器 |
| src/content/m3/fdm-printing/en.mdx:17 | you would rather design than tinker | you would rather design than adjust the machine |
| src/content/m3/fdm-printing/zh.mdx:21 | 打印机是“爱好里的爱好” | 打印机需要占用空间、放在平稳的桌面上，还要偶尔维护 |
| src/content/m3/fdm-printing/en.mdx:21 | a printer is a hobby inside a hobby | a printer is a machine that takes up space, needs a stable table and occasional maintenance |
| src/content/m3/fdm-printing/zh.mdx:29 | ### 算一笔实在账 | ### 打印机的盈亏平衡 |
| src/content/m3/fdm-printing/en.mdx:29 | ### The honest economics | ### Breaking even on a printer |
| src/content/m3/fdm-printing/zh.mdx:40 | 盈亏平衡也可以老实算 | 盈亏平衡可以这样算 |
| src/content/m3/fdm-printing/en.mdx:40 | Do the break-even honestly | Do the break-even arithmetic |
| src/content/m3/fdm-printing/zh.mdx:57 | 会悄悄改变形状 | 会逐渐改变形状 |
| src/content/m3/fdm-printing/en.mdx:63 | rather than fight it at home | rather than handle moisture at home |

### gripper-fingers

| file:line | old phrase | new wording (short) |
| --- | --- | --- |
| src/content/m3/gripper-fingers/zh.mdx:3 | 不是靠“死命夹”抓住物体的 | 抓住物体靠的不是加大夹持力，而是**摩擦** |
| src/content/m3/gripper-fingers/en.mdx:3 | does not hold an object by clamping it "hard" | holds an object with **friction**, not by clamping harder |
| src/content/m3/gripper-fingers/zh.mdx:5 | 物体“反抗”出来的额外力 m × a | 物体的惯性产生一个大小为 m × a 的反向力 |
| src/content/m3/gripper-fingers/en.mdx:5 | the object resists with an extra force m × a | the object's inertia produces an opposing force m × a |
| src/content/m3/gripper-fingers/zh.mdx:116 | 角度越小越悲观，而悲观的情况才是会让物体掉下来的情况 | 角度越小算出的摩擦系数越小，而摩擦系数越小，物体越容易滑脱 |
| src/content/m3/gripper-fingers/en.mdx:116 | the low angle is the pessimistic one… | the lowest angle gives the lowest friction coefficient…the one that lets the object slip |
| src/content/m3/gripper-fingers/zh.mdx:124 | 这两个接触点就像一对楔子 | 两个点接触构成一个楔形：每个接触点的法向力都有一段指向物体中线的分量 |
| src/content/m3/gripper-fingers/en.mdx:124 | those two contact points act like a wedge | two point contacts form a wedge: the normal force at each contact has a component along the object's centre line |
| src/content/m3/gripper-fingers/zh.mdx:126 | 整根手指像一只正在合拢的手那样**卷住**物体 | 整个三角截面随之改变形状，两片侧壁的尖端包住物体 |
| src/content/m3/gripper-fingers/en.mdx:126 | the whole finger curls around the object like a closing hand | the triangular section changes shape so that the two flanks wrap around the object |
| src/content/m3/gripper-fingers/zh.mdx:252 | 别让从臂的夹爪白白憋着劲 | 否则从臂的夹爪会在没有负载时仍然顶着位置环的目标持续出力 |
| src/content/m3/gripper-fingers/en.mdx:252 | the follower's gripper is not straining for nothing | the follower's gripper keeps driving against its position-loop target with nothing to hold |
| src/content/m3/gripper-fingers/zh.mdx:258 | 谁都会把套件拧起来，而一个能用的自定义夹爪是你自己的作品 | 照说明装好套件只需要动手，而一个能用的自定义夹爪是你自己的设计 |
| src/content/m3/gripper-fingers/en.mdx:258 | Anyone can bolt together a kit; a working custom gripper is your own work | Bolting a kit together needs only the instructions; a working custom gripper is your own design |
| src/content/m3/gripper-fingers/zh.mdx:282 | 最后一步是大家最爱跳过的 | 最后一步最容易被跳过 |
| src/content/m3/gripper-fingers/en.mdx:282 | The last step is the one people skip | The last step is the easiest to skip |

### pid-control

| file:line | old phrase | new wording (short) |
| --- | --- | --- |
| src/content/m3/pid-control/zh.mdx:1 | 两种失败长得一样 | 两种失败的根源相同 |
| src/content/m3/pid-control/en.mdx:1 | Both failures have the same shape | Both failures have the same root cause |
| src/content/m3/pid-control/zh.mdx:17 | 用大白话说：P 是弹簧，D 是减震器，I 是那只把活干完的、有耐心的手 | 在质量–弹簧–阻尼模型里，P 是弹簧（力与位移成正比），D 是阻尼器（力与速度成正比），I 是与误差累积量成正比的恒定偏置力 |
| src/content/m3/pid-control/en.mdx:17 | In plain terms: P is the spring, D is the shock absorber, I is the patient hand that finishes the job | In the mass–spring–damper model, P is the spring (force proportional to displacement), D is the damper (force proportional to velocity), and I is a constant bias torque proportional to the accumulated error |
| src/content/m3/pid-control/zh.mdx:115 | 弹簧把它拉回来之前 | 比例项把它拉回来之前 |
| src/content/m3/pid-control/en.mdx:115 | before the spring pulls it back | before the proportional term pulls it back |
| src/content/m3/pid-control/zh.mdx:115 | 同一条弹簧拉得更狠 | 同一条比例曲线推得更狠 |
| src/content/m3/pid-control/en.mdx:115 | the same spring that pulls harder | the same proportional term that pushes harder |
| src/content/m3/pid-control/zh.mdx:125 | 它就会存下一大团“推不出去”的指令 | 积分项就会累积出一个远大于电机实际输出力矩的指令 |
| src/content/m3/pid-control/en.mdx:125 | it stores a large push that has nowhere to go | it accumulates a command far larger than the torque the motor ever delivered |
| src/content/m3/pid-control/en.mdx:39 | PWM values to paste into firmware | PWM values to copy into firmware |
| src/content/m3/pid-control/zh.mdx:141 | 调参不是寻找魔法数字 | 调参不是凭经验试数字 |
| src/content/m3/pid-control/en.mdx:139 | Tuning is not a search for magic numbers | Tuning is not guesswork |
| src/content/m3/pid-control/zh.mdx:143 | 最后都会撞到某个极限 | 输出都会一直增长到饱和 |
| src/content/m3/pid-control/en.mdx:141 | will slam into a limit no matter how small the gain | drives the output to its limit, whatever the gain |
| src/content/m3/pid-control/zh.mdx:149 | 延迟相当于一个让系统不稳定的推力 | 控制指令作用在已经变化过的状态上…回路的相位裕度因此减小 |
| src/content/m3/pid-control/en.mdx:147 | delay acts like a destabilising push | the command is applied to a state that has already moved on, so the loop loses phase margin |

### so101-arm

| file:line | old phrase | new wording (short) |
| --- | --- | --- |
| src/content/m3/so101-arm/zh.mdx:5 | 不是什么演示花招 | 它是录制演示数据的手段，不是演示花招 |
| src/content/m3/so101-arm/en.mdx:5 | it is not a demo trick | it is how demonstrations are recorded, not a demo trick |
| src/content/m3/so101-arm/zh.mdx:5 | 把校准做诚实 | 把校准做准确 |
| src/content/m3/so101-arm/en.mdx:5 | an honest calibration | a careful calibration |
| src/content/m3/so101-arm/zh.mdx:22 | 组装时脑子里装着这张图 | 组装时记住这张图 |
| src/content/m3/so101-arm/en.mdx:22 | Keep that picture in your head during assembly | Knowing this while you assemble |
| src/content/m3/so101-arm/zh.mdx:39 | MuJoCo 是诚实的选择 | MuJoCo 是合适的选择 |
| src/content/m3/so101-arm/en.mdx:39 | MuJoCo is the honest choice | MuJoCo is the practical choice |
| src/content/m3/so101-arm/zh.mdx:50 | 仿真不是安慰奖 | 仿真不是降级方案，它跑的是同一套软件 |
| src/content/m3/so101-arm/en.mdx:50 | a simulator is not a consolation prize | a simulator is not a fallback |
| src/content/m3/so101-arm/zh.mdx:58 | 它像对讲机，不像电话：一方说话时另一方只能听。每个包里带 ID，相当于点名 | 发送时线路由发送端驱动，接收端同时读不出数据，所以控制器发完一帧必须转为接收…每个包里带 ID，用来在总线上寻址对应的那一个舵机 |
| src/content/m3/so101-arm/en.mdx:58 | It is a walkie-talkie, not a telephone. The ID in every packet is roll call | while the controller drives the line to send, the receiving side cannot read data…The ID in every packet addresses the one servo it is meant for |
| src/content/m3/so101-arm/zh.mdx:71 | 它是一台按“给人扳”来选减速比的臂 | 它的减速比是按人手拖动的操作方式选的 |
| src/content/m3/so101-arm/en.mdx:71 | it is an arm geared for being moved by a human | its ratios are chosen for an arm moved by hand |
| src/content/m3/so101-arm/zh.mdx:342 | 否则你会纳闷它为什么像另一台机器人 | 否则会载入另一份校准数据，关节零位与当前装配对不上 |
| src/content/m3/so101-arm/en.mdx:342 | or you will wonder why it behaves like a different robot | otherwise a different calibration file is loaded and the joint zero offsets no longer match the assembly |

### transmissions

| file:line | old phrase | new wording (short) |
| --- | --- | --- |
| src/content/m3/transmissions/zh.mdx:182 | 皮带会拉伸（关节有弹性） | 皮带会拉伸（关节有柔性） |
| src/content/m3/transmissions/en.mdx:182 | The belt stretches (a springy joint) | The belt stretches (a compliant joint) |
| src/content/m3/transmissions/zh.mdx:187 | 皮带本身是一根弹簧 | 皮带是传动链上的弹性元件，受力时储存扭矩、卸载时释放 |
| src/content/m3/transmissions/en.mdx:187 | a belt is a spring | the belt is the elastic element in the drive train, storing torque while it is loaded and releasing it when the load changes |
| src/content/m3/transmissions/zh.mdx:310 | 通常是它把只有一个轴承的关节搞坏 | 通常是它先把只有一个轴承的关节压坏 |
| src/content/m3/transmissions/en.mdx:310 | it is usually the one that kills a joint with only one bearing | it is usually what breaks a joint that has only one bearing |
| src/content/m3/transmissions/zh.mdx:314 | 预紧是受到控制的小小一挤，不是死压 | 滚珠与滚道之间的接触力过大会抬高摩擦和温升…预紧量要按轴承的额定值控制 |
| src/content/m3/transmissions/en.mdx:314 | preload is a small, controlled squeeze, not a crush | a large contact force…raises friction and temperature…the preload has to be sized against the bearing's rating |
| src/content/m3/transmissions/zh.mdx:322 | 抗折腾得多 | 金属齿的强度和耐磨性更高，同样载荷下失效得更少 |
| src/content/m3/transmissions/en.mdx:322 | survive far more abuse | whose strength and wear resistance are higher, so they fail far less often under the same load |
| src/content/m3/transmissions/zh.mdx:359 | 是控制器站上去的那几块机械地基 | 决定了控制环能被整定到什么程度 |
| src/content/m3/transmissions/en.mdx:359 | are the mechanical foundations the controller stands on | set the limits on how the control loop can be tuned |

## Section B — sections that state a result without the hardware background or the derivation

Listed only; rows marked **Fixed** were addressed later in the PR named.

| file | heading | what is missing |
| --- | --- | --- |
| src/content/m3/so101-arm/zh.mdx, en.mdx | ## 总线舵机与数据包 / ## Bus servos and packets | The leader/follower gear-ratio table (1/191, 1/345, 1/147) is given as fact: nothing says which BOM part each number comes from, how to read the ratio off a purchased STS3215, or how to confirm the shoulder_lift really is the joint that has to hold the arm. Same for "4096 steps is the encoder's resolution, not the arm's accuracy" — the error sources after the encoder (gear backlash, horn mounting, printed-part flex) are listed but never sized. |
| src/content/m3/so101-arm/zh.mdx, en.mdx | ## 供电 / ## Power | The table gives input ranges and stall torques with citations, but not how to identify which variant a servo in your hand is (C001 vs C018 on the label), nor where "12 V, at least 5 A" comes from — no current budget from stall torque and the number of joints on one supply. |
| src/content/m3/so101-arm/zh.mdx, en.mdx | ### 组装要点 / ### Assembly notes | A bullet list of operations with no hardware background: what a servo horn is, why most joints take two horns and the wrist roll only one, what M3×6 vs M2×6 is sized for (horn clamping vs printed boss), and what the horns do to define the joint's zero against the encoder. |
| src/content/m3/so101-arm/zh.mdx, en.mdx | ## 选你的路线 / ## Choose your route | The eight-row price table is a conclusion. Only the Seeed route is derived; the other rows' totals are not shown from the BOM (part counts, filament mass, tools), and "what you lose" is asserted per route without saying which LeRobot commands each route actually exercises. |
| src/content/m3/cad-parametric/zh.mdx, en.mdx | ## 装配与配合 / ## Assemblies and mates | The mate table gives "DOF left" and "real joint" as results. The section never says which constraints a revolute or slider mate applies (three coincident planes, one coincident axis, one angle limit), and never contrasts the ideal mate with a real servo output (clearance, travel limit, friction). The motion-study paragraph also assumes collision checking without saying which DOF the study drives. |
| src/content/m3/cad-parametric/zh.mdx, en.mdx | ## STEP、STL 与 3MF / ## STEP, STL and 3MF | What each format can and cannot do is asserted. The internal representations are never shown: STEP's B-rep entities and its unit declaration, STL's facet list, 3MF's XML records for units/colours/print settings. The reader cannot connect "STEP keeps exact surfaces" to anything visible in a file. |
| src/content/m3/transmissions/zh.mdx, en.mdx | ## 轴承与预紧 / ## Bearings and preload | **Fixed (#54).** The two-bearings argument ("the further apart, the smaller those forces") is given without the derivation (M = F·d, so F = M/d) or any example numbers. Preload's effect on shaft stiffness is asserted; no axial-stiffness figure or measurement is proposed. |
| src/content/m3/transmissions/zh.mdx, en.mdx | ### 反向拖动 / ### Backdriving | **Fixed (#54).** Friction ×n is stated with no reason; the inertia ×n² result is only half-explained by "the rotor spins n times faster" without the kinetic-energy argument or the efficiency factor that makes the felt friction larger than n. |
| src/content/m3/transmissions/zh.mdx, en.mdx | ### 为什么舵机齿轮最先坏 / ### Why servo gears fail first | **Fixed (#54).** The load path is described qualitatively (all output torque on small plastic teeth), but the section gives no numbers for where the load concentrates in a real gearbox and no way to check the claim on a servo you own (e.g. measuring backlash growth or tooth wear). |
| src/content/m3/pid-control/zh.mdx, en.mdx | ## 一个关节，四种控制器 / ## One joint, four controllers | The model constants (J = 0.004 kg·m², viscous friction, 0.4 N·m gravity torque, 1 N·m motor limit, 200 Hz) are handed to the reader as facts. Nothing shows how each would be obtained for a real joint: measuring reflected inertia, computing the gravity torque from arm mass and length, reading the stall torque from the datasheet, or choosing the loop rate from the mechanism's bandwidth. |
| src/content/m3/pid-control/zh.mdx, en.mdx | ## 串级回路 / ## Cascade loops | The outer loop rate (25 Hz = every 8th tick) and the ±3° lean clamp are given as rules. The section never derives the rate from the speed-measurement resolution (it is only mentioned later as an observed effect), and never connects the 3° clamp to the wheel-speed gain or to what tilt actually stops the robot from falling over (the 45° limit appears only inside the simulator code). |
| src/content/m3/gripper-fingers/zh.mdx, en.mdx | ## 鳍条效应 / ## The fin-ray idea | The three parameters (flank thickness, rib count and thickness, rib tilt) are listed as rules of thumb. The mechanics behind each is missing: how flank bending stiffness and the rib moment arm set the effective stiffness and the curl direction, and how a reader could check the prediction on their own print (e.g. force–deflection measurement). |
| src/content/m3/gripper-fingers/zh.mdx, en.mdx | ## 打印 TPU / ## Printing TPU | The settings list is given without the hardware background: only the Bowden buckling case is explained, and even that is asserted rather than tied to the extrusion force and the drive-gear grip available. Nothing explains which failure mode each setting prevents or what the direct-drive advantage actually is in force terms. |
| src/content/m3/fdm-printing/zh.mdx, en.mdx | ## 选耗材 / ## Pick the filament | **Fixed (#54).** The material properties are stated as conclusions: PLA softening at 55–60 °C, PETG creep and layer adhesion, nylon moisture uptake, ASA UV resistance. No source is given, and no mechanism (glass transition, moisture absorption rate, layer-bond area) is explained, so the reader cannot reason to a different material themselves. |
| src/content/m3/fdm-printing/zh.mdx, en.mdx | ## 面向 FDM 设计 / ## Design for FDM | **Fixed (#54).** The 45° overhang figure and the "two extrusion widths" minimum are given as rules; the section says in passing that cooling, nozzle size and layer height change them but never shows how, and never explains how a feature thinner than two extrusion widths fails inside the slicer (skipped path vs. a ragged single bead). |
