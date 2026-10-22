import type { Lesson, Month } from "./types";

export const COURSE_SOURCE = {
  author: "@DeRonin_",
  authorUrl: "https://x.com/DeRonin_",
  url: "https://x.com/DeRonin_/status/2095180126359105955",
  title: "How to become a Robotics Engineer in 6 months (RESOURCES)",
};

const month1Lessons: Lesson[] = [
  {
    slug: "ohms-law",
    title: { zh: "电压、电流、电阻与欧姆定律", en: "Voltage, current, resistance & Ohm's law" },
    summary: {
      zh: "建立电的直觉模型，熟练使用欧姆定律、功率公式与分压器。",
      en: "Build an intuition for electricity and make Ohm's law, power and voltage dividers automatic.",
    },
    minutes: 90,
    objectives: [
      { zh: "能在 A 与 mA、Ω 与 kΩ、MΩ 之间换算，且不丢 1000 倍。", en: "Convert between A and mA and between Ω, kΩ and MΩ without losing a factor of 1000." },
      { zh: "能用欧姆定律 V = I × R 和功率公式 P = V × I = I² × R = V² / R 在纸上计算电路。", en: "Use Ohm's law V = I × R and the power forms P = V × I = I² × R = V² / R to calculate a circuit on paper." },
      { zh: "能计算串并联电阻（220 Ω + 330 Ω = 550 Ω，两个 10 kΩ 并联为 5 kΩ），并应用 Vout = Vin × R2 / (R1 + R2)。", en: "Combine series and parallel resistances (220 Ω + 330 Ω = 550 Ω; two 10 kΩ in parallel = 5 kΩ) and apply Vout = Vin × R2 / (R1 + R2)." },
      { zh: "能解释 10 kΩ 负载为何使 1.6 V 分压输出降到约 1.2 V，以及何时应改用稳压器。", en: "Explain why a 10 kΩ load drops the 1.6 V divider output to about 1.2 V, and when to use a regulator." },
    ],
    prereqs: [],
    resources: ["falstad", "aac", "afrotechmods"],
    tasks: [
      { id: "falstad-ohms", text: { zh: "在 Falstad 中打开欧姆定律示例，改变电阻值并观察电流变化", en: "Open the Ohm's-law example in Falstad, change the resistor and watch the current change" } },
      { id: "divider-hand", text: { zh: "手算 5V、10kΩ/4.7kΩ 分压器的输出电压", en: "Calculate by hand the output of a 5 V, 10 kΩ / 4.7 kΩ divider" } },
      { id: "divider-sim", text: { zh: "在 Falstad 中搭建该分压器，确认仿真结果与手算一致", en: "Build that divider in Falstad and confirm the simulation matches your maths" } },
      { id: "quiz-ohms", text: { zh: "完成本课全部小测验", en: "Answer every quiz on this page" } },
    ],
  },
  {
    slug: "components",
    title: { zh: "元件、原理图与晶体管开关", en: "Components, schematics & the transistor switch" },
    summary: {
      zh: "认识电阻、电容、二极管/LED、晶体管，读懂原理图，理解上拉/下拉、去耦电容与电池安全。",
      en: "Meet resistors, capacitors, diodes/LEDs and transistors, read schematics, and understand pull-ups, decoupling and battery safety.",
    },
    minutes: 120,
    objectives: [
      { zh: "能识别电阻、电容、二极管、LED、NPN 三极管和 GND 的符号，并读懂连接点、交叉无点和同名网络标号。", en: "Read resistor, capacitor, diode, LED, NPN transistor and GND symbols, junction dots, dot-less crossings and same-net labels." },
      { zh: "能计算 τ = R × C 并掌握 63 % 与 99 % 两个节点，会在每个 IC 的 VCC 与 GND 之间放置 100 nF 去耦电容。", en: "Calculate τ = R × C with the 63 % and 99 % milestones, and place a 100 nF decoupling capacitor at each IC's VCC and GND." },
      { zh: "能用 R = (Vsupply − Vf) / I 计算 LED 限流电阻，并解释 Rb = 100 kΩ 为何使三极管无法饱和。", en: "Size an LED resistor with R = (Vsupply − Vf) / I, and explain why Rb = 100 kΩ keeps the transistor out of saturation." },
      { zh: "能解释悬空输入与 INPUT_PULLUP、LiPo 的 3.7 V/4.2 V 限制和 C 数，以及用 V = I × R 解释堵转导致的欠压复位。", en: "Explain floating inputs and INPUT_PULLUP, LiPo 3.7 V/4.2 V limits and C ratings, and stall brownout with V = I × R." },
    ],
    prereqs: ["ohms-law"],
    resources: ["falstad", "tinkercad", "aac", "make-electronics"],
    tasks: [
      { id: "led-resistor", text: { zh: "为 5V 驱动的红色 LED（2V，10mA）计算限流电阻", en: "Calculate the current-limiting resistor for a red LED (2 V, 10 mA) on 5 V" } },
      { id: "transistor-sim", text: { zh: "在 Falstad 中运行晶体管开关电路，用开关模拟 3.3V 逻辑引脚控制 LED", en: "Run the transistor-switch circuit in Falstad and use the switch as a 3.3 V logic pin driving the LED" } },
      { id: "rc-sim", text: { zh: "运行 RC 充放电示例，估算时间常数 τ = RC", en: "Run the RC charge/discharge example and estimate the time constant τ = RC" } },
      { id: "brownout", text: { zh: "用自己的话写下：为什么电机堵转会让单片机复位", en: "Write in your own words why a stalling motor can reset a microcontroller" } },
    ],
  },
  {
    slug: "bench-multimeter",
    title: { zh: "工作台、工具预算与万用表", en: "The bench, tool budget & the multimeter" },
    summary: {
      zh: "按预算分层准备工具，学会用万用表测电压、电阻、通断与电流——这是之后最省时间的技能。",
      en: "Equip your bench in budget tiers and learn to measure voltage, resistance, continuity and current — the skill that saves the most hours later.",
    },
    minutes: 90,
    objectives: [
      { zh: "能说出 COM、VΩ、mA、10A 各插孔的用途，以及测电流时与测完后红表笔的位置。", en: "Identify the COM, VΩ, mA and 10A jacks, and state where the red lead goes during and after a current measurement." },
      { zh: "能并联测电压、串联测电流，并解释各自为什么。", en: "Measure voltage in parallel and current in series, and explain why each method is required." },
      { zh: "能手读 4 环色环阻值（含倍率与误差），并在断电、离路条件下测量电阻。", en: "Read 4-band resistor colour codes including multiplier and tolerance, and measure resistance powered off and out of circuit." },
      { zh: "能用通断档查找断线并在上电前检查电源对地短路，能背出六步排障流程。", en: "Use continuity to find a dead wire and check supply to ground for shorts, and walk the six-step troubleshooting routine." },
    ],
    prereqs: ["ohms-law", "components"],
    resources: ["sparkfun-multimeter", "sparkfun-resistors", "adafruit-dmm", "elegoo-super", "elegoo-basic", "sparkfun-sik", "tinkercad"],
    tasks: [
      { id: "battery", text: { zh: "测量一节电池的电压（新电池与旧电池各一节更好）", en: "Measure the voltage of a battery (ideally one new and one used)" } },
      { id: "five-resistors", text: { zh: "读出 5 个随机电阻的色环，再用万用表实测并对比", en: "Read the colour bands on 5 random resistors, then measure each and compare" } },
      { id: "broken-wire", text: { zh: "自己做一根“断线”，用通断档把它找出来", en: "Make a deliberately broken wire and find it with continuity mode" } },
      { id: "no-hardware", text: { zh: "（暂无硬件时）在 Tinkercad Circuits 中用虚拟万用表完成以上测量", en: "(No hardware yet?) Do the same measurements with Tinkercad's virtual multimeter" } },
    ],
  },
  {
    slug: "soldering",
    title: { zh: "焊接", en: "Soldering" },
    summary: {
      zh: "安全地焊出干净的通孔焊点，识别冷焊，并学会拆焊与返修。",
      en: "Make clean through-hole joints safely, recognise cold joints, and learn to desolder and rework.",
    },
    minutes: 120,
    objectives: [
      { zh: "能把恒温烙铁设为有铅 63/37 的 320–350 °C 或无铅 SAC305 的 350–380 °C，并正确上锡与存放烙铁头。", en: "Set a temperature-controlled iron to 320–350 °C for 63/37 leaded or 350–380 °C for SAC305, and tin and store the tip correctly." },
      { zh: "能在 2–4 s 内完成通孔焊点：同时加热焊盘与引脚，把焊锡送入焊点。", en: "Make a through-hole joint in 2–4 s by heating the pad and lead together and feeding solder into the joint." },
      { zh: "能识别冷焊、桥连、锡过多和扰动焊点，并用助焊剂、重新加热、吸锡带或吸锡器修正。", en: "Identify cold, bridged, excess-solder and disturbed joints, and correct them with flux, reheat, braid or a pump." },
      { zh: "能焊完排针并用通断档确认每根针到自己的焊盘导通、相邻针不响。", en: "Solder a header and verify with continuity that each pin reaches its own pad and adjacent pins do not beep." },
    ],
    prereqs: ["bench-multimeter"],
    resources: ["adafruit-soldering", "sparkfun-multimeter", "pinecil"],
    tasks: [
      { id: "tin-tip", text: { zh: "给烙铁头上锡，并练习保持清洁", en: "Tin the iron tip and practise keeping it clean" } },
      { id: "headers-x3", text: { zh: "给一块便宜的模块焊排针，用通断档逐针测试——重复 3 次", en: "Solder header pins onto a cheap breakout and continuity-test every pin — three times" } },
      { id: "desolder", text: { zh: "拆下一个焊点再重新焊好", en: "Desolder one joint and resolder it" } },
      { id: "inspect", text: { zh: "对照检查清单给自己的焊点拍照并逐一评估", en: "Photograph your joints and grade each against the inspection checklist" } },
    ],
  },
  {
    slug: "python-terminal",
    title: { zh: "Python 与终端", en: "Python & the terminal" },
    summary: {
      zh: "掌握函数、类、文件读写、JSON、虚拟环境与 pip，并在终端中自如地运行脚本。",
      en: "Get comfortable with functions, classes, file I/O, JSON, virtual environments and pip — and run it all from the terminal.",
    },
    minutes: 180,
    objectives: [
      { zh: "能用 pwd、ls、cd 导航，创建文件和目录，并使用管道、重定向与 export ROBOT_NAME。", en: "Navigate with pwd, ls and cd, create files and folders, and use pipes, redirection and export ROBOT_NAME." },
      { zh: "能创建并激活 venv、安装包、冻结到 requirements.txt、退出环境，并绝不提交 .venv。", en: "Create and activate a venv, install a package, freeze it to requirements.txt, deactivate, and never commit .venv." },
      { zh: "能运行 ohm.py 的 current 与 divider 子命令：5 V 加在 220 Ω 上输出 22.7 mA，5 V 配 10 kΩ/4.7 kΩ 输出 1.599 V。", en: "Run ohm.py current and divider subcommands: 5 V across 220 Ω prints 22.7 mA, and 5 V with 10 kΩ/4.7 kΩ prints 1.599 V." },
      { zh: "能定义 @dataclass Resistor 和 JSON 记录器，并从下往上读 traceback，识别 ValueError、ModuleNotFoundError 与 IndentationError。", en: "Define a @dataclass Resistor and a JSON logger, and read tracebacks bottom-up to identify ValueError, ModuleNotFoundError and IndentationError." },
    ],
    prereqs: ["ohms-law"],
    resources: ["cs50p", "py4e", "missing-semester", "python-tutorial"],
    tasks: [
      { id: "venv", text: { zh: "创建虚拟环境并用 pip 安装一个包", en: "Create a virtual environment and pip-install a package" } },
      { id: "ohm-cli", text: { zh: "写一个命令行欧姆定律/分压计算器脚本", en: "Write a command-line Ohm's-law / divider calculator script" } },
      { id: "json-log", text: { zh: "写脚本把测量数据保存为 JSON 并重新读出", en: "Write a script that saves measurements to JSON and reads them back" } },
      { id: "terminal-drill", text: { zh: "完成终端练习：cd、ls、grep、环境变量、管道", en: "Finish the terminal drill: cd, ls, grep, environment variables, pipes" } },
    ],
  },
  {
    slug: "git-github",
    title: { zh: "Git 与 GitHub", en: "Git & GitHub" },
    summary: {
      zh: "用 Git 管理每一个项目：init、add、commit、push、分支，以及一份别人能照着做的 README。",
      en: "Put every project under Git — init, add, commit, push, branches — with a README someone else can follow.",
    },
    minutes: 120,
    objectives: [
      { zh: "能配置 user.name、user.email 和 init.defaultBranch main，并用 gh auth login 或 SSH 密钥完成认证。", en: "Configure Git with user.name, user.email and init.defaultBranch main, and authenticate via gh auth login or an SSH key." },
      { zh: "能解释工作区、暂存区和仓库，并用祈使句提交 ohm.py 与 log.py。", en: "Explain the working directory, staging area and repository, then stage and commit ohm.py and log.py with an imperative message." },
      { zh: "能创建分支、合并回 main，并通过删除冲突标记、执行 git add 与 git commit 手动解决冲突。", en: "Create a branch, merge it into main, and resolve a conflict by editing the markers, then running git add and git commit." },
      { zh: "能写包含照片、元件清单、接线表、运行命令和“出了什么问题”一节的 README，并用 .gitignore 排除 .venv。", en: "Write a README with photo, parts list, wiring table, run commands and a what-broke section, and exclude .venv via .gitignore." },
    ],
    prereqs: ["python-terminal"],
    resources: ["learn-git-branching", "missing-semester", "pro-git"],
    tasks: [
      { id: "lgb-intro", text: { zh: "完成 Learn Git Branching 的 “Introduction Sequence” 关卡", en: "Finish the Learn Git Branching “Introduction Sequence”" } },
      { id: "first-repo", text: { zh: "把本月的 Python 脚本放进 Git 仓库并推送到 GitHub", en: "Put this month's Python scripts in a Git repo and push it to GitHub" } },
      { id: "branch-merge", text: { zh: "在分支上做一次修改并合并回 main", en: "Make a change on a branch and merge it back into main" } },
      { id: "readme", text: { zh: "写 README：照片、接线说明、以及“什么坏了、怎么修好的”一段", en: "Write a README with a photo, a wiring description and a “what broke and how I fixed it” paragraph" } },
    ],
  },
];

