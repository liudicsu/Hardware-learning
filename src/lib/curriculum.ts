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
    resources: ["lerobot-il-robots", "dagger-paper"],
    tasks: [
      { id: "run", text: { zh: "运行 bc_reach.py，打开 demos.csv，确认每列对应 LeRobot 数据集的哪一列，并用 √n 估算无纠正时的漂移", en: "Run bc_reach.py, open demos.csv, match each column to a LeRobot dataset column, and estimate the uncorrected drift with √n" } },
      { id: "noise", text: { zh: "把 NOISE 改成 0.005 和 0.02 再运行，记录 BC（20 条示范）和 DAgger 第 1 轮的成功率，解释变化", en: "Change NOISE to 0.005 and 0.02, run again, record the success of BC on 20 demos and of DAgger round 1, and explain the change" } },
      { id: "goal-end", text: { zh: "修复“目标端”的空洞：让示范在到达目标后再多录几帧原地不动的动作，比较 BC 的失败位置", en: "Fix the goal-end hole: make the demos record a few extra frames of holding still at the goal, and compare where BC now fails" } },
      { id: "real-dataset", text: { zh: "（有硬件时）用 lerobot-record 录 50 个回合：5 个方块位置各 10 个，至少包含 5 次有意的恢复动作", en: "(With hardware) record 50 episodes with lerobot-record: 10 at each of 5 cube positions, including at least 5 deliberate recoveries" } },
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
    status: "ready",
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
    status: "ready",
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
    status: "ready",
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
    status: "ready",
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
    status: "ready",
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
    status: "outline",
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
