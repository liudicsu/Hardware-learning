import type { L10n } from "./types";

/**
 * Course glossary. One entry per term; `lesson` is the slug of the lesson where the term is used or explained
 * (linked from the popover and the /glossary page as the related lesson). `firstExplained: true` marks entries whose
 * `lesson` has been checked to be the lesson that first explains the term; their popover reads "First explained in".
 * zh and en names here are the canonical translations used across the site.
 * Definitions are short, precise and use the course's own hardware (SO-101, Uno, ESP32-S3, m4bot).
 */
export interface GlossaryEntry {
  id: string;
  term: L10n;
  def: L10n;
  lesson: string;
  firstExplained?: boolean;
}

export const glossary: GlossaryEntry[] = [
  {
    id: "gnd",
    term: { zh: "地（GND）", en: "ground (GND)" },
    def: {
      zh: "电路中约定为 0 V 的参考节点，所有电压都相对它测量。Uno 与电机驱动板必须共地，否则信号电平没有共同参考。",
      en: "The node defined as 0 V; every voltage in the circuit is measured relative to it. An Uno and a motor driver must share GND, otherwise their logic levels have no common reference.",
    },
    lesson: "ohms-law",
  },
  {
    id: "voltage",
    term: { zh: "电压", en: "voltage" },
    def: {
      zh: "两点之间的电势差，单位伏特（V）；电压永远是两点之间的差值，不存在孤立的“某点电压”。Arduino Uno 的逻辑高电平约为 5 V，ESP32-S3 约为 3.3 V。",
      en: "The electric potential difference between two points, in volts (V); voltage is always a difference between two points, never an absolute value at one point. Arduino Uno logic HIGH is about 5 V and ESP32-S3 logic HIGH about 3.3 V.",
    },
    lesson: "ohms-law",
  },
  {
    id: "current",
    term: { zh: "电流", en: "current" },
    def: {
      zh: "电荷通过某一点的速率，单位安培（A），1 A 等于每秒 1 库仑。小电路常用毫安（mA），而电机堵转电流可以达到数安培。",
      en: "The rate at which charge passes a point, in amperes (A), with 1 A equal to 1 coulomb per second. Small circuits use milliamps (mA), while a stalled motor can draw several amps.",
    },
    lesson: "ohms-law",
  },
  {
    id: "resistance",
    term: { zh: "电阻", en: "resistance" },
    def: {
      zh: "路径对电流的阻碍程度，单位欧姆（Ω）；1 Ω 上施加 1 V 时流过 1 A。电阻把电能转成热，因此还要检查它的额定功率。",
      en: "How strongly a path opposes current, in ohms (Ω); 1 V across 1 Ω drives 1 A. A resistor turns electrical energy into heat, so its power rating matters as well as its value.",
    },
    lesson: "ohms-law",
  },
  {
    id: "ohms-law",
    term: { zh: "欧姆定律", en: "Ohm's law" },
    def: {
      zh: "电压、电流与电阻的关系：V = I × R，也可写成 I = V / R 或 R = V / I。例如 5 V 加在 220 Ω 上得到 5 / 220 ≈ 22.7 mA。",
      en: "The relation between voltage, current and resistance: V = I × R, also written I = V / R or R = V / I. For example, 5 V across 220 Ω gives 5 / 220 ≈ 22.7 mA.",
    },
    lesson: "ohms-law",
  },
  {
    id: "power",
    term: { zh: "功率", en: "power" },
    def: {
      zh: "能量传递或耗散的速率，单位瓦特（W），在电阻中 P = V × I = I² × R = V² / R。5 V 加在 100 Ω 上耗散 0.25 W，正好等于常见 1/4 W 电阻的额定值，实际应留出余量。",
      en: "The rate at which energy is transferred or dissipated, in watts (W); in a resistor P = V × I = I² × R = V² / R. 5 V across 100 Ω dissipates 0.25 W, exactly the rating of a common 1/4 W resistor, so real designs need margin.",
    },
    lesson: "ohms-law",
  },
  {
    id: "voltage-divider",
    term: { zh: "分压器", en: "voltage divider" },
    def: {
      zh: "两个电阻串联、从中间取输出的电路，Vout = Vin × R2 / (R1 + R2)。5 V 经 10 kΩ 与 4.7 kΩ 分压得到约 1.6 V；它只能驱动高阻抗输入，不能当电源。",
      en: "Two resistors in series with the output taken between them: Vout = Vin × R2 / (R1 + R2). A 5 V input with 10 kΩ over 4.7 kΩ gives about 1.6 V; it can feed a high-impedance input but is not a power supply.",
    },
    lesson: "ohms-law",
  },
  {
    id: "charge-coulomb",
    term: { zh: "电荷（库仑，C）", en: "charge (coulomb, C)" },
    def: {
      zh: "电荷量以库仑（C）计，1 C 是 1 A 电流持续 1 s 所通过的电荷量。电容储存的就是电荷，100 nF 去耦电容在芯片瞬态取流时就近释放这部分电荷。",
      en: "Charge is measured in coulombs (C); 1 C is the charge carried by 1 A for 1 s. A capacitor stores charge, and a 100 nF decoupling capacitor releases it locally during a chip's current transient.",
    },
    lesson: "ohms-law",
  },
  {
    id: "adc",
    term: { zh: "模数转换器（ADC）", en: "analog-to-digital converter (ADC)" },
    def: {
      zh: "把连续电压转换成离散数字量的外设。Uno 的 ADC 是 10 位，在 0–5 V 范围内输出 0–1023，一个最低有效位约为 5 V / 1024 ≈ 4.9 mV。",
      en: "A peripheral that converts a continuous voltage into a discrete number. The Uno's ADC is 10-bit, producing 0–1023 over 0–5 V, so one least-significant bit is about 5 V / 1024 ≈ 4.9 mV.",
    },
    lesson: "arduino-io",
    firstExplained: true,
  },
  {
    id: "internal-resistance",
    term: { zh: "内阻", en: "internal resistance" },
    def: {
      zh: "电源内部与理想电压源串联的电阻，负载电流越大，它吃掉的电压越多。堵转电流 2 A 流过电池、导线与接插件合计 0.5 Ω 时，供电轨会瞬间跌落 1 V。",
      en: "The resistance inside a source, in series with its ideal voltage source; the more current it delivers, the more voltage it drops. A 2 A stall current through 0.5 Ω of battery, wire and connector resistance drops the rail by 1 V.",
    },
    lesson: "ohms-law",
  },
  {
    id: "capacitor",
    term: { zh: "电容", en: "capacitor" },
    def: {
      zh: "由两片导体和中间的介质构成、储存电荷的元件；它抵抗电压突变，阻直流、通变化。本课 Falstad 示例用 180 Ω 与 33 µF，时间常数 τ = 180 Ω × 33 µF ≈ 5.9 ms。",
      en: "A component that stores charge on two conductors separated by a dielectric; it resists sudden voltage changes, blocks DC and passes changes. The lesson's Falstad example uses 180 Ω with 33 µF, giving τ = 180 Ω × 33 µF ≈ 5.9 ms.",
    },
    lesson: "components",
  },
  {
    id: "inductor",
    term: { zh: "电感", en: "inductor" },
    def: {
      zh: "把能量储存在磁场中的元件，它抵抗电流突变，关系为 V = L × di/dt。电机绕组本质上就是电感，断电瞬间会产生远高于电源电压的反冲尖峰。",
      en: "A component that stores energy in a magnetic field and resists changes in current according to V = L × di/dt. A motor winding is an inductor, and interrupting its current produces a kickback spike far above the supply voltage.",
    },
    lesson: "components",
    firstExplained: true,
  },
  {
    id: "diode",
    term: { zh: "二极管", en: "diode" },
    def: {
      zh: "只允许电流从阳极流向阴极的元件，符号中横线一侧是阴极。硅二极管正向导通时约有 0.6–0.7 V 压降，反向偏置时截止。",
      en: "A component that conducts current only from anode to cathode; the bar in its symbol marks the cathode. A silicon diode drops about 0.6–0.7 V when forward-biased and blocks current when reverse-biased.",
    },
    lesson: "components",
  },
  {
    id: "led-forward-voltage",
    term: { zh: "LED 正向压降（Vf）", en: "LED forward voltage (Vf)" },
    def: {
      zh: "LED 开始明显导通时两端的正向电压，红色约为 1.8–2.2 V，绿、蓝、白约为 2.8–3.3 V。LED 是电流驱动器件，必须串联限流电阻，例如 5 V 点亮 2 V 红色 LED、目标 10 mA 时取 330 Ω。",
      en: "The forward voltage across an LED when it conducts appreciably: about 1.8–2.2 V for red and 2.8–3.3 V for green, blue or white. An LED is current-driven and needs a series resistor; a 2 V red LED on 5 V at 10 mA uses 330 Ω.",
    },
    lesson: "components",
  },
  {
    id: "transistor-saturation",
    term: { zh: "晶体管饱和", en: "transistor saturation" },
    def: {
      zh: "晶体管作为开关时完全导通的工作区，此时集电极—发射极压降很小，负载几乎拿到全部电源电压。基极电流要按 β 计算后再过驱动 5–10 倍，否则晶体管停在放大区并严重发热。",
      en: "The fully on region of a transistor used as a switch, where the collector–emitter drop is small and the load receives almost the whole supply. Base current is set from β and then overdriven by 5–10×; otherwise the transistor stays in its linear region and heats badly.",
    },
    lesson: "components",
  },
  {
    id: "beta-hfe",
    term: { zh: "电流放大倍数（β / hFE）", en: "current gain (β / hFE)" },
    def: {
      zh: "双极型晶体管集电极电流与基极电流之比，β = Ic / Ib。β ≈ 100、Ic = 20 mA 时最小基极电流为 0.2 mA，开关用途再取 10 倍过驱动。",
      en: "The ratio of collector current to base current in a bipolar transistor, β = Ic / Ib. With β ≈ 100 and Ic = 20 mA the minimum base current is 0.2 mA, and a switch design overdrives it by 10×.",
    },
    lesson: "components",
  },
  {
    id: "back-emf",
    term: { zh: "反电动势（back-EMF）", en: "back-electromotive force (back-EMF)" },
    def: {
      zh: "电机转动时作为发电机产生的、与供电方向相反的电压。正常旋转时它抵消大部分外加电压，堵转时降为零，因此堵转电流远大于运行电流。",
      en: "The voltage a spinning motor generates as a generator, opposing the supply. It cancels most of the applied voltage while the motor turns, falls to zero at stall, and that is why stall current is much larger than running current.",
    },
    lesson: "components",
    firstExplained: true,
  },
  {
    id: "ldo",
    term: { zh: "低压差线性稳压器（LDO）", en: "low-dropout linear regulator (LDO)" },
    def: {
      zh: "输入电压只比输出电压高很小压差时仍能稳压的线性稳压器，输出干净但多余电压会变成热。机器人里常用它给单片机和逻辑电路单独供电，避免电机浪涌拉塌逻辑电源。",
      en: "A linear regulator that still regulates when the input is only slightly above the output; its output is clean but the excess voltage becomes heat. Robots use one to give the microcontroller and logic their own rail so motor surges cannot collapse it.",
    },
    lesson: "components",
  },
  {
    id: "pwm",
    term: { zh: "脉宽调制（PWM）", en: "pulse-width modulation (PWM)" },
    def: {
      zh: "引脚在高低电平之间快速切换，用占空比控制平均电压；Uno 的 PWM 引脚为 3、5、6、9、10、11，频率约 490 Hz 或 980 Hz，analogWrite 取 0–255。负载响应比周期慢时，看到的就是平均电压。",
      en: "A pin switching rapidly between high and low, with duty cycle setting the average voltage; Uno PWM pins are 3, 5, 6, 9, 10 and 11 at about 490 Hz or 980 Hz, with analogWrite taking 0–255. A load slower than the period responds to the average.",
    },
    lesson: "arduino-io",
    firstExplained: true,
  },
  {
    id: "decoupling-capacitor",
    term: { zh: "去耦电容", en: "decoupling capacitor" },
    def: {
      zh: "跨接在芯片电源与地之间、尽量贴近电源引脚的小电容，通常为 100 nF 陶瓷电容。它在芯片瞬间取流时就近供给电荷，防止供电轨下陷和逻辑误动作。",
      en: "A small capacitor, usually 100 nF ceramic, connected between a chip's supply pin and ground and placed as close as possible. It supplies charge locally during current transients, preventing rail sag and logic errors.",
    },
    lesson: "components",
  },
  {
    id: "esr",
    term: { zh: "等效串联电阻（ESR）", en: "equivalent series resistance (ESR)" },
    def: {
      zh: "电容内部与电容串联的寄生电阻，纹波电流在它上面产生压降和热量。陶瓷去耦电容的 ESR 很低，而电机驱动器旁的大容量电解电容 ESR 较高，二者不能互相替代。",
      en: "The parasitic resistance in series with a capacitor; ripple current through it causes voltage drop and heating. Ceramic decoupling capacitors have very low ESR, while the bulk electrolytic near a motor driver has higher ESR, so the two are not interchangeable.",
    },
    lesson: "components",
    firstExplained: true,
  },
  {
    id: "pull-up-pull-down",
    term: { zh: "上拉/下拉电阻", en: "pull-up/pull-down resistor" },
    def: {
      zh: "把输入引脚在无驱动时钉在已知电平的电阻，上拉接 VCC，下拉接 GND；常用 10 kΩ。ATmega328P 内部上拉约为 20–50 kΩ，INPUT_PULLUP 启用后按键应接 GND，按下读 LOW。",
      en: "A resistor that holds an input at a known level when nothing drives it: pull-up to VCC, pull-down to GND, commonly 10 kΩ. The ATmega328P's internal pull-up is about 20–50 kΩ; with INPUT_PULLUP the button goes to GND and reads LOW when pressed.",
    },
    lesson: "components",
    firstExplained: true,
  },
  {
    id: "rc-time-constant",
    term: { zh: "RC 时间常数（τ = RC）", en: "RC time constant (τ = RC)" },
    def: {
      zh: "电阻与电容乘积，描述 RC 电路充放电速度；从 0 开始充电时，1τ 达到约 63%，5τ 达到约 99%。10 kΩ 与 100 µF 给出 τ = 1 s。",
      en: "The product of resistance and capacitance, describing how fast an RC circuit charges or discharges; charging from zero reaches about 63% at 1τ and about 99% at 5τ. 10 kΩ with 100 µF gives τ = 1 s.",
    },
    lesson: "components",
  },
  {
    id: "input-impedance",
    term: { zh: "输入阻抗", en: "input impedance" },
    def: {
      zh: "测量仪器输入端对被测电路呈现的阻抗；电压档的输入阻抗极高，所以并联测量时几乎不取电流、不改变电路。电流档则相反，内部是低阻分流器，必须串联。",
      en: "The impedance an instrument presents at its input; a voltmeter's input impedance is very high, so measuring in parallel draws almost no current and barely disturbs the circuit. A current range is the opposite, using a low-resistance shunt and requiring a series connection.",
    },
    lesson: "bench-multimeter",
    firstExplained: true,
  },
  {
    id: "cat-rating",
    term: { zh: "安全类别（CAT）", en: "measurement category (CAT)" },
    def: {
      zh: "万用表按测量位置瞬态过压能力划分的安全等级（CAT II、CAT III、CAT IV 等），与量程不是一回事。测量市电或配电线路时必须选用对应类别的表，并确认表笔和保险丝也满足该等级。",
      en: "A safety classification of a multimeter by the transient overvoltage at its measurement location (CAT II, CAT III, CAT IV and so on), separate from its range. Measuring mains or distribution circuits requires the matching category, including probes and fuses rated for it.",
    },
    lesson: "bench-multimeter",
    firstExplained: true,
  },
  {
    id: "rms",
    term: { zh: "均方根值（RMS）", en: "root mean square (RMS)" },
    def: {
      zh: "交流量在一个周期内的均方根值，代表产生相同热效应的等效直流值。正弦波的 RMS 等于峰值除以 √2；真有效值（True RMS）万用表的交流档显示的就是它，平均值响应型表只对正弦波读数正确。",
      en: "The root-mean-square value of an alternating quantity over one cycle, equal to the DC value that produces the same heating. For a sinusoid, RMS is the peak divided by √2; a true-RMS meter's AC range displays it, while an average-responding meter is correct only for sine waves.",
    },
    lesson: "bench-multimeter",
  },
  {
    id: "diode-test",
    term: { zh: "二极管测试档", en: "diode test mode" },
    def: {
      zh: "万用表输出微小测试电流并显示二极管正向压降的档位，可用于判断极性和好坏。硅二极管正常时约为 0.6–0.7 V，反向应显示溢出或开路。",
      en: "A meter mode that drives a small test current through a diode and displays its forward drop, used to check polarity and condition. A good silicon diode reads about 0.6–0.7 V one way and over-range or open the other way.",
    },
    lesson: "bench-multimeter",
  },
  {
    id: "continuity",
    term: { zh: "通断档", en: "continuity mode" },
    def: {
      zh: "在断电状态下检测低阻通路并发出蜂鸣的档位，多数表在几十欧以下鸣叫。它用于找断线、查焊点、确认网络连接，以及上电前检查电源与地是否短路。",
      en: "A powered-off mode that beeps when it detects a low-resistance path; most meters beep below a few tens of ohms. It finds broken wires, checks solder joints and nets, and verifies that supply and ground are not shorted before power-up.",
    },
    lesson: "bench-multimeter",
  },
  {
    id: "variable-type",
    term: { zh: "变量与类型", en: "variable and type" },
    def: {
      zh: "变量是绑定到值的名字，类型决定这个值能参与哪些运算；Python 常见类型有 int、float、str、bool。类型标注只用于文档和编辑器提示，运行时不会强制检查。",
      en: "A variable is a name bound to a value, and its type determines which operations make sense; common Python types are int, float, str and bool. Type hints document intent and help the editor but are not enforced at runtime.",
    },
    lesson: "python-terminal",
  },
  {
    id: "function",
    term: { zh: "函数", en: "function" },
    def: {
      zh: "有名字、可重复调用的代码块，接收参数并返回结果。ohm.py 中的 current(volts, ohms) 接收两个浮点数并返回一个浮点数，计算放在函数里、打印留在程序边缘。",
      en: "A named, reusable block of code that takes arguments and returns a result. In ohm.py, current(volts, ohms) takes two floats and returns one; calculation stays inside the function and printing happens at the edge.",
    },
    lesson: "python-terminal",
  },
  {
    id: "venv",
    term: { zh: "虚拟环境（venv）", en: "virtual environment (venv)" },
    def: {
      zh: "为单个项目隔离 Python 解释器链接和第三方包的私有目录。激活后 shell 里的 python 与 pip 指向这个副本，不同项目的依赖不会互相破坏，且 .venv 不应提交到 Git。",
      en: "A private directory holding a project's own Python link and packages. Once activated, python and pip in that shell resolve inside it, so projects cannot break each other's dependencies; .venv should not be committed to Git.",
    },
    lesson: "python-terminal",
  },
  {
    id: "pip",
    term: { zh: "pip", en: "pip" },
    def: {
      zh: "Python 的包安装工具；用 python -m pip 可确保调用的是当前解释器对应的 pip。pip freeze > requirements.txt 固定依赖，pip install -r requirements.txt 可在新环境中重建。",
      en: "Python's package installer; python -m pip ensures pip belongs to the interpreter you are running. pip freeze > requirements.txt pins dependencies and pip install -r requirements.txt rebuilds them in a new environment.",
    },
    lesson: "python-terminal",
  },
  {
    id: "path",
    term: { zh: "PATH（可执行文件搜索路径）", en: "PATH (executable search path)" },
    def: {
      zh: "shell 按顺序查找命令的可执行目录列表；激活 venv 会把环境的 bin 目录放到前面，因此 python 和 pip 解析到项目副本。ROS 2 的 setup.bash 也是把命令加入 PATH。",
      en: "The ordered list of directories the shell searches for commands; activating a venv puts the environment's bin directory first, so python and pip resolve inside the project. Sourcing a ROS 2 setup.bash likewise adds its commands to PATH.",
    },
    lesson: "python-terminal",
  },
  {
    id: "argparse",
    term: { zh: "argparse", en: "argparse" },
    def: {
      zh: "Python 标准库的命令行参数解析模块，可定义子命令、参数类型和必填项。ohm.py 用 current 与 divider 两个子命令，type=float、required=True 会在缺参数时给出用法提示。",
      en: "The Python standard-library module for parsing command-line arguments, including subcommands, types and required flags. ohm.py defines current and divider subcommands, and type=float with required=True produces a usage error when an argument is missing.",
    },
    lesson: "python-terminal",
  },
  {
    id: "json",
    term: { zh: "JSON", en: "JSON" },
    def: {
      zh: "一种由对象、数组、数字、字符串、布尔值和 null 组成的文本数据格式，几乎直接对应 Python 的字典和列表。测量日志用一个字典记录一次测量、再用字典列表保存全部记录。",
      en: "A text data format built from objects, arrays, numbers, strings, booleans and null, mapping almost directly onto Python dicts and lists. The measurement log stores one dict per measurement and a list of those dicts.",
    },
    lesson: "python-terminal",
  },
  {
    id: "commit",
    term: { zh: "提交（commit）", en: "commit" },
    def: {
      zh: "项目在某一刻的完整快照，附带说明、作者、时间和指向上一个提交的父指针。git commit 只记录暂存区里的内容，改了但未暂存的文件不会进入快照。",
      en: "A complete snapshot of the project at one moment, with a message, author, timestamp and a parent pointer. git commit records only what is staged; edits that were not added stay out of the snapshot.",
    },
    lesson: "git-github",
  },
  {
    id: "branch",
    term: { zh: "分支", en: "branch" },
    def: {
      zh: "指向某个提交的可移动标签，main 是默认分支；在分支上提交时标签自动向前移动。分支不是文件夹副本，创建几乎瞬间完成，HEAD 表示当前所在的分支或提交。",
      en: "A movable label pointing at a commit, with main as the default; committing on a branch advances the label. A branch is not a folder copy and costs almost nothing to create, and HEAD records which branch or commit you are on.",
    },
    lesson: "git-github",
  },
  {
    id: "remote",
    term: { zh: "远程仓库（remote）", en: "remote" },
    def: {
      zh: "本地仓库保存的一个远程仓库地址与昵称，惯用 origin 指向 GitHub 上的仓库。git remote -v 查看地址，git push 上传提交，git pull 取回并整合远程提交。",
      en: "A named URL stored by a local repository that points at another copy, conventionally origin on GitHub. git remote -v lists it, git push uploads commits and git pull fetches and integrates remote ones.",
    },
    lesson: "git-github",
  },
  {
    id: "clone",
    term: { zh: "克隆（clone）", en: "clone" },
    def: {
      zh: "把远程仓库连同完整历史复制到本地，并自动把来源登记为 origin。克隆得到的是可离线工作的完整仓库，所以大二进制文件即使删除也会拖慢每次克隆。",
      en: "Copying a remote repository and its full history to a local machine, automatically registering the source as origin. A clone is a complete repository that works offline, which is why large binaries slow every clone even after deletion.",
    },
    lesson: "git-github",
  },
  {
    id: "pull-request",
    term: { zh: "拉取请求（PR）", en: "pull request (PR)" },
    def: {
      zh: "GitHub 上请求把某个分支的提交合并进目标分支的提案，附带讨论、审查和自动检查。它不是 Git 命令，推送分支后由托管平台创建。",
      en: "A GitHub proposal to merge commits from one branch into a target branch, with discussion, review and automated checks. It is not a Git command; it is created on the hosting platform after the branch is pushed.",
    },
    lesson: "git-github",
  },
  {
    id: "staging-area",
    term: { zh: "暂存区", en: "staging area" },
    def: {
      zh: "也叫索引，是下一次提交的草稿；git add 把文件当前内容复制进去。git diff 比较工作区与暂存区，git diff --staged 比较暂存区与最后一次提交，提交前应读后者。",
      en: "Also called the index, it is the draft of the next commit; git add copies a file's current content into it. git diff compares the working tree with the index, and git diff --staged compares the index with the last commit, which is what to read before committing.",
    },
    lesson: "git-github",
  },
  {
    id: "logic-thresholds",
    term: { zh: "逻辑阈值（VIH / VIL）", en: "logic thresholds (VIH / VIL)" },
    def: {
      zh: "数字输入判定高、低电平的电压门限：高于 VIH 读为高，低于 VIL 读为低，两者之间没有定义。阈值随芯片电源而变，所以 5 V 器件输出不能直接送进不耐 5 V 的 ESP32-S3 输入。",
      en: "The voltage limits at which a digital input decides high or low: above VIH it reads high, below VIL it reads low, and between them the result is undefined. The thresholds follow the chip's supply, so a 5 V output cannot drive a 5 V-intolerant ESP32-S3 input directly.",
    },
    lesson: "components",
    firstExplained: true,
  },
  {
    id: "high-impedance",
    term: { zh: "高阻态（high-Z）", en: "high impedance (high-Z)" },
    def: {
      zh: "输入或关闭的输出呈现极高阻抗、几乎不取电流的状态。没有确定电平的高阻输入会经寄生电容耦合到附近导线的噪声，读数随机翻转，因此必须加上拉或下拉。",
      en: "A state in which an input or disabled output presents a very high impedance and draws almost no current. A high-Z input with no defined level couples noise from nearby wiring through stray capacitance and reads randomly, so it needs a pull-up or pull-down.",
    },
    lesson: "arduino-io",
    firstExplained: true,
  },
  {
    id: "bit-byte-hex",
    term: { zh: "位、字节与十六进制（bit/byte/hex）", en: "bit, byte and hexadecimal (bit/byte/hex)" },
    def: {
      zh: "一位是二进制的一个 0 或 1，一字节是 8 位；十六进制以 16 为基数，一位十六进制正好表示 4 位，常用 0x 前缀。Uno 的 RAM 只有 2 KB，因此一个字符占一字节的账要算清楚。",
      en: "A bit is one binary 0 or 1, a byte is 8 bits, and hexadecimal is base 16, with one hex digit representing exactly 4 bits and usually written with a 0x prefix. The Uno has only 2 KB of RAM, so counting one byte per character matters.",
    },
    lesson: "arduino-io",
  },
  {
    id: "lsb",
    term: { zh: "最低有效位（LSB）", en: "least significant bit (LSB)" },
    def: {
      zh: "二进制数中权重最小的一位，也指转换器能分辨的最小一步。Uno 的 10 位 ADC 在 5 V 量程下，一个 LSB 约为 4.9 mV；MPU-6050 在 ±2 g 量程下为 16384 LSB/g。",
      en: "The lowest-weight bit in a binary number, and by extension the smallest step a converter can resolve. The Uno's 10-bit ADC has one LSB of about 4.9 mV over 5 V, and the MPU-6050 at ±2 g has 16384 LSB/g.",
    },
    lesson: "arduino-io",
    firstExplained: true,
  },
  {
    id: "integer-overflow",
    term: { zh: "整数溢出", en: "integer overflow" },
    def: {
      zh: "算术结果超出变量类型能表示的范围，导致回绕或未定义结果。Uno 的 int 是 16 位有符号数，最大 32767，所以 10 位读数 raw × 1000 会在除法前溢出。",
      en: "When an arithmetic result exceeds the range of its type, causing wraparound or undefined behaviour. On the Uno, int is a 16-bit signed type with a maximum of 32767, so a 10-bit raw × 1000 overflows before the division.",
    },
    lesson: "arduino-io",
    firstExplained: true,
  },
  {
    id: "baud-rate",
    term: { zh: "波特率（baud rate）", en: "baud rate" },
    def: {
      zh: "串口每秒传输的符号数，收发两端必须设成同一个值，本课程用 115200。每个字节在线上按 10 位发送（起始位、8 个数据位、停止位），所以一个字符约需 87 µs。",
      en: "The number of symbols a serial link transfers per second; both ends must use the same value, and this course uses 115200. Each byte occupies 10 bit times on the wire (start bit, eight data bits, stop bit), so one character takes about 87 µs.",
    },
    lesson: "arduino-io",
    firstExplained: true,
  },
  {
    id: "hardware-timer",
    term: { zh: "硬件定时器", en: "hardware timer" },
    def: {
      zh: "独立于主程序运行的计数外设，可产生定时中断或 PWM，millis() 的计数就由它累加。它让计时不受 loop() 执行时间影响，是实现非阻塞定时的基础。",
      en: "A counting peripheral that runs independently of the main program and can generate timer interrupts or PWM; the counter behind millis() is one. It keeps time independent of how long loop() takes, which is the basis of non-blocking timing.",
    },
    lesson: "timing-interrupts",
    firstExplained: true,
  },
  {
    id: "isr",
    term: { zh: "中断服务程序（ISR）", en: "interrupt service routine (ISR)" },
    def: {
      zh: "硬件事件打断正常流程后执行的函数，CPU 保存位置、跳入 ISR，执行完再回到 loop() 原处。ISR 必须短小，不能调用 delay() 或 Serial，并只通过 volatile 变量与主程序共享数据。",
      en: "The function run when a hardware event interrupts normal execution; the CPU saves its place, enters the ISR and returns to the same point in loop(). An ISR must be short, must not call delay() or Serial, and should share data with the main program only through volatile variables.",
    },
    lesson: "timing-interrupts",
    firstExplained: true,
  },
  {
    id: "volatile",
    term: { zh: "volatile 关键字", en: "volatile keyword" },
    def: {
      zh: "告诉编译器该变量可能被 ISR 等异步代码改变，每次访问都必须重新从内存读取，不能缓存。它只保证重新读取，不保证多字节访问的原子性，四字节变量仍需在临界区复制。",
      en: "Tells the compiler that a variable may change asynchronously, for example in an ISR, so every access must re-read memory instead of using a cached copy. It guarantees re-reading, not atomicity; a four-byte value still needs a critical section to copy.",
    },
    lesson: "timing-interrupts",
    firstExplained: true,
  },
  {
    id: "wraparound",
    term: { zh: "回绕（wraparound）", en: "wraparound" },
    def: {
      zh: "无符号计数器到达最大值后回到零的现象；Uno 的 32 位 millis() 约 49.7 天回绕一次。正确写法是比较经过时间 now - last >= interval，无符号减法在回绕时仍然给出真实间隔。",
      en: "The return of an unsigned counter to zero after its maximum; the Uno's 32-bit millis() wraps about every 49.7 days. The correct pattern compares elapsed time with now - last >= interval, because unsigned subtraction still gives the true interval across the wrap.",
    },
    lesson: "timing-interrupts",
    firstExplained: true,
  },
  {
    id: "debouncing",
    term: { zh: "消抖（debouncing）", en: "debouncing" },
    def: {
      zh: "滤除机械触点闭合时的多次快速弹跳，让一次按下只产生一个事件。时间型消抖只在输入稳定保持 N 毫秒后才接受新状态，普通轻触按键通常取 10–50 ms。",
      en: "Filtering the rapid contact bounce when a mechanical switch closes so one press produces one event. Time-based debouncing accepts a new state only after the input has been stable for N milliseconds, typically 10–50 ms for a small tactile button.",
    },
    lesson: "timing-interrupts",
    firstExplained: true,
  },
  {
    id: "state-machine",
    term: { zh: "状态机", en: "state machine" },
    def: {
      zh: "把行为描述成少数几个状态，以及由输入和时钟决定的转换条件；每轮 loop() 检查状态并决定是否转换。它避免了 delay() 造成的阻塞，使机器人始终能响应其他事件。",
      en: "A way to describe behaviour as a small set of states plus transitions decided by inputs and time; each pass of loop() checks the state and decides whether to change it. It avoids blocking delay() calls, so the robot keeps responding to other events.",
    },
    lesson: "timing-interrupts",
    firstExplained: true,
  },
  {
    id: "strapping-pin",
    term: { zh: "启动绑定引脚（strapping pin）", en: "strapping pin" },
    def: {
      zh: "ESP32 在上电瞬间采样、用来决定启动模式和 Flash 电压的引脚，经典 ESP32 为 GPIO 0、2、5、12、15，ESP32-S3 为 GPIO 0、3、45、46。这些引脚上的外部上拉、下拉或负载可能让板子无法启动，例如 GPIO 12 启动时为高会选错 Flash 电压。",
      en: "Pins sampled at the instant an ESP32 powers up to choose the boot mode and flash voltage: GPIO 0, 2, 5, 12 and 15 on the classic ESP32, and GPIO 0, 3, 45 and 46 on the ESP32-S3. External pull-ups, pull-downs or loads on them can stop the board booting; a high GPIO 12 at boot selects the wrong flash voltage.",
    },
    lesson: "esp32",
    firstExplained: true,
  },
  {
    id: "ledc",
    term: { zh: "LED PWM 控制器（LEDC）", en: "LED PWM controller (LEDC)" },
    def: {
      zh: "ESP32 内部带硬件定时器和通道的 PWM 外设，用来产生舵机脉冲或调光。Arduino-ESP32 3.x 用 ledcAttach(pin, frequency, resolutionBits) 配置、ledcWrite(pin, duty) 改脉宽；50 Hz、14 位时 duty 范围为 0–16384（16384 表示整个周期都是高电平）。",
      en: "The ESP32's hardware PWM peripheral, with timers and channels, used for servo pulses or dimming. Arduino-ESP32 3.x configures it with ledcAttach(pin, frequency, resolutionBits) and changes the pulse with ledcWrite(pin, duty); at 50 Hz and 14 bits, duty runs from 0 to 16384 (16384 keeps the output high for the whole period).",
    },
    lesson: "esp32",
    firstExplained: true,
  },
  {
    id: "freertos-task",
    term: { zh: "FreeRTOS 任务", en: "FreeRTOS task" },
    def: {
      zh: "FreeRTOS 中独立调度、拥有自己的栈和优先级的执行单元。ESP32 的 Arduino 核心把 setup() 和 loop() 放在一个任务里，Wi-Fi 协议栈多在另一个核心运行，也可以用 xTaskCreatePinnedToCore() 创建自己的任务。",
      en: "An independently scheduled unit of execution in FreeRTOS with its own stack and priority. The ESP32 Arduino core runs setup() and loop() inside one task while most of the Wi-Fi stack runs on the other core, and xTaskCreatePinnedToCore() creates your own task.",
    },
    lesson: "esp32",
    firstExplained: true,
  },
  {
    id: "3v3-logic",
    term: { zh: "3.3 V 逻辑", en: "3.3 V logic" },
    def: {
      zh: "以 3.3 V 作为供电和逻辑高电平的器件体系，ESP32-S3 属于这一类且引脚不耐 5 V。数据手册给出的绝对最大值约为 3.6 V，接 5 V 信号要先用分压器降到安全范围。",
      en: "A device family that uses 3.3 V for both supply and logic high; the ESP32-S3 is one, and its pins are not 5 V tolerant. The datasheet's absolute maximum is about 3.6 V, so a 5 V signal must be divided down before it reaches an input.",
    },
    lesson: "esp32",
    firstExplained: true,
  },
  {
    id: "h-bridge",
    term: { zh: "H 桥", en: "H-bridge" },
    def: {
      zh: "四只开关围着电机、形似字母 H 的电路，可让直流电机正转、反转、短路刹车或滑行。TB6612FNG 每通道 1.0 A（绝对最大值 1.2 A），DRV8833 每通道约 1.2 A（Pololu #2130 模块的持续电流值），芯片内部已含体二极管和死区逻辑。",
      en: "Four switches around a motor, drawn like the letter H, that let a DC motor run forward, reverse, brake or coast. The TB6612FNG handles 1.0 A per channel (1.2 A absolute maximum) and the DRV8833 about 1.2 A (the continuous rating of the Pololu #2130 carrier module), and they include body diodes and dead-time logic.",
    },
    lesson: "motors-drivers",
    firstExplained: true,
  },
  {
    id: "shoot-through",
    term: { zh: "直通（shoot-through）", en: "shoot-through" },
    def: {
      zh: "H 桥同一侧的上、下开关同时导通，在电源与地之间形成只经过开关的低阻通路。课程模型里同时闭合 S1 与 S2 会有约 12 A 直接流过，真实驱动芯片用死区时间从根上禁止这种状态。",
      en: "Both switches on one side of an H-bridge conducting at once, creating a low-resistance path from supply to ground through only the switches. In the lesson model, closing S1 and S2 together passes about 12 A; real driver chips prevent it with dead time.",
    },
    lesson: "motors-drivers",
    firstExplained: true,
  },
  {
    id: "flyback-diode",
    term: { zh: "续流二极管", en: "flyback diode" },
    def: {
      zh: "反向并联在感性负载两端、阴极接正电源一侧的二极管，正常工作时截止。断电瞬间它为电感电流提供回路，把原本会击穿开关管的高压尖峰泄掉。",
      en: "A diode connected anti-parallel across an inductive load with its cathode on the positive supply, reverse-biased in normal operation. When the switch opens it gives the inductor current a path, clamping the high-voltage spike that would otherwise destroy the switch.",
    },
    lesson: "components",
    firstExplained: true,
  },
  {
    id: "encoder-cpr",
    term: { zh: "编码器每转计数（CPR）与正交四倍频", en: "encoder counts per revolution (CPR) and quadrature ×4 decoding" },
    def: {
      zh: "CPR 是编码器每转输出的计数；正交编码器的 A、B 两路相差 90°，对两路的每个边沿都计数就是四倍频解码。每路每转 3 个脉冲的编码器因此得到每转 12 个计数，配 120:1 减速箱后车轮每转 1440 个计数。",
      en: "CPR is the number of counts an encoder produces per revolution; a quadrature encoder has A and B 90° apart, and counting every edge on both gives ×4 decoding. An encoder with 3 pulses per channel per turn therefore yields 12 counts per turn, and with a 120:1 gearbox, 1440 counts per wheel turn.",
    },
    lesson: "motors-drivers",
    firstExplained: true,
  },
  {
    id: "stall-current",
    term: { zh: "堵转电流", en: "stall current" },
    def: {
      zh: "电机轴被完全卡住、反电动势为零时抽取的最大电流，通常是正常运行电流的 5–10 倍；课程用的 Romi 减速电机（Pololu #1520）在 4.5 V 下堵转电流为 1.25 A，是其 130 mA 空载电流的 9.6 倍。驱动器和电池必须按堵转电流选型，而不是按平稳行驶时的读数。",
      en: "The maximum current a motor draws when its shaft is held still and back-EMF is zero, typically 5–10× the running current; the course's Romi gearmotor (Pololu #1520) stalls at 1.25 A at 4.5 V, 9.6× its 130 mA free-run current. Size the driver and battery for stall current, not for the tidy reading while rolling.",
    },
    lesson: "components",
    firstExplained: true,
  },
  {
    id: "dead-band",
    term: { zh: "死区", en: "dead band" },
    def: {
      zh: "指令小到不足以克服静摩擦、机构仍不运动的输入范围。课程的一圈模型取 0.8 V，因此 5 V 供电时最小占空比至少要为 0.8 / 5.0 = 16%，否则轮子会停在目标前。",
      en: "The range of command too small to overcome static friction, where the mechanism does not move. The one-revolution model uses 0.8 V, so on a 5 V supply the minimum duty must be at least 0.8 / 5.0 = 16%, otherwise the wheel stops short of the target.",
    },
    lesson: "motors-drivers",
    firstExplained: true,
  },
  {
    id: "i2c",
    term: { zh: "I2C 总线", en: "I2C bus" },
    def: {
      zh: "用 SDA 传数据、SCL 传时钟的两线同步总线，控制器产生时钟，每个外设用 7 位地址应答。标准速率为 100 kHz 和 400 kHz；Uno 的 SDA/SCL 是 A4/A5，ESP32 经典默认是 GPIO 21/22。",
      en: "A two-wire synchronous bus with SDA for data and SCL for clock; the controller generates the clock and each peripheral answers to a 7-bit address. Standard rates are 100 kHz and 400 kHz; the Uno uses A4/A5 for SDA/SCL and the classic ESP32 defaults to GPIO 21/22.",
    },
    lesson: "sensors-fusion",
    firstExplained: true,
  },
  {
    id: "open-drain",
    term: { zh: "开漏（open-drain）", en: "open drain" },
    def: {
      zh: "输出级只能把线拉低、不能主动推高的结构，高电平必须由上拉电阻提供。多个开漏器件共线时不会互相短路，这正是 I2C 能让许多器件共享总线的原因，典型上拉为 4.7–10 kΩ。",
      en: "An output stage that can pull a line low but cannot drive it high, so a pull-up resistor supplies the high level. Several open-drain devices can share a line without contention, which is why I2C supports many devices; typical pull-ups are 4.7–10 kΩ.",
    },
    lesson: "motors-drivers",
    firstExplained: true,
  },
  {
    id: "register",
    term: { zh: "寄存器", en: "register" },
    def: {
      zh: "芯片内部按地址访问的一个字节或字，用来配置功能或读取数据。MPU-6050 的 WHO_AM_I 在 0x75、固定返回 0x68，PWR_MGMT_1 在 0x6B，上电时 SLEEP 位置位，必须写 0 唤醒。",
      en: "An addressable byte or word inside a chip, used to configure functions or read data. On the MPU-6050, WHO_AM_I is at 0x75 and always returns 0x68, while PWR_MGMT_1 at 0x6B has its SLEEP bit set at power-up and must be cleared to wake the chip.",
    },
    lesson: "sensors-fusion",
    firstExplained: true,
  },
  {
    id: "twos-complement",
    term: { zh: "二进制补码", en: "two's complement" },
    def: {
      zh: "用最高位表示负数权重的有符号整数编码，同一组位既能表示正数也能表示负数。MPU-6050 的读数是有符号 16 位，必须用 int16_t 接收，否则 −262 会被当成巨大的正数。",
      en: "The signed-integer encoding in which the most significant bit has negative weight, so the same bits represent both positive and negative values. MPU-6050 readings are signed 16-bit and must be received as int16_t, otherwise −262 becomes a huge positive number.",
    },
    lesson: "sensors-fusion",
    firstExplained: true,
  },
  {
    id: "gyro-bias",
    term: { zh: "陀螺仪零偏", en: "gyro bias" },
    def: {
      zh: "陀螺仪静止时仍输出的非零角速度，积分后会变成随时间无限增长的角度误差，误差 = 零偏 × 时间。1.5 °/s 的零偏在 60 s 后会造成 90° 误差，所以开机静止时取平均并每次积分前减去。",
      en: "The non-zero rate a gyroscope reports while stationary; integrating it produces an angle error that grows without bound, error = bias × time. A 1.5 °/s bias gives 90° of error after 60 s, so average it while still at startup and subtract it before every integration.",
    },
    lesson: "sensors-fusion",
    firstExplained: true,
  },
  {
    id: "complementary-filter",
    term: { zh: "互补滤波", en: "complementary filter" },
    def: {
      zh: "把陀螺仪积分与加速度计角度按权重融合的一行公式：angle = α × (angle + rate × dt) + (1 − α) × accelAngle。α 接近 1，典型 0.98；在 100 Hz 下时间常数 τ = 0.98 × 0.01 / 0.02 = 0.49 s。",
      en: "A one-line fusion of the integrated gyro angle with the accelerometer angle: angle = α × (angle + rate × dt) + (1 − α) × accelAngle. α is close to 1, typically 0.98; at 100 Hz the time constant is τ = 0.98 × 0.01 / 0.02 = 0.49 s.",
    },
    lesson: "sensors-fusion",
    firstExplained: true,
  },
  {
    id: "low-high-pass-filter",
    term: { zh: "低通/高通滤波", en: "low-pass/high-pass filter" },
    def: {
      zh: "低通滤波让缓慢变化通过、抑制快速噪声，高通滤波相反，只保留快速变化。互补滤波相当于对陀螺仪做高通、对加速度计做低通，两个权重相加为 1。",
      en: "A low-pass filter passes slow changes and attenuates fast noise, while a high-pass filter does the opposite and keeps only fast changes. A complementary filter is a high-pass on the gyro combined with a low-pass on the accelerometer, with weights that sum to one.",
    },
    lesson: "sensors-fusion",
  },
  {
    id: "setpoint",
    term: { zh: "设定值（setpoint）", en: "setpoint" },
    def: {
      zh: "控制器希望被控量达到的目标值。循线小车的设定值是传感器阵列中心 3500，平衡车的设定值是水平 0°，外环还会小幅修改内环的设定值。",
      en: "The target value a controller wants the measured quantity to reach. The line follower's setpoint is the centre of the sensor array, 3500, and the balancer's is level, 0°; an outer loop can also shift the inner loop's setpoint slightly.",
    },
    lesson: "first-robots",
    firstExplained: true,
  },
  {
    id: "error",
    term: { zh: "误差", en: "error" },
    def: {
      zh: "设定值减去测量值，error = setpoint − measurement，是反馈控制器唯一直接依据的量。循线时 error = 3500 − position，平衡时 error = 0° − pitch。",
      en: "The setpoint minus the measurement, error = setpoint − measurement, and the only quantity a feedback controller acts on directly. For line following, error = 3500 − position; for balancing, error = 0° − pitch.",
    },
    lesson: "first-robots",
    firstExplained: true,
  },
  {
    id: "pd-control",
    term: { zh: "PD 控制", en: "PD control" },
    def: {
      zh: "输出由比例项与微分项相加的控制器：P 按误差大小推，D 按误差变化速度制动，抑制过冲。循线小车先调 P 再加入 D，可把 62.3 mm 的过冲降到 4.8 mm。",
      en: "A controller whose output adds a proportional term to a derivative term: P pushes in proportion to error and D brakes in proportion to how fast it changes, damping overshoot. On the line follower, adding D after tuning P cut overshoot from 62.3 mm to 4.8 mm.",
    },
    lesson: "first-robots",
    firstExplained: true,
  },
  {
    id: "inverted-pendulum",
    term: { zh: "倒立摆", en: "inverted pendulum" },
    def: {
      zh: "质心位于支点上方的不稳定系统，任何小扰动都会让它倒下。质心高出车轴 0.10 m 时，倾角按时间常数 √(L/g) ≈ 0.10 s 增长，因此自平衡车的控制器必须每隔几毫秒修正一次。",
      en: "An unstable system whose centre of mass sits above its pivot, so any small disturbance makes it fall. For a centre of mass 0.10 m above the axle the tilt grows with the time constant √(L/g) ≈ 0.10 s, so a self-balancer's controller must correct every few milliseconds.",
    },
    lesson: "first-robots",
    firstExplained: true,
  },
  {
    id: "constraint",
    term: { zh: "约束", en: "constraint" },
    def: {
      zh: "CAD 草图中消除自由度的几何或尺寸关系，如水平、竖直、重合、相切、对称和尺寸标注。约束加够后草图达到 0 自由度，修改其他尺寸时不会自己移动。",
      en: "A geometric or dimensional relation in a CAD sketch that removes degrees of freedom, such as horizontal, vertical, coincident, tangent, symmetric or a dimension. Enough constraints bring the sketch to 0 DOF so it cannot move on its own when another dimension changes.",
    },
    lesson: "cad-parametric",
  },
  {
    id: "degrees-of-freedom",
    term: { zh: "自由度（DOF）", en: "degrees of freedom (DOF)" },
    def: {
      zh: "一个系统能够独立运动的方向数。2D 中一个自由点有 2 个自由度、一个圆有 3 个，空间刚体有 6 个；全约束草图的自由度为 0。",
      en: "The number of independent ways a system can move. In 2D a free point has 2 DOF and a circle has 3, a rigid body in space has 6, and a fully constrained sketch has 0.",
    },
    lesson: "cad-parametric",
  },
  {
    id: "datum",
    term: { zh: "基准", en: "datum" },
    def: {
      zh: "标注尺寸所依据的原点、中心线、参考面或参考边，所有尺寸都应从同一基准分别标出。从基准标注避免串联尺寸把误差一路累积到最后一件特征。",
      en: "The origin, centreline, reference plane or reference edge from which dimensions are taken, with every dimension measured from the same datum. Datum-based dimensions avoid chained dimensions that pass error along to the last feature.",
    },
    lesson: "cad-parametric",
  },
  {
    id: "tolerance",
    term: { zh: "公差", en: "tolerance" },
    def: {
      zh: "允许尺寸偏离名义值的范围，是图纸的一部分而不是缺陷。FDM 打印中孔通常偏小、外形偏大，所以必须用自己机器的公差测试件量出真实间隙，而不是照抄课程里的数字。",
      en: "The permitted range of deviation from a nominal dimension, part of the specification rather than a defect. FDM holes usually print small and outer shapes large, so measure your own machine's real clearances with a tolerance gauge instead of copying the lesson's numbers.",
    },
    lesson: "cad-parametric",
  },
  {
    id: "fit",
    term: { zh: "配合（间隙/过盈）", en: "fit (clearance/interference)" },
    def: {
      zh: "两个零件装配时的尺寸关系：间隙配合可自由滑动或转动，过盈配合需要压入并靠摩擦力保持。间隙按每侧计算，3 mm 轴配每侧 0.15 mm 的滑配需要 3.3 mm 孔，画成 3.15 mm 就会干涉。",
      en: "The dimensional relationship between two mating parts: a clearance fit slides or turns freely, while an interference fit must be pressed in and is held by friction. Clearance is per side, so a 3 mm shaft with 0.15 mm per side needs a 3.3 mm hole; 3.15 mm would interfere.",
    },
    lesson: "fdm-printing",
  },
  {
    id: "layer-height",
    term: { zh: "层高", en: "layer height" },
    def: {
      zh: "FDM 打印中每一层的厚度，SO-101 的结构件按仓库要求使用 0.2 mm 层高和 0.4 mm 喷嘴。层高越小细节越好但打印更慢，层高越大则层间台阶和结合方式都会改变。",
      en: "The thickness of each layer in FDM printing; the SO-101 structural parts use the repository's 0.2 mm layer height with a 0.4 mm nozzle. A smaller layer height gives finer detail but takes longer, while a larger one changes the stair-stepping and how layers bond.",
    },
    lesson: "fdm-printing",
  },
  {
    id: "perimeter-wall",
    term: { zh: "外墙/壁数", en: "perimeter/wall" },
    def: {
      zh: "切片件每层外侧的实心走线，强度主要来自外墙而不是填充，所以多加一两道墙通常比加填充更有效。壁厚应取挤出宽度的整数倍，0.4 mm 喷嘴对应 0.8、1.2 或 1.6 mm。",
      en: "The solid paths around the outside of each sliced layer; strength comes mainly from the walls rather than the infill, so one or two extra walls usually beat more infill. Wall thickness should be a multiple of extrusion width, so a 0.4 mm nozzle gives 0.8, 1.2 or 1.6 mm.",
    },
    lesson: "fdm-printing",
  },
  {
    id: "infill",
    term: { zh: "填充", en: "infill" },
    def: {
      zh: "零件内部按一定百分比和图案打印的材料，用于支撑顶面并提供部分刚度。SO-101 的结构件按仓库规定使用 15% 填充，而强度主要由外墙承担。",
      en: "The material printed inside a part at a chosen percentage and pattern to support top surfaces and add some stiffness. The SO-101 structural parts use the repository's 15% infill, while most strength still comes from the walls.",
    },
    lesson: "fdm-printing",
  },
  {
    id: "glass-transition-tg",
    term: { zh: "玻璃化转变温度（Tg）", en: "glass transition temperature (Tg)" },
    def: {
      zh: "聚合物从坚硬玻璃态转变成柔软橡胶态的温区，不是熔点；PLA 约在 55–60 °C 开始软化，PETG 的 Tg 约为 80 °C。贴近 70 °C 电机的安装座要选 ABS、ASA 或留足余量的 PETG，而不是 PLA。",
      en: "The temperature range where a polymer changes from a hard glassy state to a soft rubbery one, not its melting point; PLA starts to soften around 55–60 °C and PETG's Tg is about 80 °C. A mount next to a 70 °C motor needs ABS, ASA or PETG with margin, not PLA.",
    },
    lesson: "fdm-printing",
  },
  {
    id: "anisotropy",
    term: { zh: "各向异性", en: "anisotropy" },
    def: {
      zh: "材料性能随方向而变；FDM 件由一层层熔接的线组成，层与层之间的结合弱于层内。设计时让主要载荷沿着层走，而不是横跨层，否则零件会沿层线裂开。",
      en: "Material properties that differ with direction; an FDM part is built from welded lines in layers, and the bond between layers is weaker than the plastic within a layer. Design so the main load runs along the layers rather than across them, or the part will split along a layer line.",
    },
    lesson: "fdm-printing",
  },
  {
    id: "creep",
    term: { zh: "蠕变", en: "creep" },
    def: {
      zh: "材料在持续载荷下随时间缓慢发生的永久变形，即使应力低于屈服强度。PLA 在长期受力的螺柱或悬臂上会蠕变，因此持续承载的机器人零件常改用 PETG 或更耐热的材料。",
      en: "Slow permanent deformation of a material under sustained load, even below its yield stress. PLA creeps in long-loaded bosses or cantilevers, which is why robot parts under continuous load often move to PETG or a more heat-resistant material.",
    },
    lesson: "fdm-printing",
  },
  {
    id: "stress",
    term: { zh: "应力", en: "stress" },
    def: {
      zh: "单位面积上承受的内力，常用单位为 MPa 或 N/mm²。卡扣臂根部的应力集中最危险，所以设计时要在根部加圆角，并让应力与实际截面积匹配。",
      en: "Internal force per unit area, commonly in MPa or N/mm². Stress concentrates at the root of a snap-fit arm, so the design adds a fillet there and keeps the stress consistent with the actual cross-section.",
    },
    lesson: "fdm-printing",
  },
  {
    id: "strain",
    term: { zh: "应变", en: "strain" },
    def: {
      zh: "变形量与原始长度之比，是无量纲量，常用百分比表示。悬臂卡扣根部的应变为 ε = 1.5 × y × t / L²；L = 10 mm、t = 1.2 mm、钩深 0.8 mm 时为 1.44%，低于 PLA 的 1.5% 经验上限。",
      en: "Deformation divided by original length, dimensionless and often shown as a percentage. A cantilever snap arm's root strain is ε = 1.5 × y × t / L²; with L = 10 mm, t = 1.2 mm and a 0.8 mm hook it is 1.44%, below the cautious 1.5% limit for PLA.",
    },
    lesson: "fdm-printing",
  },
  {
    id: "youngs-modulus",
    term: { zh: "杨氏模量", en: "Young's modulus" },
    def: {
      zh: "材料在弹性范围内应力与应变之比，衡量刚度，单位 MPa。课程脚本取 PLA 为 3500 MPa、PETG 为 2000 MPa，所以同样几何的 PETG 卡扣压入力量更小、更有弹性。",
      en: "The ratio of stress to strain in the elastic range, a measure of stiffness in MPa. The lesson script uses 3500 MPa for PLA and 2000 MPa for PETG, so the same snap geometry in PETG is more flexible and needs less push-on force.",
    },
    lesson: "fdm-printing",
  },
  {
    id: "torque",
    term: { zh: "扭矩", en: "torque" },
    def: {
      zh: "使物体绕轴转动的力矩，单位牛·米（N·m）；功率 P = τ × ω。0.05 N·m 的电机经 25:1、效率 81% 的两级减速后输出约 1.01 N·m。",
      en: "The moment that tends to rotate an object about an axis, in newton-metres (N·m); power is P = τ × ω. A 0.05 N·m motor through a 25:1 two-stage reduction at 81% efficiency delivers about 1.01 N·m.",
    },
    lesson: "transmissions",
  },
  {
    id: "angular-velocity",
    term: { zh: "角速度", en: "angular velocity" },
    def: {
      zh: "单位时间转过的角度，常用 rad/s 或 rpm 表示，符号 ω。减速比 n 把输入转速除以 n，所以 6000 rpm 的电机经 25:1 减速后输出 240 rpm。",
      en: "Angle turned per unit time, usually in rad/s or rpm, symbol ω. A gear ratio n divides input speed by n, so a 6000 rpm motor through a 25:1 reduction turns its output at 240 rpm.",
    },
    lesson: "transmissions",
  },
  {
    id: "moment-of-inertia",
    term: { zh: "转动惯量", en: "moment of inertia" },
    def: {
      zh: "物体抵抗角加速度的性质，单位 kg·m²；本课关节模型取 J = 0.004 kg·m²。经过 n:1 减速器后，手推动输出端感受到的转子惯量按 n² 放大，所以从臂 345:1 的惯性感约为 147:1 的 5.51 倍。",
      en: "The property that resists angular acceleration, in kg·m²; the lesson's joint model uses J = 0.004 kg·m². Through an n:1 gearbox, the rotor inertia felt when backdriving the output grows with n², so the follower's 345:1 joint feels about 5.51× the inertia of a 147:1 joint.",
    },
    lesson: "transmissions",
  },
  {
    id: "gear-ratio",
    term: { zh: "减速比", en: "gear ratio" },
    def: {
      zh: "输入转 n 圈、输出转 1 圈的比值，记作 n:1；忽略摩擦时扭矩乘 n、转速除以 n，功率不变。行星级在齿圈固定、太阳轮输入、行星架输出时，减速比 = 1 + 齿圈齿数 / 太阳轮齿数。",
      en: "The ratio n:1 meaning n input turns for one output turn; ignoring friction, torque is multiplied by n and speed divided by n at constant power. For a planetary stage with the ring fixed, sun input and carrier output, the ratio is 1 + ring teeth / sun teeth.",
    },
    lesson: "transmissions",
  },
  {
    id: "gear-module",
    term: { zh: "齿轮模数", en: "gear module" },
    def: {
      zh: "齿轮齿形大小的标准参数，等于分度圆直径除以齿数，配对齿轮必须使用相同模数才能正确啮合。模数与齿数一起决定中心距：a = m × (z1 + z2) / 2。",
      en: "The standard parameter for gear tooth size, equal to pitch diameter divided by tooth count; meshing gears must share the same module. Module and tooth counts set the centre distance: a = m × (z1 + z2) / 2.",
    },
    lesson: "transmissions",
  },
  {
    id: "centre-distance",
    term: { zh: "中心距", en: "centre distance" },
    def: {
      zh: "一对齿轮两轴之间的距离，由模数与齿数决定，也由打印件上的轴承座位置实现。中心距略小可以消掉齿间自由行程，太小时摩擦和发热急剧增加，甚至根本转不动。",
      en: "The distance between the shafts of two meshing gears, set by module and tooth counts and realised by the bearing bores in a printed part. Slightly reducing it removes free play between teeth, but too little raises friction and heat sharply and can stop the gears turning.",
    },
    lesson: "transmissions",
  },
  {
    id: "backlash",
    term: { zh: "回差", en: "backlash" },
    def: {
      zh: "啮合齿之间的自由间隙，输入端小幅转动时输出端可以完全不动；传动链上每个啮合点都会累加。关节上 1° 的回差在 0.30 m 手臂末端就是 0.30 × π / 180 ≈ 5.2 mm 的位置误差，软件无法在间隙内施加力。",
      en: "The free play between meshing teeth, within which the input can move while the output does not; every mesh in a train adds its share. At a joint, 1° of backlash produces 0.30 × π / 180 ≈ 5.2 mm of tip error on a 0.30 m arm, and software cannot push inside the gap.",
    },
    lesson: "transmissions",
  },
  {
    id: "preload",
    term: { zh: "预紧", en: "preload" },
    def: {
      zh: "用弹簧、螺母或波簧沿固定方向施加的轻压，用来消除轴承游隙或齿轮回差，让轴和关节更刚。预紧必须受控：过大会让轴承发涩、发热并快速磨损。",
      en: "A light, controlled force applied by a spring, nut or wave washer in a fixed direction to remove bearing play or gear backlash and make a shaft or joint stiffer. Preload must be controlled; too much makes bearings stiff, hot and short-lived.",
    },
    lesson: "transmissions",
  },
  {
    id: "proportional-term",
    term: { zh: "比例项（P）", en: "proportional term (P)" },
    def: {
      zh: "PID 中与当前误差成正比的一项，输出为 Kp × error；误差越大推得越狠。只有 P 时，顶住恒定重力需要保留一个稳态误差，例如 0.227 N·m / 0.05 N·m/度 = 4.5°。",
      en: "The PID term proportional to the present error, Kp × error, pushing harder the farther away the target is. With P alone, holding a constant gravity load requires a steady-state error, for example 0.227 N·m / 0.05 N·m per degree = 4.5°.",
    },
    lesson: "pid-control",
  },
  {
    id: "integral-term",
    term: { zh: "积分项（I）", en: "integral term (I)" },
    def: {
      zh: "PID 中与误差随时间的累积成正比的一项，输出为 Ki × ∫error dt；它能在误差为零时继续输出力矩，从而消除稳态误差。代价是响应最慢，并且输出饱和时容易积分饱和。",
      en: "The PID term proportional to the accumulated error over time, Ki × ∫error dt; it can keep producing torque at zero error, which removes steady-state error. The cost is the slowest response and a tendency to wind up when the output saturates.",
    },
    lesson: "pid-control",
  },
  {
    id: "derivative-term",
    term: { zh: "微分项（D）", en: "derivative term (D)" },
    def: {
      zh: "PID 中与误差或测量值变化速度成正比的一项，作用像阻尼器，在接近目标时制动以抑制过冲。工程上通常对测量值求导以避免目标跳变引起的微分冲击，但它也会放大传感器噪声。",
      en: "The PID term proportional to how fast the error or measurement changes; it acts like a damper, braking on approach to reduce overshoot. Practice differentiates the measurement to avoid derivative kick from a setpoint step, but this also amplifies sensor noise.",
    },
    lesson: "pid-control",
  },
  {
    id: "overshoot",
    term: { zh: "超调", en: "overshoot" },
    def: {
      zh: "响应第一次越过设定值的最大量，通常以角度或百分比表示。课程关节模型中，完整 PID 的超调为 0.1°，而同一组增益关闭抗积分饱和后增大到 8.8°。",
      en: "The maximum amount by which a response first passes beyond the setpoint, usually in degrees or percent. In the lesson's joint model, a full PID overshoots by 0.1°, while the same gains without anti-windup overshoot by 8.8°.",
    },
    lesson: "pid-control",
  },
  {
    id: "settling-time",
    term: { zh: "稳定时间", en: "settling time" },
    def: {
      zh: "响应进入并保持在设定值附近某个误差带内所需的时间。课程以 1° 为误差带，完整 PID 在 0.24 s 内进入，只有 PI 时需要 0.92 s。",
      en: "The time a response takes to enter and remain inside a chosen error band around the setpoint. The lesson uses a 1° band: the full PID enters it in 0.24 s, while PI alone needs 0.92 s.",
    },
    lesson: "pid-control",
  },
  {
    id: "steady-state-error",
    term: { zh: "稳态误差", en: "steady-state error" },
    def: {
      zh: "系统稳定后仍然存在的目标与测量之差。只有 P 的关节在 60° 目标前 4.5° 停住，加入积分项后最终到达 60.0°，稳态误差才消失。",
      en: "The difference between setpoint and measurement that remains after the system has settled. The P-only joint stops 4.5° short of its 60° target; adding the integral term brings it to 60.0° and removes the steady-state error.",
    },
    lesson: "pid-control",
  },
  {
    id: "integral-windup",
    term: { zh: "积分饱和（windup）", en: "integral windup" },
    def: {
      zh: "输出已经达到执行器上限时，积分项仍继续累加误差，存下一大团暂时无法实现的指令，导致脱困后大幅超调。修法是只在未饱和时积分、限制积分范围，或在目标跳变时清零积分。",
      en: "When the output is already at the actuator limit and the integral keeps accumulating error, it stores a large command that cannot be delivered and causes a big overshoot on release. Fix it by integrating only while unsaturated, clamping the integral, or resetting it on a setpoint step.",
    },
    lesson: "pid-control",
  },
  {
    id: "feedforward",
    term: { zh: "前馈", en: "feedforward" },
    def: {
      zh: "不等误差出现，直接根据模型或已知扰动发出指令的开环补偿；它与反馈并联，可减轻反馈环的负担。机械臂的重力前馈按测到的角度算出重力力矩并加到指令上，模型准确时正好抵消重力。",
      en: "An open-loop command computed from a model or a known disturbance before any error appears; it runs alongside feedback and reduces the burden on the loop. Gravity feedforward on the arm computes the gravity torque from the measured angle and adds it to the command, cancelling gravity when the model is right.",
    },
    lesson: "control-modelling",
  },
  {
    id: "cascade-control",
    term: { zh: "串级控制", en: "cascade control" },
    def: {
      zh: "两个反馈回路嵌套，外环较慢，通过修改内环的设定值来间接控制慢变量；内环较快，直接驱动执行器。平衡车的外环以 25 Hz 控制轮速并把倾角设定值限制在 ±3°，内环以 200 Hz 维持倾角。",
      en: "Two nested feedback loops: a slower outer loop controls a slow variable by changing the inner loop's setpoint, while the faster inner loop drives the actuator directly. The balancer's outer loop runs at 25 Hz on wheel speed and limits the tilt setpoint to ±3°, while the inner loop holds tilt at 200 Hz.",
    },
    lesson: "pid-control",
  },
  {
    id: "bus-servo",
    term: { zh: "总线舵机", en: "bus servo" },
    def: {
      zh: "带有 ID、经串行总线通信并能回传位置、速度、负载、电压和温度的闭环舵机。SO-101 每臂使用 6 个飞特 STS3215，12 位磁编码器每圈给出 4096 步，位置环在舵机内部运行。",
      en: "A closed-loop servo with an ID that communicates over a serial bus and reports position, speed, load, voltage and temperature. Each SO-101 arm uses six Feetech STS3215 servos, whose 12-bit magnetic encoders give 4096 steps per turn and whose position loop runs inside the servo.",
    },
    lesson: "so101-arm",
  },
  {
    id: "half-duplex",
    term: { zh: "半双工", en: "half-duplex" },
    def: {
      zh: "一对线可以双向传输但不能同时进行的通信方式，控制器先发送、再监听。SO-101 的六个 STS3215 共用一条半双工总线，LeRobot 把这条线跑在 1 Mbit/s。",
      en: "Communication over one pair of wires in both directions but not at the same time; the controller talks, then listens. The six STS3215 servos on an SO-101 share one half-duplex bus, which LeRobot runs at 1 Mbit/s.",
    },
    lesson: "so101-arm",
  },
  {
    id: "daisy-chain",
    term: { zh: "菊花链", en: "daisy chain" },
    def: {
      zh: "设备首尾相接、共用一条总线的连接方式；每个舵机有独立 ID，只有被点名的那个才应答。SO-101 的串行线从夹爪一路菊花链回底座，最后把 shoulder_pan（ID 1）接到控制板。",
      en: "A connection in which devices are linked one after another on a shared bus; each servo has its own ID and only the addressed one answers. The SO-101 serial line daisy-chains from the gripper back to the base, where shoulder_pan (ID 1) plugs into the controller.",
    },
    lesson: "so101-arm",
  },
  {
    id: "eeprom",
    term: { zh: "EEPROM", en: "EEPROM" },
    def: {
      zh: "舵机内部断电不丢失的非易失存储器，用来保存 ID 和总线波特率等设置。正常设置一次即可长期保留，但换上新舵机时它又回到出厂 ID 1，必须重新设置。",
      en: "Non-volatile memory inside a servo that keeps settings such as its ID and bus baud rate across power cycles. It is set once in normal use, but a replacement servo arrives with the factory ID 1 and must be set again.",
    },
    lesson: "so101-arm",
  },
  {
    id: "little-endian",
    term: { zh: "小端序（little-endian）", en: "little-endian" },
    def: {
      zh: "多字节数值中低字节存放在前的字节序。STS3215 的目标位置 2048 = 0x0800 发送为低字节 00、高字节 08；回复参数 2C 0C 按小端拼成 0x0C2C = 3116 步。",
      en: "A byte order in which the low byte of a multi-byte value comes first. The STS3215 goal position 2048 = 0x0800 is sent as low byte 00 then high byte 08, and the reply parameter 2C 0C assembles to 0x0C2C = 3116 steps.",
    },
    lesson: "so101-arm",
  },
  {
    id: "checksum",
    term: { zh: "校验和", en: "checksum" },
    def: {
      zh: "把 ID、长度、指令和参数相加后取低字节再按位取反，附在数据包末尾用于发现传输错误。它不修复消息，只拒绝消息；翻转数据中的一个比特就会让校验失败。",
      en: "The low byte of the sum of ID, length, instruction and parameters, inverted and appended to a packet to detect transmission errors. It does not repair a message, it rejects it; flipping one data bit makes the checksum fail.",
    },
    lesson: "so101-arm",
  },
  {
    id: "teleoperation",
    term: { zh: "遥操作", en: "teleoperation" },
    def: {
      zh: "由人手动移动主臂、从臂实时复制动作的操作方式。它不只是演示，还是录制演示数据的手段：主臂给出动作，从臂给出自身的关节读数，两者合起来供第 6 个月的模仿学习使用。",
      en: "Operating a robot by moving a leader arm by hand while the follower reproduces the motion. It is not only a demo but the way demonstrations are recorded: the leader supplies the action and the follower its own joint readings, together forming data for Month 6 imitation learning.",
    },
    lesson: "so101-arm",
  },
  {
    id: "leader-follower",
    term: { zh: "主臂/从臂", en: "leader/follower arm" },
    def: {
      zh: "SO-101 的一对机械臂：主臂是手推动的输入设备，从臂执行动作并回传关节读数。从臂六个关节全用 1/345 减速比，主臂混用 1/147、1/191 和 1/345，以便在需要支撑处撑住、其余关节容易被手扳动。",
      en: "The SO-101 pair: the leader is the hand-driven input device, and the follower executes the motion and reports its joint readings. The follower uses 1/345 on all six joints, while the leader mixes 1/147, 1/191 and 1/345 so it holds where needed and stays easy to backdrive elsewhere.",
    },
    lesson: "so101-arm",
  },
];

export function getTerm(id: string): GlossaryEntry | undefined {
  return glossary.find((g) => g.id === id);
}