const month2Lessons: Lesson[] = [
  {
    slug: "arduino-io",
    title: { zh: "Arduino 入门：数字/模拟 IO、PWM 与串口调试", en: "Arduino basics: digital & analog IO, PWM and serial debugging" },
    summary: {
      zh: "看懂 setup/loop，会读按键和电位器、用 PWM 调亮度，并把串口打印当成主要的调试工具。",
      en: "Understand setup/loop, read buttons and potentiometers, dim an LED with PWM, and make serial printing your main debugging tool.",
    },
    minutes: 150,
    objectives: [
      { zh: "能说清 setup() 与 loop() 各自做什么，以及一个只跑一次、另一个反复跑的原因。", en: "Explain what setup() and loop() do and why one runs once while the other repeats." },
      { zh: "能不看资料用 INPUT_PULLUP 接好按键，并说出按下与松开时 digitalRead() 分别返回 LOW 还是 HIGH。", en: "Wire a button with INPUT_PULLUP and state what digitalRead() returns when pressed and released." },
      { zh: "能用 V = raw × 5.0 / 1023 把 ADC 原始值换算成电压，并解释为什么必须写成 5.0。", en: "Convert a raw ADC reading to volts with V = raw × 5.0 / 1023 and explain why 5.0 is required." },
      { zh: "能计算 PWM 的占空比与平均电压（例如 analogWrite(9, 191) 得到 3.75 V），并在串口绘图器里画出一行 name:value 输出。", en: "Calculate PWM duty cycle and average voltage, e.g. analogWrite(9, 191) giving 3.75 V, and plot a serial line in the Serial Plotter." },
    ],
    prereqs: ["ohms-law", "components"],
    resources: ["mcwhorter", "arduino-examples", "arduino-docs", "wokwi", "tinkercad"],
    tasks: [
      { id: "blink-sim", text: { zh: "在 Wokwi 或真板上跑通 Blink，并把闪烁周期改成 200 ms 亮 / 800 ms 灭", en: "Run Blink in Wokwi or on a real board, then change it to 200 ms on / 800 ms off" } },
      { id: "button-pullup", text: { zh: "用 INPUT_PULLUP 接一个按键，按下时点亮 LED，并在串口打印状态变化", en: "Wire a button with INPUT_PULLUP, light the LED while pressed and print each state change to serial" } },
      { id: "pot-pwm", text: { zh: "用电位器（analogRead）控制 LED 亮度（analogWrite），在串口绘图器里看曲线", en: "Control LED brightness (analogWrite) from a potentiometer (analogRead) and watch it in the Serial Plotter" } },
      { id: "falstad-pwm", text: { zh: "在本页 Falstad 中改变 PWM 占空比，确认平均电压 = 占空比 × 5 V", en: "Change the PWM duty in the Falstad embed and confirm average voltage = duty × 5 V" } },
    ],
  },
  {
    slug: "timing-interrupts",
    title: { zh: "非阻塞计时、中断与按键消抖", en: "Non-blocking timing, interrupts & debouncing" },
    summary: {
      zh: "用 millis() 代替 delay() 同时做好几件事，学会中断和消抖，做出一个反应时间小游戏。",
      en: "Replace delay() with millis() so one loop does many things, learn interrupts and debouncing, and build a reaction-timer game.",
    },
    minutes: 180,
    objectives: [
      { zh: "能用 0.5 m/s 行驶时 delay(1000) 让机器人盲开 50 cm 的例子，解释 delay() 为什么对机器人有害。", en: "Explain why delay() harms a robot, using the example of 0.5 m/s speed and 1000 ms of delay costing 50 cm." },
      { zh: "能凭记忆写出 millis() 模式（含 last += PERIOD），并解释 49.7 天回绕后 now - last 为什么仍然正确。", en: "Write the millis() pattern from memory with last += PERIOD, and explain why now - last survives the 49.7-day wrap." },
      { zh: "能解释触点弹跳，并为一个具体按键选出合理的消抖时间（如轻触按键 10–30 ms）。", en: "Explain contact bounce and choose a sensible debounce time for a given button, such as 10–30 ms." },
      { zh: "能把中断挂到 2 号引脚，并遵守 ISR 规矩：短小、不用 delay()、不用 Serial、共享变量加 volatile 并原子复制。", en: "Attach an interrupt to pin 2 and apply the ISR rules: short handler, no delay(), no Serial, volatile shared variables, atomic copies." },
    ],
    prereqs: ["arduino-io", "python-terminal"],
    resources: ["arduino-docs", "wokwi", "mcwhorter"],
    tasks: [
      { id: "two-blinks", text: { zh: "只用 millis()，让两个 LED 分别以 250 ms 和 400 ms 的周期独立闪烁", en: "Using only millis(), blink two LEDs independently at 250 ms and 400 ms periods" } },
      { id: "debounce-py", text: { zh: "运行本课的 Python 消抖模拟，把消抖时间改成 2 ms，观察误触发次数", en: "Run the lesson's Python debounce simulation, change the debounce time to 2 ms and count the false presses" } },
      { id: "reaction-timer", text: { zh: "完成反应时间游戏（随机延时、中断按键、串口输出毫秒数、抢按判犯规）", en: "Build the reaction-timer game (random delay, interrupt button, milliseconds to serial, early press = foul)" } },
      { id: "reaction-video", text: { zh: "录一段 15 秒的演示视频，连同代码推送到 GitHub", en: "Record a 15-second demo video and push it with the code to GitHub" } },
    ],
  },
  {
    slug: "esp32",
    title: { zh: "ESP32：Wi-Fi、3.3 V 逻辑与框架选择", en: "ESP32: Wi-Fi, 3.3 V logic & choosing a framework" },
    summary: {
      zh: "从 Uno 迁移到 ESP32：选对型号、避开引脚陷阱，在 Arduino / ESP-IDF / MicroPython 之间做选择，并用手机网页控制舵机。",
      en: "Move from the Uno to the ESP32: pick a variant, avoid the pin traps, choose between Arduino, ESP-IDF and MicroPython, and drive a servo from a phone web page.",
    },
    minutes: 180,
    objectives: [
      { zh: "能为项目挑选 ESP32 型号，并说明为什么课程主力是 S3、同时经典板仍值得备一块。", en: "Choose an ESP32 variant for a project and explain why the S3 is the main board while a classic board is still worth owning." },
      { zh: "能用上 1 kΩ、下 2 kΩ 的分压器把 5 V 信号降到 3.333 V，接进不耐 5 V 的 3.3 V 引脚。", en: "Make a 5 V signal safe for a 3.3 V pin with a 1 kΩ / 2 kΩ divider giving 3.333 V." },
      { zh: "能按 duty = pulse / period × 2^bits 算出 LEDC 占空比：50 Hz、14 位下 1.5 ms 脉冲对应 1228。", en: "Calculate an LEDC duty value with duty = pulse / period × 2^bits: 1.5 ms at 50 Hz and 14 bits gives 1228." },
      { zh: "能说出经典 ESP32 上要避开的引脚（GPIO 6–11、strapping 引脚 GPIO 0/2/5/12/15、开 Wi-Fi 时的 ADC2），并说明各自会出什么问题。", en: "Name the classic ESP32 pins to avoid — GPIO 6–11, strapping GPIO 0/2/5/12/15, ADC2 under Wi-Fi — and what each causes." },
    ],
    prereqs: ["arduino-io", "timing-interrupts"],
    resources: ["rnt-esp32", "arduino-esp32", "esp-idf", "dronebot-esp32", "esp32-s3-devkit", "esp32-classic", "wokwi"],
    tasks: [
      { id: "esp32-blink", text: { zh: "安装 ESP32 开发板支持包，上传 Blink，并在串口看到芯片型号", en: "Install the ESP32 board package, upload Blink and print the chip model to serial" } },
      { id: "servo-duty", text: { zh: "手算 50 Hz、14 位 LEDC 下 1.0 / 1.5 / 2.0 ms 脉宽对应的占空比数值", en: "Calculate the LEDC duty values for 1.0 / 1.5 / 2.0 ms pulses at 50 Hz and 14-bit resolution" } },
      { id: "web-servo", text: { zh: "完成网页舵机控制：手机打开 ESP32 网页，看到实时读数，并用按钮转动舵机", en: "Finish the web servo: open the ESP32 page on your phone, see the live reading and move the servo with buttons" } },
      { id: "pin-audit", text: { zh: "为你的板子列一张引脚表：哪些是启动绑定引脚、哪些 ADC 在 Wi-Fi 下不能用", en: "Write a pin table for your board: which pins are strapping pins and which ADC pins stop working with Wi-Fi" } },
    ],
  },
  {
    slug: "motors-drivers",
    title: { zh: "电机、驱动器与编码器闭环", en: "Motors, drivers & your first encoder loop" },
    summary: {
      zh: "认识四类执行器，理解 H 桥与续流二极管，选对驱动芯片，并用编码器让车轮精确转一整圈。",
      en: "Meet the four actuator types, understand H-bridges and flyback diodes, pick the right driver, and use an encoder to turn a wheel exactly one revolution.",
    },
    minutes: 210,
    objectives: [
      { zh: "能解释占空比不等于转速，并算出 60 % 占空比在 7.4 V 电池上给出 0.60 × 7.4 V = 4.44 V 平均电压。", en: "Explain why PWM duty is not speed, and calculate 0.60 × 7.4 V = 4.44 V average at 60 % duty." },
      { zh: "能画出 H 桥的四个状态（含刹车与滑行），并说明为什么弃用 L298N：它 2 V 的压降在 1 A 时变成 2.0 W 的热量。", en: "Draw the H-bridge's four states including brake and coast, and reject the L298N whose 2 V drop wastes 2.0 W as heat at 1 A." },
      { zh: "能解释电感反冲，并把续流二极管反向并联在线圈两端，阴极接正电源一侧。", en: "Explain inductive kickback and connect a flyback diode across a switched coil, cathode to the positive supply." },
      { zh: "能用编码器 CPR 与减速比算出每转车轮的计数（12 × 120 = 1440），并用 P 控制器把车轮转到恰好一圈。", en: "Compute counts per wheel revolution from CPR and gear ratio (12 × 120 = 1440) and turn a wheel exactly one revolution with a P controller." },
    ],
    prereqs: ["arduino-io", "timing-interrupts", "components"],
    resources: ["dronebot-l298n", "sparkfun-tb6612", "dronebot-stepper", "simplefoc", "drv8833", "tb6612-breakout", "romi-gearmotor-encoder", "a4988", "sts3215"],
    tasks: [
      { id: "falstad-kick", text: { zh: "在 Falstad 中对比有无续流二极管时，断开电感瞬间的电压尖峰", en: "In Falstad, compare the voltage spike when an inductor is switched off with and without a flyback diode" } },
      { id: "five-speeds", text: { zh: "用 PWM 让一个直流电机正反转、各跑五档速度，记录每档的实际转速", en: "Drive a DC motor forward and back at five PWM speeds and record the actual speed at each" } },
      { id: "loop-sim", text: { zh: "运行本课的 Python 闭环模拟，比较开环定时和编码器闭环在不同电池电压下的结果", en: "Run the lesson's Python loop simulation and compare timed open loop vs encoder closed loop at different battery voltages" } },
      { id: "one-rev", text: { zh: "在真车轮上实现“恰好转一圈”函数，并在两种电池电压下验证", en: "Implement “turn exactly one revolution” on a real wheel and check it at two battery voltages" } },
    ],
  },
  {
    slug: "sensors-fusion",
    title: { zh: "传感器、I2C 与互补滤波", en: "Sensors, I2C & the complementary filter" },
    summary: {
      zh: "只看数据手册接好并读取 I2C 传感器，理解陀螺仪漂移和加速度计噪声，用四行互补滤波得到稳定的倾角。",
      en: "Wire and read an I2C sensor from its datasheet, understand gyro drift and accelerometer noise, and get a stable tilt angle from a four-line complementary filter.",
    },
    minutes: 210,
    objectives: [
      { zh: "能用 I2C 扫描器找到新器件，并解释返回 0 表示器件已经应答。", en: "Find an I2C device with the scanner and explain that a return value of 0 means the device acknowledged." },
      { zh: "能按数据手册灵敏度把 MPU-6050 原始寄存器换算成 g 与 °/s：16384 LSB/g、131 LSB/(°/s)。", en: "Convert raw MPU-6050 registers to g and °/s using the datasheet sensitivity of 16384 LSB/g and 131 LSB per °/s." },
      { zh: "能凭记忆写出互补滤波，并为给定采样率选择 α，用 τ = α × dt / (1 − α) = 0.49 s（100 Hz、α = 0.98）核算时间常数。", en: "Write the complementary filter from memory and pick α for a sample rate, using τ = α × dt / (1 − α) = 0.49 s at 100 Hz." },
      { zh: "能在开机时静止平均 100–200 个采样测出陀螺仪零偏，并在积分前把它减掉。", en: "Measure the gyro bias at startup by averaging 100–200 stationary samples and subtract it before integrating." },
    ],
    prereqs: ["arduino-io", "timing-interrupts"],
    resources: ["arduino-docs", "labbe-kalman", "mathworks-fusion", "adafruit-bno085", "wokwi"],
    tasks: [
      { id: "i2c-scan", text: { zh: "运行 I2C 扫描程序，找到你的 IMU 地址，并读出 WHO_AM_I 寄存器", en: "Run the I2C scanner, find your IMU's address and read its WHO_AM_I register" } },
      { id: "raw-to-units", text: { zh: "只靠数据手册把原始加速度/陀螺仪读数换算成 g 和 °/s", en: "Convert raw accel/gyro readings to g and °/s using only the datasheet" } },
      { id: "drift-sim", text: { zh: "运行本课的 Python 漂移模拟，把 a 改成 0.90 和 0.995，比较噪声和漂移", en: "Run the lesson's Python drift simulation with a = 0.90 and 0.995 and compare noise vs drift" } },
      { id: "imu-filter", text: { zh: "在真 IMU 上打印俯仰角：先纯陀螺积分看漂移，再加互补滤波看漂移消失", en: "Print pitch from a real IMU: integrate the gyro alone and watch it drift, then add the complementary filter and watch the drift vanish" } },
    ],
  },
  {
    slug: "first-robots",
    title: { zh: "你的前两台机器人：循线小车与自平衡车", en: "Your first two robots: line follower & self-balancer" },
    summary: {
      zh: "把前五课合成一个闭环：用 P 再加 D 调好循线小车，再挑战只有滤波和循环时序都对才能站住的自平衡车。",
      en: "Put the first five lessons into one closed loop: tune a line follower with P then D, then take on a balancer that only stands when both the filter and the loop timing are right.",
    },
    minutes: 240,
    objectives: [
      { zh: "能以 error = setpoint − measurement 为基础，用机器人实际表现讲清 P、I、D 三个项各自的作用。", en: "Explain P, I and D from what the robot actually did when you changed each gain, starting from error = setpoint − measurement." },
      { zh: "能先用纯 P 调好循线小车，再加入 D，并为每次尝试记录 KP、KD 与 BASE_PWM。", en: "Tune the line follower with P only, then add D, and log KP, KD and BASE_PWM for every attempt." },
      { zh: "能用 micros() 把自平衡车的控制循环固定在 200 Hz，配互补滤波与 40° 倾角断电保护。", en: "Run the balancer at a fixed 200 Hz using micros(), with a complementary filter and a 40° cut-off that stops the motors." },
      { zh: "能把两台机器人放到 GitHub，并写上 README、调参日志以及出过的故障及其原因的记录。", en: "Put both robots on GitHub with a README, a tuning log and a record of each failure and its cause." },
    ],
    prereqs: ["sensors-fusion", "motors-drivers"],
    resources: ["romi-chassis", "qtr-8rc", "tb6612-breakout", "drv8833", "romi-gearmotor-encoder", "esp32-s3-devkit", "labbe-kalman"],
    tasks: [
      { id: "pd-sim", text: { zh: "运行本课的循线 Python 模拟，比较 P 和 PD 的过冲与振荡", en: "Run the lesson's line-follower Python simulation and compare overshoot and oscillation for P vs PD" } },
      { id: "line-follower", text: { zh: "搭好循线小车，先只用 P 调参，再加入 D，两个版本都录视频", en: "Build the line follower, tune it with P only, then add D, and film both versions" } },
      { id: "balancer", text: { zh: "搭自平衡车：固定频率控制循环、互补滤波、倾角过大自动断电", en: "Build the balancer: fixed-rate control loop, complementary filter, motor cut-off on large tilt" } },
      { id: "writeup", text: { zh: "在 GitHub 上为两台机器人写 README：接线、代码、调参过程和出过的故障", en: "Write a GitHub README for both robots: wiring, code, tuning notes and what broke" } },
      { id: "outer-loop", text: { zh: "选做挑战：给平衡车加一个外环速度控制（编码器测速 → 调整倾角设定值），60 s 内不溜走、轻推后能回来", en: "Optional challenge: add an outer speed loop to the balancer (encoder speed → angle setpoint) so it stays put for 60 s and recovers from a gentle push" } },
    ],
  },
];

