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
    status: "outline",
    topics: [
      { zh: "CAD：Onshape / Fusion / FreeCAD / SOLIDWORKS 选型与参数化建模", en: "CAD: choosing Onshape / Fusion / FreeCAD / SOLIDWORKS; parametric modelling" },
      { zh: "3D 打印：校准、公差与面向 FDM 的设计", en: "3D printing: calibration, tolerances and design for FDM" },
      { zh: "执行器、传动与回差", en: "Actuators, transmissions and backlash" },
      { zh: "组装并改造一台真实的机械臂", en: "Build and modify a real robot arm" },
    ],
    milestones: [
      { zh: "根据数据手册用完全约束的草图建模零件", en: "Model a part from a datasheet with fully constrained sketches" },
      { zh: "通过实测给出你的打印机真实配合间隙", en: "State your printer's real clearances from measurement" },
      { zh: "针对 FDM 设计零件，考虑方向、悬垂与层间结合", en: "Design for FDM, accounting for orientation, overhangs and layer adhesion" },
      { zh: "为零件选择 PLA/PETG/ABS/TPU 并说明理由", en: "Choose PLA, PETG, ABS or TPU for a part and justify it" },
      { zh: "解释并演示回差", en: "Explain and demonstrate backlash" },
      { zh: "展示一台你组装、校准并用自制零件改造过的机械臂", en: "Show a robot arm you assembled, calibrated and modified with your own parts" },
    ],
    lessons: [],
  },
  {
    id: 4,
    slug: "month-4",
    title: { zh: "ROS 2 与仿真", en: "ROS 2 & simulation" },
    goal: {
      zh: "用 ROS 2 构建机器人并仿真，让它建图并自主导航。",
      en: "Build a robot in ROS 2, simulate it, and make it map a room and navigate autonomously.",
    },
    status: "outline",
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
    lessons: [],
  },
  {
    id: 5,
    slug: "month-5",
    title: { zh: "让机器人真正工作的数学", en: "The maths that makes robots work" },
    goal: {
      zh: "理解并实现你已用过的控制与感知背后的原理。",
      en: "Understand and implement the control and perception underneath everything you've built.",
    },
    status: "outline",
    topics: [
      { zh: "控制理论：从 PID 开始", en: "Control theory, starting with PID" },
      { zh: "状态空间、LQR 与 MPC", en: "State space, LQR and MPC" },
      { zh: "运动学：正解与数值逆解、奇异点", en: "Kinematics: forward, numerical IK, singularities" },
      { zh: "相机标定与视觉感知", en: "Camera calibration and perception" },
      { zh: "MoveIt 2 运动规划与抓取", en: "Motion planning and pick-and-place with MoveIt 2" },
    ],
    milestones: [
      { zh: "实现并整定 PID，用实测数据解释每一项", en: "Implement and tune PID and explain every term from measured data" },
      { zh: "用状态空间描述系统，并在仿真对象上实现 LQR", en: "Describe a system in state space and implement LQR on a simulated plant" },
      { zh: "手算正运动学，数值求解逆运动学", en: "Compute forward kinematics by hand and solve IK numerically" },
      { zh: "指着机器人解释什么是奇异点", en: "Explain a singularity by pointing at a robot doing it" },
      { zh: "标定相机，把像素转换成三维位置", en: "Calibrate a camera and turn a pixel into a 3D position" },
      { zh: "在 MoveIt 2 中规划并执行无碰撞抓放", en: "Plan and execute a collision-free pick and place in MoveIt 2" },
    ],
    lessons: [],
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
    lessons: [],
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