const month3Lessons: Lesson[] = [
  {
    slug: "cad-parametric",
    title: { zh: "CAD：选好工具，用参数设计", en: "CAD: pick a tool, then design with parameters" },
    summary: {
      zh: "选一个 CAD 工具深入下去：完全约束的草图、参数驱动的尺寸、照数据手册建模，以及 STEP 和 STL 的区别。",
      en: "Pick one CAD tool and go deep: fully constrained sketches, parameters that drive every size, modelling from the datasheet, and STEP versus STL.",
    },
    minutes: 150,
    objectives: [
      { zh: "能用 cut_l = servo_l + 2 * clearance 计算派生切口尺寸（22.2 mm + 2 * 0.4 mm = 23.0 mm）。", en: "Compute a derived cut-out with cut_l = servo_l + 2 * clearance (22.2 mm + 2 * 0.4 mm = 23.0 mm)." },
      { zh: "能把四条线组成的矩形草图约束到 0 DOF，从 8 DOF 起逐步加约束与尺寸。", en: "Constrain a four-line rectangle sketch to 0 DOF, counting down from 8 DOF with constraints and dimensions." },
      { zh: "能用卡尺测孔距：外到外减一个孔径（29.5 mm − 2.0 mm = 27.5 mm）。", en: "Measure hole spacing from calipers as outside-to-outside minus one hole diameter (29.5 mm − 2.0 mm = 27.5 mm)." },
      { zh: "能解释为什么需要修改孔径的协作者必须拿到 STEP 文件，而 STL 只是不可再参数化的三角网格。", en: "Explain why a collaborator who must change a hole size needs the STEP file, while STL is a triangle mesh with no editable features." },
    ],
    prereqs: [],
    resources: ["onshape-free", "onshape-learn", "fusion-personal", "pdo-fusion30", "freecad", "mangojelly", "solidworks-makers", "openscad"],
    tasks: [
      { id: "pick-tool", text: { zh: "选定一个 CAD 工具，完成它的入门课程（Onshape 基础课或 30 天 Fusion 的前 5 天）", en: "Pick one CAD tool and finish its starter course (Onshape Fundamentals or the first 5 days of Fusion in 30 Days)" } },
      { id: "constrained", text: { zh: "画一个完全约束（0 自由度）的草图，尺寸都从基准标注", en: "Draw a fully constrained (0 DOF) sketch with every dimension taken from a datum" } },
      { id: "measure-servo", text: { zh: "用卡尺测量你自己的舵机（机身、安装耳宽度、孔距），和数据手册对比并记录差异", en: "Measure your own servo with calipers (body, tab span, hole spacing), compare with the datasheet and log the differences" } },
      { id: "bracket", text: { zh: "按数据手册和实测尺寸建一个参数化舵机支架，导出 STEP 和 STL", en: "Model a parametric servo bracket from the datasheet and your measurements; export STEP and STL" } },
    ],
  },
  {
    slug: "fdm-printing",
    title: { zh: "3D 打印：材料、校准与公差", en: "3D printing: materials, calibration & tolerances" },
    summary: {
      zh: "选打印机和耗材，按顺序校准，测出你机器的真实间隙，再为 FDM 设计零件：方向、悬垂、层间结合和能反复扣合的卡扣。",
      en: "Choose a printer and filament, calibrate in the right order, measure your machine's real clearances, then design for FDM: orientation, overhangs, layer adhesion and snap-fits that click.",
    },
    minutes: 180,
    objectives: [
      { zh: "能把测试件的总差值换算成每侧间隙（0.3 mm / 2 = 0.15 mm），再填入 CAD 参数。", en: "Convert a gauge's total difference into per-side clearance (0.3 mm / 2 = 0.15 mm) before setting CAD parameters." },
      { zh: "能算出自由转动孔的孔径：轴径加两倍每侧间隙（5 mm + 2 × 0.2 mm = 5.4 mm）。", en: "Compute a free-turning hole as shaft diameter plus twice the per-side clearance (5 mm + 2 × 0.2 mm = 5.4 mm)." },
      { zh: "能用 ε = 1.5 × y × t / L² 评估悬臂卡扣应变（L = 10、t = 1.2、y = 0.8 mm 得 1.44 %）。", en: "Evaluate cantilever snap strain with ε = 1.5 × y × t / L² (L = 10, t = 1.2, y = 0.8 mm gives 1.44 %)." },
      { zh: "能按载荷与温度选材料：PLA 约 55–60 °C 软化，贴 70 °C 电机的安装座应选 ABS 或 ASA。", en: "Choose filament from load and heat: PLA softens around 55–60 °C, so a 70 °C motor mount needs ABS or ASA." },
    ],
    prereqs: ["cad-parametric"],
    resources: ["ender3-v3-se", "bambu-a1-mini", "bambu-a1", "creality-k1c", "bambu-p1s", "orca-calibration", "teachingtech-calibration", "cnc-kitchen", "tolerance-gauge", "hubs-dfam", "fablabs", "library-makerspace", "craftcloud", "jlc3dp"],
    tasks: [
      { id: "calibrate", text: { zh: "按 OrcaSlicer 的顺序完成温度、流量和回抽校准，把结果记在打印日志里", en: "Run temperature, flow and retraction calibration in OrcaSlicer's order and record the results in a print log" } },
      { id: "gauge", text: { zh: "打印公差测试件，写下你机器的滑配和压配间隙", en: "Print the tolerance gauge and write down your machine's sliding-fit and press-fit clearances" } },
      { id: "snap-calc", text: { zh: "用本课的卡扣公式检查一根悬臂卡扣，再打印一根测试臂扣 20 次", en: "Check a cantilever snap arm with this lesson's formula, then print a test arm and snap it 20 times" } },
      { id: "enclosure", text: { zh: "设计并打印一个不用胶水就能扣紧的两件式 ESP32 外壳，反复迭代直到扣合清脆", en: "Design and print a two-part ESP32 enclosure that closes without glue; iterate until it clicks properly" } },
    ],
  },
  {
    slug: "transmissions",
    title: { zh: "传动与回差：齿轮、皮带与轴承", en: "Transmissions & backlash: gears, belts and bearings" },
    summary: {
      zh: "减速比怎样用速度换扭矩，回差为什么会毁掉定位精度而软件补不回来，以及轴承预紧、皮带与直驱的取舍。",
      en: "How a gear ratio trades speed for torque, why backlash ruins position accuracy in a way software cannot fully fix, and choosing bearings, preload, belts or direct drive.",
    },
    minutes: 150,
    objectives: [
      { zh: "能计算输出扭矩 = 电机扭矩 × n × 效率（0.1 N·m × 10 × 0.9 = 0.9 N·m）。", en: "Calculate output torque as motor torque × n × efficiency (0.1 N·m × 10 × 0.9 = 0.9 N·m)." },
      { zh: "能验算行星装配规则：行星轮 = (齿圈 − 太阳轮)/2 为整数齿数，且 (太阳轮 + 齿圈)/N 为整数。", en: "Check planetary assembly rules: planet = (ring − sun)/2 is a whole tooth count and (sun + ring)/N is a whole number." },
      { zh: "能把关节回差换算成末端误差：弧长 = 臂长 × 角度弧度（0.40 m 臂上 1.5° = 10.5 mm）。", en: "Convert joint backlash to tip error with arc = reach × angle in radians (1.5° on a 0.40 m arm = 10.5 mm)." },
      { zh: "能解释反向拖动：摩擦按 n、转子惯量按 n² 放大，345:1 的惯量感是 147:1 的 5.51 倍。", en: "Explain backdriving: friction scales with n and rotor inertia with n², so 345:1 feels 5.51× the inertia of 147:1." },
    ],
    prereqs: ["fdm-printing"],
    resources: ["opencycloid", "sts3215"],
    tasks: [
      { id: "ratio-calc", text: { zh: "用本课的脚本设计一个能装配的行星级（齿数、行星数、减速比）", en: "Use the lesson's script to design a planetary stage that assembles (teeth, planet count, ratio)" } },
      { id: "reducer", text: { zh: "为步进电机或玩具电机设计并打印一个行星或摆线减速器", en: "Design and print a planetary or cycloidal reducer for a NEMA17 stepper or a hobby motor" } },
      { id: "measure-backlash", text: { zh: "夹住输入轴、来回摇动输出，用指针量出回差（度），改进设计后再测一次", en: "Lock the input, rock the output and measure the backlash in degrees with a pointer; redesign and measure again" } },
    ],
  },
  {
    slug: "pid-control",
    title: { zh: "PID 与控制：积分饱和与串级回路", en: "PID & control: windup and cascade loops" },
    summary: {
      zh: "把 PID 补完整：积分消除稳态误差、微分阻尼、积分饱和与抗饱和；然后用串级外环让第 2 个月的平衡车停在原地。",
      en: "Finish PID properly: I for steady error, D for damping, windup and anti-windup; then add a cascade outer loop that keeps Month 2's balancer in one place.",
    },
    minutes: 180,
    objectives: [
      { zh: "能预测纯 P 的稳态误差 = 负载 / Kp（0.227 N·m / 0.05 N·m 每度 = 4.5°）。", en: "Predict P-only steady error as load divided by Kp (0.227 N·m / 0.05 N·m per degree = 4.5°)." },
      { zh: "能通过只在输出未饱和时积分来防止积分饱和（Ki 0.4 超调：8.9° 对 39.0°）。", en: "Prevent integral windup by integrating only while the output is unsaturated (Ki 0.4 overshoot: 8.9° vs 39.0°)." },
      { zh: "能对测量值而不是误差求微分，避免目标阶跃产生微分冲击。", en: "Differentiate the measurement rather than the error to avoid a derivative kick when the target steps." },
      { zh: "能配置串级回路：内环 200 Hz PD、外环 25 Hz PI，设定点限制在 ±3°。", en: "Configure a cascade with inner 200 Hz PD, outer 25 Hz PI and the setpoint clamped to ±3°." },
    ],
    prereqs: ["first-robots", "transmissions", "timing-interrupts"],
    resources: ["mathworks-pid", "beauregard-pid"],
    tasks: [
      { id: "pid-sim", text: { zh: "运行本课的关节 PID 模型，自己改增益，找出有/无抗饱和时超调的差别", en: "Run the lesson's joint PID model, change the gains yourself and find the overshoot difference with and without anti-windup" } },
      { id: "cascade-sim", text: { zh: "运行串级平衡车模型，复现“只有内环会溜走、PI 外环能停住”的结果", en: "Run the cascade balancer model and reproduce: inner loop alone runs away, an outer PI loop holds it" } },
      { id: "cascade-robot", text: { zh: "给你的平衡车加上外环：60 s 内离起点不超过一圈轮子，轻推后能回来", en: "Add the outer loop to your balancer: within one wheel turn of the start for 60 s, and back after a gentle push" } },
      { id: "tuning-log", text: { zh: "在调参日志里分开记录内环和外环的增益，并用自己的话解释串级", en: "Log the inner and outer gains separately and explain the cascade in your own words" } },
    ],
  },
  {
    slug: "so101-arm",
    title: { zh: "组装 SO-101 机械臂：校准与遥操作", en: "Build the SO-101 arm: calibrate and teleoperate" },
    summary: {
      zh: "选购买方式，组装主从两只臂，读懂总线舵机的数据包，按 LeRobot 的步骤设置 ID、校准，再用主臂遥控从臂。",
      en: "Choose how to buy it, build the leader and follower arms, read the bus-servo packets, then set IDs, calibrate and teleoperate with LeRobot.",
    },
    minutes: 240,
    objectives: [
      { zh: "能构造 STS 数据包并用 CHECKSUM = ~(ID + LENGTH + INSTRUCTION + PARAMS) & 0xFF 校验。", en: "Build an STS packet and verify its checksum with CHECKSUM = ~(ID + LENGTH + INSTRUCTION + PARAMS) & 0xFF." },
      { zh: "能把舵机回报的步数换算成角度：编码器每圈 4096 步（1024 步 = 90°）。", en: "Convert a reported position in steps to degrees with the 4096-step encoder (1024 steps = 90°)." },
      { zh: "能逐个连接舵机并设置 ID 1–6，因为每只新舵机出厂都响应 ID 1。", en: "Set servo IDs 1–6 one motor at a time because every new servo answers to ID 1." },
      { zh: "能用 lerobot-calibrate 校准两条臂，并用 lerobot-teleoperate 遥操作从臂跟随主臂。", en: "Calibrate both arms with lerobot-calibrate and teleoperate the follower with lerobot-teleoperate." },
    ],
    prereqs: ["python-terminal", "git-github", "transmissions"],
    resources: ["so-arm100", "lerobot-so101", "seeed-so101-pro", "seeed-so101-printed", "robonine-so101", "wowrobo-so101", "eezybotarm", "xarm-1s", "mujoco", "sts3215"],
    tasks: [
      { id: "buy-plan", text: { zh: "按你的预算选一条路线（MuJoCo、单从臂、整套主从），写下总价和理由", en: "Choose a route for your budget (MuJoCo, single follower, full pair) and write down the total and why" } },
      { id: "packets", text: { zh: "运行本课的数据包脚本，手算一个校验和并和输出对照", en: "Run the lesson's packet script and work out one checksum by hand to match it" } },
      { id: "build-calibrate", text: { zh: "组装两只臂，设置舵机 ID 1–6，用 lerobot-calibrate 校准主臂和从臂", en: "Build both arms, set servo IDs 1–6, and calibrate leader and follower with lerobot-calibrate" } },
      { id: "teleop", text: { zh: "用 lerobot-teleoperate 让从臂跟随主臂，录一段视频", en: "Teleoperate the follower from the leader with lerobot-teleoperate and film it" } },
    ],
  },
  {
    slug: "gripper-fingers",
    title: { zh: "设计你自己的夹爪手指（TPU）", en: "Design your own gripper fingers (TPU)" },
    summary: {
      zh: "用摩擦力算出夹多紧才够，用鳍条结构让手指包住物体，用 TPU 打印并在三种不同形状的物体上测试，最后完成本月的机械臂改造。",
      en: "Work out how hard to squeeze from friction, use a fin-ray structure so fingers wrap around objects, print them in TPU and test them on three differently shaped objects, finishing the month's arm modification.",
    },
    minutes: 180,
    objectives: [
      { zh: "能用 F = S × m × (g + a) / (2 × μ) 计算最小夹持力（60 g 鸡蛋配 TPU ≈ 1.0 N）。", en: "Calculate minimum squeeze force with F = S × m × (g + a) / (2 × μ) (60 g egg on TPU ≈ 1.0 N)." },
      { zh: "能用倾斜木板法测摩擦系数：物体刚开始滑动时 μ = tan(角度)。", en: "Measure the friction coefficient with a tilted board until the object slides, using μ = tan(angle)." },
      { zh: "能用 OpenSCAD 参数化设计鳍条手指，调整侧壁厚度、肋条数量与肋条倾角。", en: "Design a parametric fin-ray finger in OpenSCAD, varying flank thickness, rib count and rib tilt." },
      { zh: "能按三物体测试流程评估抓取：每种 10 次，抬起 10 cm 并保持 5 s 才算成功。", en: "Run the three-object grasp test: 10 grasps each, success only if lifted 10 cm and held 5 s." },
    ],
    prereqs: ["cad-parametric", "fdm-printing", "so101-arm"],
    resources: ["so101-compliant-gripper", "so-arm100", "cnc-kitchen"],
    tasks: [
      { id: "friction", text: { zh: "用斜板法测出 PLA 和 TPU 在你的物体上的摩擦系数，算出需要的夹紧力", en: "Measure PLA and TPU friction on your objects with a tilted board and work out the squeeze force needed" } },
      { id: "test-finger", text: { zh: "打印本课的参数化鳍条手指，改一个参数（肋数或壁厚）再打一次，比较它们怎样弯", en: "Print the lesson's parametric fin-ray finger, change one parameter (rib count or flank) and compare how they bend" } },
      { id: "own-fingers", text: { zh: "基于 SO-101 的 STEP 文件设计你自己的 TPU 手指并装上机械臂", en: "Design your own TPU fingers from the SO-101 STEP files and fit them to the arm" } },
      { id: "three-objects", text: { zh: "在三种不同形状的物体上测试（各 10 次），记录成功率并和原装夹爪对比", en: "Test on three differently shaped objects (10 tries each), log the success rate and compare with the stock gripper" } },
    ],
  },
];

const month4Lessons: Lesson[] = [
  {
    slug: "ros2-setup",
    title: { zh: "选哪个 ROS 2，搭好第一个工作空间", en: "Which ROS 2, and your first workspace" },
    summary: {
      zh: "为什么从 Jazzy 开始、怎样一眼认出过时的 ROS 1 教程、四种安装方式，然后用 colcon 构建并运行你的第一个 ROS 2 包。",
      en: "Why to start on Jazzy, how to spot an outdated ROS 1 tutorial at a glance, four ways to install, then build and run your first ROS 2 package with colcon.",
    },
    minutes: 150,
    objectives: [
      { zh: "能解释为何从 Jazzy 开始（LTS 支持到 2029 年 5 月），并识别 roscore、catkin_make 等 ROS 1 命令。", en: "Explain why Jazzy is the starting distro (LTS until May 2029) and recognise ROS 1 commands such as roscore and catkin_make." },
      { zh: "能用任一受支持的路线安装 ROS 2 Jazzy，并通过运行 C++ talker 与 Python listener 验证安装。", en: "Install ROS 2 Jazzy by one supported route and verify it by running the C++ talker and Python listener." },
      { zh: "能创建 m4_hello 包，用 colcon 构建，运行 2 Hz 的 hello_node，并用 ros2 node/topic 命令检查它。", en: "Create the m4_hello package, build it with colcon, run hello_node at 2 Hz, and inspect it with ros2 node and topic commands." },
      { zh: "能诊断四类常见安装错误：未 source、在 src/ 内构建、混用发行版、ROS_DOMAIN_ID 不一致。", en: "Diagnose four common setup failures: missing source, building inside src/, mixed distros and mismatched ROS_DOMAIN_ID." },
    ],
    prereqs: [],
    resources: ["ros2-tutorials", "the-construct", "robostack"],
    tasks: [
      { id: "install", text: { zh: "装好 ROS 2 Jazzy（任选一种方式），跑通 C++ talker 和 Python listener", en: "Install ROS 2 Jazzy (any route) and get the C++ talker and Python listener talking" } },
      { id: "spot-ros1", text: { zh: "找三篇搜索排名靠前的 ROS 教程，按本课的特征判断哪些是 ROS 1，记下线索", en: "Find three top-ranked ROS tutorials, decide which are ROS 1 using this lesson's tell-tale signs, and note the clue" } },
      { id: "workspace", text: { zh: "创建 ~/ros2_ws，用 ros2 pkg create 生成一个 Python 包，写一个用定时器发布消息的节点", en: "Create ~/ros2_ws, generate a Python package with ros2 pkg create, and write a node that publishes on a timer" } },
      { id: "inspect", text: { zh: "用 ros2 node list、topic list、topic echo 和 topic hz 检查你的节点，确认发布频率", en: "Inspect your node with ros2 node list, topic list, topic echo and topic hz, and confirm its rate" } },
    ],
  },
  {
    slug: "ros2-graph",
    title: { zh: "节点、话题、服务与动作", en: "Nodes, topics, services and actions" },
    summary: {
      zh: "不用机器人、不用仿真器，搭一个完整的多节点系统：自定义 msg/srv/action、Python 和 C++ 节点、参数与 YAML、带参数的 launch 文件、ros2 bag 录制回放，以及“发了却收不到”的 QoS 问题。",
      en: "A complete multi-node system with no robot and no simulator: your own msg/srv/action, Python and C++ nodes, parameters and YAML, a launch file with arguments, recording and replaying with ros2 bag, and the QoS mismatch behind “it publishes but nothing receives”.",
    },
    minutes: 240,
    objectives: [
      { zh: "能为连续数据选择 topic、为即时请求选择 service、为需要反馈或取消的任务选择 action。", en: "Choose a topic for continuous data, a service for an immediate request, and an action for work needing feedback or cancellation." },
      { zh: "能编写 .msg、.srv、.action 文件，并用 rosidl_generate_interfaces 生成 C++ 与 Python 代码。", en: "Write .msg, .srv and .action files and generate C++ and Python code with rosidl_generate_interfaces." },
      { zh: "能实现指数滑动平均 y ← y + α(x − y)，并在参数回调中拒绝 (0, 1] 之外的 α。", en: "Implement an exponential moving average y ← y + α(x − y), and reject α outside (0, 1] in a parameter callback." },
      { zh: "能用参数与重映射启动整张图，用 ros2 bag 录制并回放 /raw 与 /filtered，并诊断 QoS 不兼容。", en: "Launch the graph with arguments and remappings, record and replay /raw and /filtered with ros2 bag, and diagnose QoS mismatches." },
    ],
    prereqs: ["ros2-setup"],
    resources: ["ros2-tutorials", "renard-ros2-l1", "articulated-robotics", "mogi-ros", "automatic-addison", "ros2-qos"],
    tasks: [
      { id: "pick-pipe", text: { zh: "为你设想的机器人列出 6 种数据流，每种判断该用话题、服务还是动作，写下理由", en: "List six data flows for a robot you have in mind and decide topic, service or action for each, with the reason" } },
      { id: "interfaces", text: { zh: "建一个接口包，至少包含一个自定义 .msg 和一个 .srv，用 ros2 interface show 检查", en: "Create an interfaces package with at least one custom .msg and one .srv, and check them with ros2 interface show" } },
      { id: "graph", text: { zh: "搭出本课的四节点系统（传感器、处理、配置服务、带参数的汇总），其中至少一个节点用 C++", en: "Build this lesson's four-node system (sensor, processing, configuration service, parameterised aggregator), with at least one node in C++" } },
      { id: "launch", text: { zh: "写一个带参数的 Python launch 文件，用参数改变频率并重映射一个话题", en: "Write a Python launch file with arguments; use them to change a rate and remap a topic" } },
      { id: "bag", text: { zh: "用 ros2 bag 录一段数据，再把它回放给单独运行的处理节点", en: "Record a run with ros2 bag and replay it into the processing node running on its own" } },
      { id: "qos", text: { zh: "故意制造一次 QoS 不兼容，读懂警告，再修好它", en: "Cause a QoS mismatch on purpose, read the warning, then fix it" } },
    ],
  },
  {
    slug: "urdf-tf",
    title: { zh: "URDF 与 TF：描述一台机器人", en: "URDF and TF: describing a robot" },
    summary: {
      zh: "用 xacro 写出自己的机器人：差速底盘、传感器桅杆和二自由度云台，惯量正确，视觉与碰撞几何分开；再用 robot_state_publisher、RViz 和 tf2 工具看懂并诊断 TF 树。",
      en: "Write your own robot in xacro: a differential-drive base, a sensor mast and a two-DOF pan-tilt head, with correct inertias and separate visual and collision geometry; then read and diagnose its TF tree with robot_state_publisher, RViz and the tf2 tools.",
    },
    minutes: 240,
    objectives: [
      { zh: "能写出带命名属性与轮子宏的 xacro 描述，并正确使用 fixed、continuous、revolute 关节。", en: "Write a xacro description with named properties and a wheel macro, using fixed, continuous and revolute joints." },
      { zh: "能计算长方体、圆柱、球体的惯量（底盘 Ixx = 0.010667 kg·m²），并用 inertia_check.py 验证。", en: "Calculate box, cylinder and sphere inertias (chassis Ixx = 0.010667 kg·m²) and verify them with inertia_check.py." },
      { zh: "能解释 robot_state_publisher 如何把 /joint_states 与 URDF 变成 /tf，并用 joints:=none 启动模型。", en: "Explain how robot_state_publisher turns /joint_states and the URDF into /tf, and launch the model with joints:=none." },
      { zh: "能算出 pan 30° 时 base_link→camera_link 为 [-0.043, 0.010, 0.305]，并用 tf2_echo 与 view_frames 诊断 TF 树断裂。", en: "Calculate base_link→camera_link at pan 30° as [-0.043, 0.010, 0.305], and diagnose TF tree breaks with tf2_echo and view_frames." },
    ],
    prereqs: ["ros2-setup", "ros2-graph"],
    resources: ["ar-transforms", "renard-ros2-l2", "urdf-rsp-tutorial"],
    tasks: [
      { id: "xacro", text: { zh: "用 xacro 写出你自己的机器人（不是 TurtleBot）：差速底盘、桅杆、云台，尺寸都用 property，轮子用宏", en: "Write your own robot in xacro (not TurtleBot): a differential-drive base, a mast and a pan-tilt head, with dimensions as properties and the wheels as a macro" } },
      { id: "inertia", text: { zh: "给每个有质量的连杆加上 inertial，并用 inertia_check.py 或手算核对至少一个", en: "Give every link with mass an inertial, and check at least one by hand or with inertia_check.py" } },
      { id: "sliders", text: { zh: "用 joint_state_publisher_gui 拖动云台关节，在 RViz 里看 TF 跟着动，截一张图", en: "Drive the pan-tilt joints with joint_state_publisher_gui, watch the TF move in RViz, and take a screenshot" } },
      { id: "tf-math", text: { zh: "手算云台转 30° 时 base_link → camera_link 的平移，再用 tf2_echo 核对", en: "Work out the base_link → camera_link translation with the head panned 30° by hand, then check it with tf2_echo" } },
      { id: "broken", text: { zh: "故意弄断 TF 树（不发 joint_states、用错 frame 名），读懂报错，再修好", en: "Break the TF tree on purpose (no joint_states, a wrong frame name), read the errors, then fix them" } },
    ],
  },
  {
    slug: "gazebo-sim",
    title: { zh: "仿真：把机器人放进 Gazebo", en: "Simulation: your robot in Gazebo" },
    summary: {
      zh: "理清 Gazebo 的命名历史和版本配对，选对仿真器（Gazebo、MuJoCo、Isaac Sim）；然后写一个带障碍物的 SDF 世界，把上一课的 xacro 机器人放进去，加上激光雷达和相机，通过 ros_gz_bridge 在 ROS 2 和 RViz 里看到传感器数据。",
      en: "Untangle Gazebo's naming history and version pairing and pick the right simulator (Gazebo, MuJoCo, Isaac Sim); then write an SDF world with obstacles, put last lesson's xacro robot into it with a lidar and a camera, and see the sensor data in ROS 2 and RViz through ros_gz_bridge.",
    },
    minutes: 240,
    objectives: [
      { zh: "能为 ROS 2 Jazzy 选择 Gazebo Harmonic，并识别 ign 或 gazebo_ros_pkgs 这类过时教程。", en: "Select Gazebo Harmonic for ROS 2 Jazzy and identify outdated ign or gazebo_ros_pkgs tutorials." },
      { zh: "能搭建带四个系统插件和静态障碍物的 SDF 世界，并算出红色方块前表面 1.80 m、墙内表面 2.95 m。", en: "Build an SDF world with the four system plugins and static obstacles, and compute the red-box face at 1.80 m and walls at 2.95 m." },
      { zh: "能配置 360 束、10 Hz 的 gpu_lidar 和 640×480 相机，把 gz_frame_id 设为 lidar_link 与 camera_optical_link，并用 ros_gz_bridge 桥接。", en: "Configure a 360-beam, 10 Hz gpu_lidar and a 640×480 camera with gz_frame_id lidar_link and camera_optical_link, then bridge them with ros_gz_bridge." },
      { zh: "能用 1.80 − 0.12 = 1.68 m 核对正前方扫描，并把相机图像与世界文件对照。", en: "Cross-check the straight-ahead scan with 1.80 − 0.12 = 1.68 m and compare the camera image against the world file." },
    ],
    prereqs: ["ros2-graph", "urdf-tf"],
    resources: ["gazebo-docs", "mujoco-sim", "isaac-sim"],
    tasks: [
      { id: "versions", text: { zh: "确认你的 ROS 2 发行版配哪个 Gazebo 版本，并找一篇用 gazebo_ros 或 ign gazebo 的过时教程", en: "Confirm which Gazebo release pairs with your ROS 2 distro, and find one outdated tutorial that uses gazebo_ros or ign gazebo" } },
      { id: "world", text: { zh: "写一个自己的 SDF 世界：地面、光照、四面墙和至少三个障碍物，不依赖在线模型", en: "Write your own SDF world: ground, light, four walls and at least three obstacles, with no downloaded models" } },
      { id: "sensors", text: { zh: "给你的 xacro 机器人加上激光雷达和相机插件，frame_id 用你 URDF 里的连杆名", en: "Add a lidar and a camera to your xacro robot, with frame_ids that are link names from your URDF" } },
      { id: "bridge", text: { zh: "用 ros_gz_bridge 把 /scan、/camera/image_raw、/odom、/cmd_vel 接进 ROS 2，在 RViz 里同时看到激光点和相机画面", en: "Bridge /scan, /camera/image_raw, /odom and /cmd_vel into ROS 2 and see the laser points and the camera image together in RViz" } },
      { id: "check", text: { zh: "手算机器人到正前方障碍物的距离，再用 scan_probe.py 核对；开一段距离后，用里程计和激光读数互相印证", en: "Work out the distance to the obstacle straight ahead by hand and check it with scan_probe.py; drive forward and check odometry and lidar against each other" } },
    ],
  },
  {
    slug: "ros2-control",
    title: { zh: "ros2_control：通过控制器驱动机器人", en: "ros2_control: driving through a controller" },
    summary: {
      zh: "把上一课的 Gazebo 驱动插件换成 ros2_control：在 xacro 里写 <ros2_control> 标签，用 YAML 配置 diff_drive_controller 和 joint_state_broadcaster，用键盘遥控；再写一个“开指定距离”的动作服务器，带反馈和取消；最后用 mock 硬件看清换成真机时到底换掉什么。",
      en: "Replace last lesson's Gazebo drive plugin with ros2_control: <ros2_control> tags in the xacro, diff_drive_controller and joint_state_broadcaster configured in YAML, keyboard teleop; then an action server that drives a commanded distance with feedback and cancellation; and mock hardware to see exactly what changes on a real robot.",
    },
    minutes: 240,
    objectives: [
      { zh: "能解释 update_rate 50 下每 20 ms 一次的 read-update-write 循环，以及为什么一个命令接口只能被一个控制器占用。", en: "Explain the read-update-write loop at update_rate 50 (every 20 ms) and why a command interface is claimed by one controller." },
      { zh: "能添加 <ros2_control> 标签和 controllers.yaml，使 wheel_separation 0.28 m 与 wheel_radius 0.05 m 和 URDF 一致。", en: "Add <ros2_control> tags and a controllers.yaml whose wheel_separation 0.28 m and wheel_radius 0.05 m match the URDF." },
      { zh: "能计算差速轮速：0.2 m/s 直行时两轮 4.0 rad/s，ω = 1.0 rad/s 时为 −2.8/+2.8 rad/s。", en: "Calculate differential-drive wheel speeds: 0.2 m/s straight gives 4.0 rad/s, and ω = 1.0 rad/s gives −2.8/+2.8 rad/s." },
      { zh: "能运行带反馈与取消的 DriveDistance 动作，把 0.997 m 的结果与里程计对照，并在 mock 硬件上重复。", en: "Run the DriveDistance action with feedback and cancellation, compare its 0.997 m result with odometry, and repeat on mock hardware." },
    ],
    prereqs: ["ros2-graph", "urdf-tf", "gazebo-sim"],
    resources: ["ros2-control-docs", "articulated-ros2-control-real", "articulated-robotics"],
    tasks: [
      { id: "tags", text: { zh: "给你的 xacro 机器人加上 <ros2_control> 标签：轮子用速度命令接口，并报告位置和速度状态接口", en: "Add <ros2_control> tags to your xacro robot: velocity command interfaces for the wheels, reporting position and velocity state interfaces" } },
      { id: "yaml", text: { zh: "用 YAML 配置 diff_drive_controller 和 joint_state_broadcaster，确认 list_controllers 里都是 active，轮距和轮半径与 URDF 一致", en: "Configure diff_drive_controller and joint_state_broadcaster in YAML; check that list_controllers shows them active and that wheel separation and radius match the URDF" } },
      { id: "teleop", text: { zh: "在 Gazebo 里用 teleop_twist_keyboard（stamped:=true）开车，松开按键后观察 cmd_vel_timeout 让机器人停下", en: "Drive in Gazebo with teleop_twist_keyboard (stamped:=true) and watch cmd_vel_timeout stop the robot when you let go" } },
      { id: "action", text: { zh: "写一个开指定距离的动作服务器：周期反馈进度、支持取消，结果报告机器人实际走了多远，并用里程计核对", en: "Write an action server that drives a commanded distance: progress feedback, cancellation, and a result that reports how far the robot really went, checked against odometry" } },
    ],
  },
  {
    slug: "slam-nav",
    title: { zh: "SLAM 与导航：SLAM Toolbox 和 Nav2", en: "SLAM and navigation: SLAM Toolbox and Nav2" },
    summary: {
      zh: "先用激光雷达检查里程计转弯是否准确并校准它；再用 SLAM Toolbox 边走边给房间建图、保存地图；最后在保存的地图里定位，让 Nav2 规划路径、绕开障碍、自己开到目标点，并学会从 TF 和代价地图里找出导航失败的原因。",
      en: "First use the lidar to check how well odometry measures turns, and calibrate it; then map the room with SLAM Toolbox while driving and save the map; finally localize in the saved map and let Nav2 plan a path, avoid obstacles and drive itself to a goal, and learn to find why navigation fails from TF and the costmaps.",
    },
    minutes: 240,
    objectives: [
      { zh: "能解释 map→odom→base_footprint 链：SLAM Toolbox 发布 map→odom，diff_drive_controller 发布轮式里程计。", en: "Explain the map→odom→base_footprint chain, with SLAM Toolbox publishing map→odom and diff_drive_controller publishing wheel odometry." },
      { zh: "能用 spin_check.py 校准里程计，按新倍率 = 旧倍率 × 里程计角度 ÷ 实际角度（1.0 × 360 ÷ 403.1 = 0.893）计算。", en: "Calibrate odometry with spin_check.py using new multiplier = old × odometry angle ÷ real angle (1.0 × 360 ÷ 403.1 = 0.893)." },
      { zh: "能按 0.05 m 分辨率配置 SLAM Toolbox，保存位姿图与 PGM，并用 map_check.py 核对地图。", en: "Configure SLAM Toolbox at 0.05 m resolution, save the pose graph and PGM, and verify the map with map_check.py." },
      { zh: "能发送 NavigateToPose 目标，按 xy_goal_tolerance 0.10 m 检查到达，并从 TF、代价地图与 /scan 诊断故障。", en: "Send a NavigateToPose goal, check arrival within xy_goal_tolerance 0.10 m, and diagnose failures from TF, costmaps and /scan." },
    ],
    prereqs: ["urdf-tf", "gazebo-sim", "ros2-control"],
    resources: ["slam-toolbox", "nav2-docs", "articulated-slam", "articulated-nav2"],
    tasks: [
      { id: "odom", text: { zh: "用 spin_check.py 让机器人按里程计原地转一整圈，用激光雷达测出真实转角，并校准 wheel_separation_multiplier，直到误差小于 1%", en: "Use spin_check.py to turn the robot one full turn by odometry, measure the real angle with the lidar, and calibrate wheel_separation_multiplier until the error is under 1%" } },
      { id: "map", text: { zh: "用 SLAM Toolbox 给房间建图，把所有障碍物都扫到，并同时保存位姿图（.posegraph）和栅格地图（.pgm + .yaml）", en: "Map the room with SLAM Toolbox until every obstacle shows, and save both the pose graph (.posegraph) and the occupancy grid (.pgm + .yaml)" } },
      { id: "nav", text: { zh: "在保存的地图里定位并启动 Nav2，从 RViz 或命令行发出目标点，让机器人绕过障碍物自己开过去", en: "Localize in the saved map, start Nav2 and send a goal from RViz or the command line; the robot must drive around the obstacles to it on its own" } },
      { id: "debug", text: { zh: "故意制造一次导航失败（如把目标放进障碍物，或停掉激光雷达），从日志、TF 和代价地图找出原因", en: "Make navigation fail on purpose (a goal inside an obstacle, or the lidar stopped) and find the cause from the logs, TF and the costmaps" } },
    ],
  },
];

const month5Lessons: Lesson[] = [
  {
    slug: "control-modelling",
    title: { zh: "控制理论：先建模，再看频域", en: "Control theory: model the plant, then read the loop" },
    summary: {
      zh: "PID 的基础在第 3 个月已经讲过，这里往深处走：给第 3 个月的机械臂关节建一个模型，用阶跃数据辨识出它的参数，写出传递函数；再用伯德图读出增益裕度和相位裕度，并在仿真里验证它们能预测超调和失稳。",
      en: "PID basics were Month 3; this goes deeper. Model Month 3's arm joint, identify its parameters from step data and write its transfer function; then read gain and phase margins off the loop's Bode data and check in simulation that they predict overshoot and instability.",
    },
    minutes: 240,
    objectives: [
      { zh: "能推出带重力前馈的传递函数 G(s) = 1/(J s² + B s)，指出极点 s = 0 与 −12.5 1/s，并算出时间常数 J/B = 0.08 s。", en: "Derive the gravity-feedforward plant G(s) = 1/(J s² + B s), its poles at s = 0 and −12.5 1/s, and the time constant J/B = 0.08 s." },
      { zh: "能把第 3 个月的增益换算成 SI 单位：0.05 N·m/度 变成 2.86 N·m/rad，0.002 N·m/(度/秒) 变成 0.115 N·m/(rad/s)。", en: "Convert Month 3's gains to SI: 0.05 N·m/deg becomes 2.86 N·m/rad and 0.002 N·m per deg/s becomes 0.115 N·m/(rad/s)." },
      { zh: "能用 0.2 N·m 的开环力矩阶跃辨识参数：B = 0.050 N·m/(rad/s)，J = 0.0040 kg·m²。", en: "Identify B and J from an open-loop 0.2 N·m torque step: B = 0.050 N·m per rad/s and J = 0.0040 kg·m²." },
      { zh: "能从 joint_freq.py 读出 34.6 rad/s 处的相位裕度 56° 与增益裕度 14.2 dB，并预测只用 P 时临界 kp ≈ 6.79。", en: "Read phase margin 56° at 34.6 rad/s and gain margin 14.2 dB from joint_freq.py, then predict the P-only loop's critical kp ≈ 6.79." },
    ],
    prereqs: ["pid-control", "so101-arm"],
    resources: ["ctms-frequency", "mathworks-control-practice"],
    tasks: [
      { id: "identify", text: { zh: "对一个真实电机（或本课模型）做开环阶跃，用终值和 63% 时间求出 B 和 J，写出它的传递函数", en: "Run an open-loop step on a real motor (or the lesson's model), get B and J from the final value and the 63 % time, and write its transfer function" } },
      { id: "units", text: { zh: "把你第 3 个月的 PID 增益换算成 SI 单位（每弧度），并说出每个增益的物理意义", en: "Convert your Month 3 PID gains to SI units (per radian) and say what each gain means physically" } },
      { id: "margins", text: { zh: "运行 joint_freq.py，读出相位裕度和增益裕度，并用增益裕度预测失稳的 kp", en: "Run joint_freq.py, read the phase and gain margins, and predict from the gain margin the kp at which the loop goes unstable" } },
      { id: "verify", text: { zh: "在时域里验证这个预测：取略低和略高于临界值的 kp，记录振荡是衰减还是增长，以及振荡频率", en: "Check the prediction in the time domain: one kp just below and one just above the limit, noting whether the ringing decays or grows and at what frequency" } },
    ],
  },
  {
    slug: "state-space-lqr",
    title: { zh: "状态空间、LQR 与 MPC", en: "State space, LQR and MPC" },
    summary: {
      zh: "把关节和倒立摆小车写成状态空间形式，用离散 Riccati 方程算出 LQR 增益，调 Q 和 R 看取舍，再放到完整的非线性模型上检验；最后用一个小 MPC 在力矩限制下移动关节，和输出被削顶的 LQR 比一比。",
      en: "Write the joint and a cart-pole in state space, get LQR gains from the discrete Riccati equation, trade Q against R and test the result on the full nonlinear model; then move the joint under a torque limit with a small MPC and compare it with LQR whose output is clipped.",
    },
    minutes: 240,
    objectives: [
      { zh: "能把关节和小车倒立摆写成状态空间 x' = A x + B u，为关节推出 A = [[0, 1], [0, −12.5]]、B = [[0], [250]]。", en: "Write the joint and cart-pole in state space x' = A x + B u, deriving A = [[0, 1], [0, −12.5]] and B = [[0], [250]] for the joint." },
      { zh: "能迭代离散 Riccati 方程求出 LQR 增益，并用 u = −K x、K = [−0.92, −1.75, −18.76, −3.03] 控制倒立摆。", en: "Compute LQR gains by iterating the discrete Riccati equation and apply u = −K x with K = [−0.92, −1.75, −18.76, −3.03]." },
      { zh: "能调整 Q 和 R 并解释取舍：把位置权重提到 100，最终位置降到 0.000 m，但峰值力升到 5.19 N。", en: "Tune Q and R and explain the trade-off: raising the position weight to 100 drops the final position to 0.000 m but raises peak force to 5.19 N." },
      { zh: "能在 0.6 N·m 力矩上限下对比削顶 LQR 与 MPC：超调 2.24° 对 0.86°，而 MPC 每步约需 12,000 次状态更新。", en: "Compare LQR with clipped output against MPC on the 0.6 N·m joint limit: overshoot 2.24° versus 0.86°, at about 12,000 state updates per step." },
    ],
    prereqs: ["control-modelling", "first-robots"],
    resources: ["underactuated-lqr", "mathworks-state-space"],
    tasks: [
      { id: "state-space", text: { zh: "自己推导倒立摆小车线性化后的 A 和 B，与 lqr_sim.py 打印的数值逐项核对", en: "Derive the cart-pole's linearised A and B yourself and check every entry against what lqr_sim.py prints" } },
      { id: "lqr", text: { zh: "运行 lqr_sim.py，至少再试两组自己的 Q 和 R，记录增益、峰值力和 4 s 后小车的位置", en: "Run lqr_sim.py and try at least two Q and R choices of your own; log the gains, the peak force and where the cart is after 4 s" } },
      { id: "nonlinear", text: { zh: "找出你的增益在非线性模型上还能救回的最大起始角，并解释它为什么比线性模型预测的小", en: "Find the largest start angle your gains still recover from on the nonlinear model, and explain why the linear model cannot tell you this" } },
      { id: "mpc", text: { zh: "改变 MPC 的预测步数（例如 10、20、80），比较超调、进入 1° 的时间和每步的计算量", en: "Change the MPC horizon (e.g. 10, 20, 80 steps) and compare overshoot, time to within 1° and the computation per step" } },
    ],
  },
  {
    slug: "kinematics-ik",
    title: { zh: "运动学：正解、数值逆解与奇异点", en: "Kinematics: forward, numerical IK and singularities" },
    summary: {
      zh: "用齐次变换链和手算两种方式求出机械臂末端的位置；用数值雅可比和阻尼最小二乘把目标点反解成关节角，看清多解和够不着的情况；最后找到奇异点：行列式归零、关节速度爆炸，以及阻尼如何用精度换来安全。",
      en: "Find where the arm's tip is, both with a chain of homogeneous transforms and by hand; turn a target point back into joint angles with a numerical Jacobian and damped least squares, including multiple solutions and targets out of reach; then find the singularities, where the determinant vanishes, joint speeds explode and damping trades accuracy for safety.",
    },
    minutes: 240,
    objectives: [
      { zh: "能用变换连乘和手算两种方式求 q = [30, 45, −60]° 的末端位置，得到 (0.1840, 0.1062, 0.1637) m。", en: "Compute the tip position with the transform chain and by hand for q = [30, 45, −60]°, getting (0.1840, 0.1062, 0.1637) m." },
      { zh: "能用阻尼最小二乘（λ = 0.03）解逆运动学，把 209.357 mm 的误差在 15 次迭代内降到 0.002 mm。", en: "Solve inverse kinematics with damped least squares at λ = 0.03, cutting a 209.357 mm error to 0.002 mm in 15 iterations." },
      { zh: "能识别够不到的目标和多解分支：0.283 m 的目标停在差 32.3 mm 处，换一个初值得到底座 −123.69°。", en: "Recognise unreachable targets and multiple branches: a 0.283 m target stops 32.3 mm short, and a different start gives base −123.69°." },
      { zh: "能用 |det J| = L1 L2 r |sin(elbow)| 判断奇异点，并解释肘角 −0.3° 时精确求逆为何要求 8249.1 deg/s。", en: "Detect singularities with |det J| = L1 L2 r |sin(elbow)| and explain why the exact inverse demands 8249.1 deg/s at elbow −0.3°." },
    ],
    prereqs: ["so101-arm"],
    resources: ["modern-robotics"],
    tasks: [
      { id: "fk-hand", text: { zh: "手算 q = [30, 45, −60]° 时末端的位置，再用 kinematics.py 的变换链核对到 0.1 mm", en: "Work out the tip position for q = [30, 45, −60]° by hand and check it against kinematics.py's transform chain to 0.1 mm" } },
      { id: "ik", text: { zh: "给数值逆解选三个自己的目标点（其中一个够不着），从两个不同的初值出发，记录迭代次数和得到的解", en: "Pick three targets of your own for the numerical IK (one out of reach), start from two different initial guesses, and log the iterations and the solutions" } },
      { id: "fk-check", text: { zh: "把每个逆解结果再代回正运动学，确认误差小于 0.1 mm", en: "Feed every IK result back through forward kinematics and confirm the error is under 0.1 mm" } },
      { id: "singular", text: { zh: "在你的机械臂（或模型）上把手臂伸直，演示奇异点：说明哪个方向动不了，以及雅可比行列式为什么归零", en: "Show a singularity on your arm (or the model) by stretching it straight: say which direction it cannot move in and why the Jacobian's determinant goes to zero" } },
    ],
  },
  {
    slug: "camera-calibration",
    title: { zh: "相机标定：内参、畸变与像素到三维", en: "Camera calibration: intrinsics, distortion and pixel to 3D" },
    summary: {
      zh: "从针孔模型和径向畸变讲起，用 OpenCV 在已知真值的合成棋盘格照片上标定相机，对比有无畸变项的结果；再用 solvePnP 找到桌面，把像素变成桌面上的三维点，看清跳过去畸变在画面角上会差出多少。",
      en: "Start from the pinhole model and radial distortion, calibrate a camera with OpenCV on synthetic checkerboard photos whose true values are known, and compare fits with and without distortion; then find the table with solvePnP, turn pixels into 3D points on it, and see how much skipping undistortion costs at the image corners.",
    },
    minutes: 240,
    objectives: [
      { zh: "能由内参算出焦距：fx = 500 px 配 3 µm 的像素对应 1.5 mm 的镜头。", en: "Compute the focal length from the intrinsics: fx = 500 px with 3 µm pixels gives a 1.5 mm lens." },
      { zh: "能用 OpenCV 在棋盘格照片上标定并比较拟合：无畸变 RMS 0.702 px，带 k1、k2 时 0.189 px。", en: "Calibrate with OpenCV on checkerboard photos and compare the fits: RMS 0.702 px without distortion against 0.189 px with k1 and k2." },
      { zh: "能读出标定结果 fx = 499.8、fy = 499.9、cx = 319.8、cy = 239.6、k1 = −0.1212、k2 = +0.0310，并与真值逐项比较。", en: "Read off fx = 499.8, fy = 499.9, cx = 319.8, cy = 239.6, k1 = −0.1212 and k2 = +0.0310, and compare them with the true values." },
      { zh: "能用 solvePnP 与 undistortPoints 把像素变成桌面上的三维点，并算清跳过去畸变在画面角上要付 44.7 mm 的代价。", en: "Turn a pixel into a 3D point on the table with solvePnP and undistortPoints, and price skipping undistortion at 44.7 mm in the corner." },
    ],
    prereqs: ["gazebo-sim", "ros2-graph"],
    resources: ["opencv-calibration", "ros-camera-calibration"],
    tasks: [
      { id: "run", text: { zh: "依次运行 make_views.py、calibrate.py 和 pixel_to_table.py，把恢复出的 fx、fy、cx、cy、k1、k2 和真值逐项比较", en: "Run make_views.py, calibrate.py and pixel_to_table.py in turn, and compare the recovered fx, fy, cx, cy, k1 and k2 with the true values one by one" } },
      { id: "own-camera", text: { zh: "打印一张 9 × 6 内角点的棋盘格，用你自己的摄像头拍 15 到 20 张照片并标定，记录 RMS 重投影误差", en: "Print a 9 × 6 inner-corner checkerboard, take 15 to 20 photos with your own camera, calibrate it and record the RMS reprojection error" } },
      { id: "centre-only", text: { zh: "只用画面中央的照片再标定一次，比较 k1、k2 和主点的变化，并解释原因", en: "Calibrate again using only photos with the board in the centre of the frame, compare k1, k2 and the principal point, and explain the difference" } },
      { id: "measure", text: { zh: "把棋盘格平放在桌上，用 pixel_to_table.py 的方法求两个像素之间的距离，再用尺子量，比较两者", en: "Lay the board flat on a table, use pixel_to_table.py's method to find the distance between two pixels, measure it with a ruler, and compare" } },
    ],
  },
  {
    slug: "moveit-pick-place",
    title: { zh: "MoveIt 2：运动规划与无碰撞抓放", en: "MoveIt 2: motion planning and a collision-free pick and place" },
    summary: {
      zh: "从逆运动学走到运动规划：构型空间、碰撞检测、随机采样规划器 RRTConnect 和走直线的 Pilz LIN。在 ros2_control mock 硬件上的 Panda 机械臂上，用 MoveItPy 搭好规划场景，抓起方块、把它附着到手上、越过一堵墙放下，再看一个墙里的目标为什么规划不出来。",
      en: "Go from inverse kinematics to motion planning: configuration space, collision checking, the random sampling planner RRTConnect and Pilz LIN for straight lines. On a Panda arm on ros2_control mock hardware, build a planning scene with MoveItPy, pick up a block, attach it to the hand, carry it over a wall and set it down, then see why a goal inside the wall cannot be planned.",
    },
    minutes: 300,
    objectives: [
      { zh: "能区分 OMPL RRTConnect 与 Pilz LIN：随机搜索的无碰撞移动，与接近、撤退用的笛卡尔直线。", en: "Distinguish OMPL RRTConnect from Pilz LIN: random collision-free moves versus straight Cartesian lines for the approach and retreat." },
      { zh: "能在规划场景里放入 0.25 m 高的墙和 0.04 × 0.04 × 0.08 m 的积木，并用 touch_links 把积木附到 panda_hand。", en: "Build the planning scene with a 0.25 m wall and a 0.04 × 0.04 × 0.08 m block, then attach the block to panda_hand with touch_links." },
      { zh: "能在 ros2_control 模拟硬件上完成抓放：指尖到达 (0.500, −0.250, 0.060) m，搬运段每个路点都通过碰撞检查。", en: "Execute the pick and place on ros2_control mock hardware: fingertips reach (0.500, −0.250, 0.060) m and every carry waypoint passes the collision check." },
      { zh: "能把墙内的目标判为 GOAL_STATE_INVALID 而非规划超时，并列出从模拟到真机要改的地方：抓取检测、速度缩放、急停。", en: "Diagnose a goal inside the wall as GOAL_STATE_INVALID, not a planner timeout, and list the mock-to-real changes: grasp detection, speed scaling, emergency stop." },
    ],
    prereqs: ["ros2-control", "kinematics-ik", "camera-calibration"],
    resources: ["moveit-docs"],
    tasks: [
      { id: "run", text: { zh: "运行 bringup.launch.py 和 pick_place.py，把你的输出和课程里的输出对比，指出哪些行每次都一样、哪些会变，以及为什么", en: "Run bringup.launch.py and pick_place.py, compare your output with the lesson's, and say which lines stay the same every run, which change, and why" } },
      { id: "taller-wall", text: { zh: "把墙加高到 0.35 m 再运行，记录搬运路径怎么走、碰撞检查是否仍然 valid", en: "Raise the wall to 0.35 m, run again, and record the carry's route and whether the collision check is still valid" } },
      { id: "long-wall", text: { zh: "把墙加长到 0.80 m，让手臂没法从墙的两端绕过去，运行五次，记录每次的路径和方块底部高出墙顶多少", en: "Make the wall 0.80 m long so the arm cannot go around its ends, run five times, and record each route and how far the block's bottom stays above the wall top" } },
      { id: "real-arm", text: { zh: "为你自己的机械臂写一份从 mock 硬件到真机的检查清单：控制器、夹爪力与抓取检测、速度缩放、急停，以及用第 4 课的相机定位方块", en: "Write a checklist for moving this to your own arm: controllers, gripper force and grasp detection, speed scaling, the emergency stop, and locating the block with the camera from Lesson 4" } },
    ],
  },
];

const month6Lessons: Lesson[] = [
  {
    slug: "behaviour-cloning",
    title: { zh: "模仿学习（一）：示范数据、行为克隆与 DAgger", en: "Imitation learning I: demonstrations, behaviour cloning and DAgger" },
    summary: {
      zh: "把示范数据看成一张按帧记录的表，用最近邻行为克隆在 L 形走廊里学会专家的动作；在执行器噪声下看清协变量偏移：示范越多也不见好，失败集中在示范从没去过的地方；再用带噪声的示范和 DAgger 把恢复动作放进数据，最后对照 LeRobot 在 SO-101 上的录制、训练和运行命令。",
      en: "Treat a demonstration dataset as a table of frames, clone an expert in an L-shaped corridor with nearest-neighbour behaviour cloning, and watch covariate shift under actuator noise: more demos do not help and the failures sit where the demos never went; then put recoveries into the data with noisy demos and DAgger, and map it all onto LeRobot's record, train and rollout commands for the SO-101.",
    },
    minutes: 240,
    objectives: [
      { zh: "能把示范数据集读成按帧记录的表，说明 LeRobot 数据集里 episode_index、frame_index、observation.state、action 各列的含义，以及 SO-101 上 30 帧/秒的六个关节位置。", en: "Read a demonstration dataset as a table of frames, name what episode_index, frame_index, observation.state and action hold in a LeRobot dataset, and note the 30 fps six-joint recording on SO-101." },
      { zh: "能写出行为克隆的平方误差目标，并能解释 1 最近邻策略与训练好的神经网络在离开训练数据时都只能外推。", en: "Write the squared-error behaviour cloning objective, and explain that both a 1-nearest-neighbour policy and a trained network can only extrapolate off their training data." },
      { zh: "能解释协变量偏移：20 条与 80 条无噪声示范都是 67/100，失败集中在示范从未记录的目标端，并能手算 1 cm × √38 = 6.2 cm 的漂移。", en: "Explain covariate shift: 20 and 80 noise-free demos both score 67/100, failures sit at the goal end where nothing was recorded, and the drift computes as 1 cm × √38 = 6.2 cm." },
      { zh: "能说明带噪声示范（776 帧，99/100）与一轮 DAgger（581 帧，61/100 提升到 100/100）如何把恢复动作放进数据，并在 SO-101 上用 lerobot-record、lerobot-train、lerobot-rollout 跑通流程。", en: "Explain how noisy demos (776 frames, 99/100) and one DAgger round (581 frames, 61/100 to 100/100) add recoveries, and run lerobot-record, lerobot-train and lerobot-rollout on the SO-101." },
    ],
    prereqs: ["so101-arm", "python-terminal"],
    resources: ["lerobot-il-robots", "dagger-paper"],
    tasks: [
      { id: "run", text: { zh: "运行 bc_reach.py，打开 demos.csv，确认每列对应 LeRobot 数据集的哪一列，并用 √n 估算无纠正时的漂移", en: "Run bc_reach.py, open demos.csv, match each column to a LeRobot dataset column, and estimate the uncorrected drift with √n" } },
      { id: "noise", text: { zh: "把 NOISE 改成 0.005 和 0.02 再运行，记录 BC（20 条示范）和 DAgger 第 1 轮的成功率，解释变化", en: "Change NOISE to 0.005 and 0.02, run again, record the success of BC on 20 demos and of DAgger round 1, and explain the change" } },
      { id: "goal-end", text: { zh: "修复“目标端”的空洞：让示范在到达目标后再多录几帧原地不动的动作，比较 BC 的失败位置", en: "Fix the goal-end hole: make the demos record a few extra frames of holding still at the goal, and compare where BC now fails" } },
      { id: "real-dataset", text: { zh: "（有硬件时）用 lerobot-record 录 50 个回合：5 个方块位置各 10 个，至少包含 5 次有意的恢复动作", en: "(With hardware) record 50 episodes with lerobot-record: 10 at each of 5 cube positions, including at least 5 deliberate recoveries" } },
    ],
  },
  {
    slug: "act-diffusion",
    title: { zh: "模仿学习（二）：多模态示范、动作分块（ACT）与扩散策略", en: "Imitation learning II: multimodal demos, action chunking (ACT) and diffusion policy" },
    summary: {
      zh: "示范里有两个都对的答案时，平方误差损失学到的是它们的平均——一个谁也没做过、还会撞上障碍物的动作。在方块任务上比较取平均、采样、不同长度的动作块和用精确去噪器的 DDPM 采样，看清 ACT 分块的好处与开环代价、扩散策略为什么能保留多个模式，再对照 LeRobot 训练 ACT 和 Diffusion Policy 的命令。",
      en: "When the demonstrations contain two right answers, a squared-error loss learns their average: a move nobody made, straight into the obstacle. On a block task, compare averaging, sampling, action chunks of different lengths and DDPM sampling with the exact denoiser, see what ACT's chunking buys and what running open loop costs, why a diffusion policy keeps several modes, and map it onto LeRobot's commands for training ACT and Diffusion Policy.",
    },
    minutes: 240,
    objectives: [
      { zh: "能手算均值策略在岔口的横向动作 (−7 + 3) / 10 × 4.16 = −1.66 cm（即 −0.017 m），并解释它为什么撞上方块、成功率只有 67/100，而采样是 99/100。", en: "Compute the averaging policy's sideways move at the fork as (−7 + 3) / 10 × 4.16 = −1.66 cm (−0.017 m), and explain its 67/100 success against 99/100 for sampling." },
      { zh: "能说明 ACT 一次预测 k = 100 个动作（50 Hz 下 2 秒）并用时间集成混合动作块，也能解释开环代价：块长 4、8、16 的成功率依次是 98/100、88/100、80/100。", en: "Explain how ACT predicts k = 100 actions at 50 Hz (2 s) and blends chunks by temporal ensembling, and why longer chunks cost success: 4, 8 and 16 give 98/100, 88/100 and 80/100." },
      { zh: "能写出扩散的前向加噪 x_s = √ᾱ_s · x_0 + √(1 − ᾱ_s) · ε，并说明 Diffusion Policy 预测 16 个动作、执行前 8 个，以及每个动作块要多次通过网络、推理时间有代价。", en: "Write the forward noising x_s = √ᾱ_s · x_0 + √(1 − ᾱ_s) · ε, and explain that Diffusion Policy predicts 16 actions, executes the first 8, and needs repeated network passes per chunk." },
      { zh: "能在同一份 LeRobot 数据集上分别用 --policy.type=act 与 --policy.type=diffusion 训练，并用同一组固定起始位置比较成功率和失败发生的位置。", en: "Train --policy.type=act and --policy.type=diffusion on the same LeRobot dataset, then compare success and failure locations over one fixed set of start positions." },
    ],
    prereqs: ["behaviour-cloning", "so101-arm"],
    resources: ["act-paper", "diffusion-policy", "lerobot-il-robots"],
    tasks: [
      { id: "run", text: { zh: "运行 multimodal.py，用 7 : 3 的近邻比例手算均值策略在岔口的横向动作（−1.66 cm）；再打印它在刚过岔口的 (0, 0.23) 处实际给出的动作：在 examples/month-6/act-diffusion 目录下运行 python3 -c 'import random, multimodal as m; d = m.Demos(m.record_demos(40, random.Random(5))); print(round(100 * m.average_policy(d)((0, 0.23), 0)[0][0], 2))'，确认它打印出 −1.74（单位 cm），与 Quiz q1 解析一致", en: "Run multimodal.py and work out by hand, from the 7 : 3 neighbours, the averaging policy's sideways move at the fork (−1.66 cm). Then print the move it actually makes just past the fork, at (0, 0.23): in examples/month-6/act-diffusion run python3 -c 'import random, multimodal as m; d = m.Demos(m.record_demos(40, random.Random(5))); print(round(100 * m.average_policy(d)((0, 0.23), 0)[0][0], 2))' and confirm it prints −1.74 (in cm), the value in the Quiz q1 explanation" } },
      { id: "one-side", text: { zh: "让专家只从左边绕（side 固定为 −1），再比较 average 和 sample 的成功率，解释为什么差距消失", en: "Make the expert always pass on the left (side fixed at −1), compare average and sample again, and explain why the gap disappears" } },
      { id: "chunk-length", text: { zh: "把方块的 HALF 改成 0.12，再跑 chunk 4、8、16，画出成功率随块长的变化", en: "Change the block's HALF to 0.12, run chunk 4, 8 and 16 again, and plot success against chunk length" } },
      { id: "train-real", text: { zh: "（有 GPU 和数据集时）用 LeRobot 在同一数据集上训练 ACT 和 Diffusion Policy，在同样 10 个起始位置上各测 10 次，记录成功率和每个动作块的推理时间", en: "(With a GPU and a dataset) train ACT and Diffusion Policy on the same LeRobot dataset, test each 10 times at the same 10 start positions, and record success and inference time per chunk" } },
    ],
  },
  {
    slug: "vla-models",
    title: { zh: "VLA 模型：动作如何变成词元，哪些开放权重", en: "VLA models: how actions become tokens, and which have open weights" },
    summary: {
      zh: "视觉-语言-动作模型由视觉编码器、语言模型和动作输出组成。在一个类似 SO-101 遥操作的数据集上，比较 RT-2/OpenVLA 式的 256 区间分词和 FAST 式的 DCT 压缩：词元数、截断误差、相邻词元几乎相同的问题；再逐一核对 OpenVLA、Octo、π0/π0.5、SmolVLA、GR00T 的权重许可证，并给出在 SO-101 上微调 SmolVLA 的命令。",
      en: "A vision-language-action model is a vision encoder, a language model and an action output. On a dataset shaped like SO-101 teleoperation, compare RT-2/OpenVLA-style 256-bin tokens with FAST-style DCT compression: token counts, clipping error and nearly identical consecutive tokens; then check the weight licences of OpenVLA, Octo, π0/π0.5, SmolVLA and GR00T one by one, with the command for fine-tuning SmolVLA on an SO-101.",
    },
    minutes: 180,
    objectives: [
      { zh: "能说出 VLA 的三部分（视觉编码器、语言模型、动作输出），并区分 RT-2、OpenVLA、π0-FAST 的动作词元做法与 Octo、π0、SmolVLA、GR00T 的独立动作头做法。", en: "Name the three parts of a VLA (vision encoder, language model, action output) and distinguish RT-2, OpenVLA and π0-FAST action tokens from the separate action head used by Octo, π0, SmolVLA and GR00T." },
      { zh: "能手算 256 个区间的宽度 (77 − (−84)) / 256 = 0.63 度，解释 6.2 度的最大误差来自 6 个超出第 1 到第 99 百分位数而被截断的值，并指出 174 次相邻词元变化中有 102 次不超过 2 个区间。", en: "Compute the 256-bin width as (77 − (−84)) / 256 = 0.63 degrees, explain the 6.2-degree error from 6 clipped values, and note that 102 of 174 consecutive tokens differ by 2 bins or fewer." },
      { zh: "能说明 FAST 用 DCT 压缩动作块：缩放 30 时 41 个非零系数替代 180 个区间词元（少 4.4 倍），缩放 10 时 28 个数、rms 误差约 1.1 度，再用字节对编码压缩。", en: "Explain FAST's DCT compression: scale 30 needs 41 nonzero coefficients instead of 180 bin tokens (4.4 times fewer), scale 10 needs 28 numbers at 1.1 deg rms error, then byte-pair encoding." },
      { zh: "能逐个说出 OpenVLA（MIT）、Octo（MIT）、SmolVLA（Apache-2.0）、GR00T N1.6（仅限研究与非商业）与 GR00T N1.7（允许商用）的权重许可证，并用 lerobot-train 在 SO-101 上微调 SmolVLA。", en: "State the weight licences for OpenVLA (MIT), Octo (MIT), SmolVLA (Apache-2.0), GR00T N1.6 (research and non-commercial only) and GR00T N1.7 (commercial allowed), and fine-tune SmolVLA with lerobot-train." },
    ],
    prereqs: ["act-diffusion", "behaviour-cloning", "so101-arm"],
    resources: ["lerobot-smolvla", "openvla", "openpi"],
    tasks: [
      { id: "run", text: { zh: "运行 action_tokens.py，手算关节 0 的区间宽度，并解释 6.2 度的最大误差从哪里来", en: "Run action_tokens.py, work out joint 0's bin width by hand, and explain where the 6.2-degree maximum error comes from" } },
      { id: "rate", text: { zh: "把 HZ 改成 50 和 10（CHUNK 同步改成 1 秒），比较区间词元数、“与上一步相同”的比例和 DCT 缩放 10 时的非零系数个数", en: "Change HZ to 50 and to 10 (and CHUNK to match 1 s), and compare the bin token count, the share of tokens equal to the previous step, and the nonzero DCT coefficients at scale 10" } },
      { id: "licences", text: { zh: "为表中每个模型打开模型卡，记下今天的权重许可证、参数量和是否允许商用，与课程表格对比", en: "Open the model card of every model in the table, write down today's weight licence, parameter count and whether commercial use is allowed, and compare with the lesson's table" } },
      { id: "smolvla", text: { zh: "（有 GPU 和数据集时）在你第 1 课录的数据集上微调 SmolVLA，与同一数据集上的 ACT 在同样 10 个起始位置上比较成功率", en: "(With a GPU and a dataset) fine-tune SmolVLA on the dataset from lesson 1 and compare its success with ACT on the same data at the same 10 start positions" } },
    ],
  },
  {
    slug: "policy-evaluation",
    title: { zh: "评估一个策略：置信区间、配对试验与失败分析", en: "Evaluating a policy: intervals, paired trials and failure analysis" },
    summary: {
      zh: "从少量试验中量化成功率的不确定性：用 Wilson 区间看清 10/10 只说明成功率大概高于 72 %，同一策略十组 10 次试验从 4 到 9 不等；用逐次固定种子（真机上是固定的起始位置清单）做配对比较和 McNemar 检验，算出区分两个成功率要多少次试验，再用失败表找出下一步该修什么，最后为你的机械臂写一份评估规程。",
      en: "Quantify the uncertainty of a success rate from few trials: Wilson intervals show that 10/10 only means the rate is probably above 72 %, and ten 10-trial sessions of one policy range from 4 to 9; compare policies trial by trial with per-trial seeds (a fixed list of start positions on hardware) and McNemar's test, work out how many trials a comparison needs, use a failure table to find what to fix next, and write an evaluation protocol for your arm.",
    },
    minutes: 180,
    objectives: [
      { zh: "能算出成功率 k/n 的 Wilson 95 % 区间（例如 8/10 是 49.0 .. 94.3 %），并说明 10 次全成功只说明真实成功率大概高于 72 %。", en: "Compute the Wilson 95 % interval for k/n (8/10 gives 49.0 .. 94.3 %) and explain that 10 out of 10 only shows a true rate probably above 72 %." },
      { zh: "能解释同一策略十组 10 次试验从 4 次到 9 次不等意味着什么，并规定报告全部试验组而不是最好的一组。", en: "Explain what it means that one policy ranges from 4 to 9 successes across ten 10-trial sessions, and report every session instead of the best one." },
      { zh: "能用逐次固定种子做配对比较，只对不一致的试验做 McNemar 精确检验（35 次全部偏向一边时 p = 5.8e-11）。", en: "Compare two policies trial by trial with per-trial seeds, and apply McNemar's exact test to the disagreements (35 all one way gives p = 5.8e-11)." },
      { zh: "能算出区分两个成功率所需的试验次数（67 % 对 99 % 是 21 次），并用失败表定位该修什么（74 % 的失败在目标端），最后写出评估规程。", en: "Compute the trials needed to separate two success rates (21 for 67 % vs 99 %), find what to fix in a failure table (74 % at the goal end), and write an evaluation protocol." },
    ],
    prereqs: ["behaviour-cloning"],
    resources: ["lerobot-il-robots"],
    tasks: [
      { id: "run", text: { zh: "运行 eval_report.py，手算 8/10 的 Wilson 区间并与输出核对", en: "Run eval_report.py and work out the Wilson interval for 8/10 by hand; check it against the output" } },
      { id: "dagger", text: { zh: "在第 3 部分把第二个策略换成第 1 课的 DAgger 第 1 轮策略，记录配对表和 McNemar p 值", en: "In part 3, replace the second policy with lesson 1's DAgger round-1 policy and record the paired table and McNemar's p" } },
      { id: "sessions", text: { zh: "把第 2 部分改成每组 30 次试验，比较十组结果的最低与最高值，并解释为什么范围变窄", en: "Change part 2 to 30 trials per session, compare the lowest and highest of the ten sessions, and explain why the range narrows" } },
      { id: "protocol", text: { zh: "为你的机械臂任务写一份评估规程：成功标准、20 个起始位置（其中 5 个不在训练数据里）、固定项、记录项和报告格式", en: "Write an evaluation protocol for your arm's task: success criterion, 20 start positions (5 of them not in the training data), what stays fixed, what is recorded and the report format" } },
    ],
  },
  {
    slug: "specialisation-portfolio",
    title: { zh: "选择方向、作品集与求职", en: "Choosing a specialisation, the portfolio and getting hired" },
    summary: {
      zh: "用三个问题（你会主动回头看哪些课、你已经能拿出什么、你想去的地方招什么人）在五个方向里选定一个；挑三个带视频、指标和失败分析的作品集项目；用 portfolio_check.py 检查 README 是否有评审要看的八个部分；在一行代码上练习三层追问；最后是简历、申请信息和边做边投。",
      en: "Pick one of five directions with three questions (which lessons you went back to, what you can already show, who is hiring where you want to work); choose three portfolio projects with video, metrics and failure analysis; check a README for the eight parts a reviewer looks for with portfolio_check.py; practise three levels of follow-up questions on one line of code; then the CV, the application message and applying while you build.",
    },
    minutes: 180,
    objectives: [
      { zh: "能用三个问题（你会主动回头看哪些课、你已经能拿出什么、你统计的 20 份招聘启事要什么技能）在五个方向中选定一个，并把它写成一句话。", en: "Choose one of five directions using three questions (lessons you revisited, work you can already show, skills in 20 job adverts) and write the answer as one sentence." },
      { zh: "能选出三个作品集项目，每个都附视频、指标和失败分析，并让每个项目比教程版本多走一步（换物体、更难条件、多做一次测量或修复一个失败）。", en: "Pick three portfolio projects, each with video, metrics and failure analysis, and move each one step beyond the tutorial (different object, harder condition, extra measurement, fixed failure)." },
      { zh: "能运行 portfolio_check.py 检查项目 README，并把视频、结果、试验次数、失败分析、复现、硬件、本人贡献、局限与下一步这八项补齐。", en: "Run portfolio_check.py on a project README and add the missing parts until all eight are present: video, result, trials, failures, reproduce, hardware, contribution and next steps." },
      { zh: "能对一行关键代码回答三层追问（它做什么、为什么这样做、什么会坏以及你会怎么改，例如用 k-d 树代替逐帧扫描），并写一页项目在前的简历，每个项目附一个数字和一个链接。", en: "Answer three levels of follow-up questions about one key line of code (what it does, why this way, what breaks and what you would change), and write a one-page CV with projects first." },
    ],
    prereqs: ["behaviour-cloning", "policy-evaluation", "slam-nav"],
    resources: ["beauregard-pid", "slam-toolbox", "lerobot-il-robots"],
    tasks: [
      { id: "direction", text: { zh: "读 20 份真实招聘启事，统计技能要求，写下你选的方向和一句理由", en: "Read 20 real job adverts, tally the skills they ask for, and write down your direction with a one-sentence reason" } },
      { id: "readme", text: { zh: "对你最好的一个项目运行 portfolio_check.py，把缺的部分补齐，直到 8 项都在", en: "Run portfolio_check.py on your best project and add the missing parts until all 8 are present" } },
      { id: "three-projects", text: { zh: "列出你的三个作品集项目：每个写一个指标、一种失败和一处超出教程的改动", en: "List your three portfolio projects: for each, one metric, one failure and one change beyond the tutorial" } },
      { id: "follow-ups", text: { zh: "从每个项目里挑一行关键代码，写下三层追问的答案；答不出的那一层就是下周要学的", en: "Pick one key line from each project and write the answers to three levels of follow-up questions; any level you cannot answer is next week's study" } },
      { id: "apply", text: { zh: "写一页简历（项目在前，每个附一个数字和链接），投出前五份申请并开始记日志", en: "Write a one-page CV (projects first, each with a number and a link), send your first five applications and start the log" } },
    ],
  },
];

export const months: Month[] = [
  {
    id: 1,
    slug: "month-1",
    title: { zh: "电子基础、工作台与工具", en: "Electronics, the bench & your tools" },
    goal: {
      zh: "能读懂原理图、搭出能工作的电路，并在电路不工作时找到故障。",
      en: "Read a schematic, build a circuit that works, and find the fault when it doesn't.",
    },
    topics: [
      { zh: "电子学基础", en: "Electronics fundamentals" },
      { zh: "工作台、工具与预算", en: "The bench, tools and budget" },
      { zh: "焊接", en: "Soldering" },
      { zh: "Python、终端与 Git", en: "Python, the terminal and Git" },
    ],
    milestones: [
      { zh: "读懂原理图，并在面包板上搭出它描述的电路", en: "Read a schematic and build the circuit it describes on a breadboard" },
      { zh: "插上电之前，先算出电阻取值是否正确", en: "Work out whether a resistor value is right before you plug it in" },
      { zh: "用万用表找出短路、断路或损坏的元件", en: "Find a short, a break or a dead component with a multimeter" },
      { zh: "焊出干净的通孔焊点，并用电气方法验证", en: "Solder a clean through-hole joint and verify it electrically" },
      { zh: "写一个 Python 脚本，在终端运行，并推送到 GitHub", en: "Write a Python script, run it from the terminal, and push it to GitHub" },
      { zh: "讲清楚为什么电机堵转会让单片机复位", en: "Explain out loud why a stalling motor can reset a microcontroller" },
    ],
    lessons: month1Lessons,
  },
  {
    id: 2,
    slug: "month-2",
    title: { zh: "单片机、电机与传感器", en: "Microcontrollers, motors & sensors" },
    goal: {
      zh: "做出一台能移动、能感知环境、能自我纠正的机器人。",
      en: "Build a robot that moves, senses its environment and corrects itself.",
    },
    topics: [
      { zh: "Arduino：IO、PWM、中断、I2C/SPI、串口调试、非阻塞计时", en: "Arduino: IO, PWM, interrupts, I2C/SPI, serial debugging, non-blocking timing" },
      { zh: "ESP32：Wi-Fi/蓝牙、ESP-IDF 与 Arduino 内核", en: "ESP32: Wi-Fi/Bluetooth, ESP-IDF and the Arduino core" },
      { zh: "电机、驱动器与执行器（直流、步进、FOC）", en: "Motors, drivers and actuation (DC, stepper, FOC)" },
      { zh: "传感器与传感器融合（IMU、编码器、卡尔曼滤波）", en: "Sensors and sensor fusion (IMU, encoders, Kalman filters)" },
      { zh: "你的前两台机器人：循线小车与自平衡车", en: "Your first two robots: a line follower and a self-balancer" },
    ],
    milestones: [
      { zh: "以受控速度驱动电机，并区分 PWM 占空比与实际转速", en: "Drive a motor at a controlled speed and tell PWM duty apart from actual RPM" },
      { zh: "读取编码器并围绕它闭合位置环", en: "Read an encoder and close a position loop around it" },
      { zh: "不看教程，仅凭数据手册接好并读取 I2C 传感器", en: "Wire and read an I2C sensor from its datasheet alone" },
      { zh: "把加速度计与陀螺仪数据融合成稳定的角度估计", en: "Fuse accelerometer and gyro data into a stable angle estimate" },
      { zh: "通过描述机器人的表现来解释 P、I、D 各自的作用", en: "Explain P, I and D by describing what your robot did when you changed them" },
      { zh: "在 GitHub 上展示两台能工作的机器人及其故障记录", en: "Show two working robots on GitHub with a write-up of what broke" },
    ],
    lessons: month2Lessons,
  },
  {
    id: 3,
    slug: "month-3",
    title: { zh: "机械设计、CAD 与制造", en: "Mechanical design, CAD & manufacturing" },
    goal: {
      zh: "在 CAD 中设计一个零件，把它制造出来，并且装得上。",
      en: "Design a part in CAD, manufacture it, and have it fit.",
    },
    topics: [
      { zh: "CAD：Onshape / Fusion / FreeCAD / SOLIDWORKS 选型与参数化建模", en: "CAD: choosing Onshape / Fusion / FreeCAD / SOLIDWORKS; parametric modelling" },
      { zh: "3D 打印：校准、公差与面向 FDM 的设计", en: "3D printing: calibration, tolerances and design for FDM" },
      { zh: "执行器、传动与回差", en: "Actuators, transmissions and backlash" },
      { zh: "组装并改造一台真实的机械臂", en: "Build and modify a real robot arm" },
      { zh: "控制：PID、积分饱和与串级回路（本站补充）", en: "Control: PID, windup and cascade loops (site supplement)" },
    ],
    milestones: [
      { zh: "根据数据手册用完全约束的草图建模零件", en: "Model a part from a datasheet with fully constrained sketches" },
      { zh: "通过实测给出你的打印机真实配合间隙", en: "State your printer's real clearances from measurement" },
      { zh: "针对 FDM 设计零件，考虑方向、悬垂与层间结合", en: "Design for FDM, accounting for orientation, overhangs and layer adhesion" },
      { zh: "为零件选择 PLA/PETG/ABS/TPU 并说明理由", en: "Choose PLA, PETG, ABS or TPU for a part and justify it" },
      { zh: "解释并演示回差", en: "Explain and demonstrate backlash" },
      { zh: "展示一台你组装、校准并用自制零件改造过的机械臂", en: "Show a robot arm you assembled, calibrated and modified with your own parts" },
      { zh: "让第 2 个月的平衡车靠串级外环在 60 秒内停在原地（本站补充）", en: "Keep Month 2's balancer in place for 60 s with a cascade outer loop (site supplement)" },
    ],
    lessons: month3Lessons,
  },
  {
    id: 4,
    slug: "month-4",
    title: { zh: "ROS 2 与仿真", en: "ROS 2 & simulation" },
    goal: {
      zh: "用 ROS 2 构建机器人并仿真，让它建图并自主导航。",
      en: "Build a robot in ROS 2, simulate it, and make it map a room and navigate autonomously.",
    },
    topics: [
      { zh: "选择 ROS 2 发行版，避开 ROS 1 陷阱", en: "Choosing a ROS 2 distro and avoiding the ROS 1 trap" },
      { zh: "ROS 2 核心概念：节点、话题、服务、动作", en: "ROS 2 core concepts: nodes, topics, services, actions" },
      { zh: "URDF、TF 与机器人描述", en: "URDF, TF and describing a robot" },
      { zh: "仿真：Gazebo、MuJoCo、Isaac Sim（外链）", en: "Simulation: Gazebo, MuJoCo, Isaac Sim (external links)" },
      { zh: "ros2_control 与真实硬件", en: "ros2_control and real hardware" },
      { zh: "SLAM 与导航（SLAM Toolbox、Nav2）", en: "SLAM and navigation (SLAM Toolbox, Nav2)" },
    ],
    milestones: [
      { zh: "用 Python 和 C++ 编写使用话题、服务、动作的 ROS 2 节点", en: "Write ROS 2 nodes in Python and C++ using topics, services and actions" },
      { zh: "用 xacro 描述你的机器人，坐标系、惯量与碰撞几何正确", en: "Describe your robot in xacro with correct frames, inertias and collisions" },
      { zh: "在 Gazebo 中仿真带激光雷达和相机的机器人", en: "Simulate it in Gazebo with working lidar and camera" },
      { zh: "配置 ros2_control，通过控制器驱动机器人", en: "Configure ros2_control and drive through a controller" },
      { zh: "用 SLAM Toolbox 建图，用 Nav2 自主导航", en: "Map with SLAM Toolbox and navigate with Nav2" },
      { zh: "诊断损坏的 TF 树", en: "Diagnose a broken TF tree" },
    ],
    lessons: month4Lessons,
  },
  {
    id: 5,
    slug: "month-5",
    title: { zh: "让机器人真正工作的数学", en: "The maths that makes robots work" },
    goal: {
      zh: "理解并实现你已用过的控制与感知背后的原理。",
      en: "Understand and implement the control and perception underneath everything you've built.",
    },
    topics: [
      { zh: "控制理论：从 PID 走向建模与频域", en: "Control theory: from PID to models and the frequency domain" },
      { zh: "状态空间、LQR 与 MPC", en: "State space, LQR and MPC" },
      { zh: "运动学：正解与数值逆解、奇异点", en: "Kinematics: forward, numerical IK, singularities" },
      { zh: "相机标定与视觉感知", en: "Camera calibration and perception" },
      { zh: "MoveIt 2 运动规划与抓取", en: "Motion planning and pick-and-place with MoveIt 2" },
    ],
    milestones: [
      { zh: "从实测数据辨识关节模型，并在频域里读出 PID 整定的相位裕度与增益裕度", en: "Identify a joint model from measured data and read a PID tuning's phase and gain margins in the frequency domain" },
      { zh: "用状态空间描述系统，并在仿真对象上实现 LQR", en: "Describe a system in state space and implement LQR on a simulated plant" },
      { zh: "手算正运动学，数值求解逆运动学", en: "Compute forward kinematics by hand and solve IK numerically" },
      { zh: "指着机器人解释什么是奇异点", en: "Explain a singularity by pointing at a robot doing it" },
      { zh: "标定相机，把像素转换成三维位置", en: "Calibrate a camera and turn a pixel into a 3D position" },
      { zh: "在 MoveIt 2 中规划并执行无碰撞抓放", en: "Plan and execute a collision-free pick and place in MoveIt 2" },
    ],
    lessons: month5Lessons,
  },
  {
    id: 6,
    slug: "month-6",
    title: { zh: "机器人学习、专精与求职", en: "Robot learning, specialisation & getting hired" },
    goal: {
      zh: "选定一个方向，做出代表作，并开始投递。",
      en: "Pick one direction, build a portfolio piece in it, and start applying.",
    },
    topics: [
      { zh: "模仿学习：行为克隆、ACT、扩散策略", en: "Imitation learning: behaviour cloning, ACT, diffusion policy" },
      { zh: "VLA 模型：哪些开放权重", en: "VLA models and which have open weights" },
      { zh: "选择专精方向", en: "Choosing a specialisation" },
      { zh: "作品集与求职", en: "Portfolio and job applications" },
    ],
    milestones: [
      { zh: "录制示范数据集并训练能在自己硬件上运行的策略", en: "Record a demo dataset and train a policy that runs on your hardware" },
      { zh: "解释行为克隆、ACT 与扩散策略的区别", en: "Explain behaviour cloning vs ACT vs diffusion policy" },
      { zh: "说出哪些 VLA 模型开放权重", en: "Name which VLA models have open weights" },
      { zh: "说明你选择的方向及原因", en: "State which direction you're pursuing and why" },
      { zh: "展示三个附带视频、指标与失败分析的作品", en: "Show three portfolio projects with video, metrics and failure analysis" },
      { zh: "能回答关于你代码任意一行的三层追问", en: "Answer three levels of follow-up questions about any line of your code" },
    ],
    lessons: month6Lessons,
  },
];

/** Totals shown on the home page and month overview. */
export function monthStats(month: Month) {
  const minutes = month.lessons.reduce((sum, l) => sum + l.minutes, 0);
  return {
    lessons: month.lessons.length,
    tasks: month.lessons.reduce((sum, l) => sum + l.tasks.length, 0),
    /** Reading and exercise time, rounded to the nearest half hour. */
    hours: Math.round(minutes / 30) / 2,
  };
}

export function getMonth(slug: string): Month | undefined {
  return months.find((m) => m.slug === slug);
}

export function getLesson(monthSlug: string, lessonSlug: string) {
  const month = getMonth(monthSlug);
  if (!month) return undefined;
  const index = month.lessons.findIndex((l) => l.slug === lessonSlug);
  if (index < 0) return undefined;
  return {
    month,
    lesson: month.lessons[index],
    index,
    prev: month.lessons[index - 1],
    next: month.lessons[index + 1],
  };
}

/** Stable key used for localStorage progress, e.g. "m1/ohms-law". */
export function lessonKey(monthId: number, lessonSlug: string) {
  return `m${monthId}/${lessonSlug}`;
}
