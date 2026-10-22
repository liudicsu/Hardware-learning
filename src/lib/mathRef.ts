import type { L10n } from "./types";

/**
 * Math quick reference ("enough and no more"). Each entry: a definition, one worked example taken
 * from the course (numbers verified by script or formula), the lessons that use it, and free
 * authoritative textbooks. Source list: the math-prerequisite table of the Months 4-6 beginner audit.
 */
export interface MathLink {
  label: string;
  url: string;
}

export interface MathEntry {
  id: string;
  title: L10n;
  definition: L10n;
  /** Worked example from a lesson or script; plain text, line breaks kept. */
  example: L10n;
  /** Lesson slugs that use the concept. */
  lessons: string[];
  links: MathLink[];
}

export const mathEntries: MathEntry[] = [
  {
    id: "hex",
    title: { zh: "十六进制：0x 与字节", en: "Hexadecimal: 0x and bytes" },
    definition: {
      zh: "十六进制是 16 进位记数法：数字为 0–9 加 A–F（A = 10 … F = 15），代码里用 0x 前缀标记。一位十六进制数正好编码 4 个二进制位，所以一个字节写成两位，一个地址也是两位。寄存器偏移、I2C 地址和报文字节本来就是按位组织的东西，固件因此用十六进制书写它们；读一个十六进制数，只需按半字节拆回二进制。",
      en: "Hexadecimal is base-16 notation: digits 0–9 plus A–F (A = 10 … F = 15), written with a 0x prefix in code. One hex digit encodes exactly 4 bits, so a byte is two hex digits and an address is likewise two. Register offsets, I2C addresses and packet bytes are bit-organised things in the first place, which is why firmware writes them in hex; reading a hex number is just splitting it back into nibbles.",
    },
    example: {
      zh: "第 2 个月《传感器、I2C 与互补滤波》\nMPU-6050 的 I2C 地址按半字节拆开：0x6 = 0b0110、0x8 = 0b1000，因此 0x68 = 0b01101000 = 64 + 32 + 8 = 104。\n扫描器打印 Found device at 0x68；读 WHO_AM_I（寄存器 0x75）也返回 0x68。\nAD0 接高电平后地址变成 0x69 = 0b01101001：最低半字节只是从 8 加到 9，也就是一个位从 0 变 1。",
      en: "Month 2 · Sensors, I2C & the complementary filter\nSplit the MPU-6050's I2C address into nibbles: 0x6 = 0b0110, 0x8 = 0b1000, so 0x68 = 0b01101000 = 64 + 32 + 8 = 104.\nThe scanner prints Found device at 0x68, and reading WHO_AM_I (register 0x75) also returns 0x68.\nWith AD0 pulled high the address becomes 0x69 = 0b01101001: the low nibble merely steps from 8 to 9, one bit going from 0 to 1.",
    },
    lessons: ["sensors-fusion", "so101-arm"],
    links: [
      {
        label: "Python 3 docs · Lexical analysis · Integer literals",
        url: "https://docs.python.org/3/reference/lexical_analysis.html#integer-literals",
      },
      {
        label: "cppreference · C++ integer literals",
        url: "https://en.cppreference.com/w/cpp/language/integer_literal",
      },
    ],
  },
  {
    id: "twos-complement",
    title: { zh: "二进制补码与有符号整数", en: "Two's complement and signed integers" },
    definition: {
      zh: "有符号整数按二进制补码存储：N 位能表示 −2^(N−1) … 2^(N−1) − 1，最高位不是符号标记，而是一枚带负权的位（16 位时权重 −32768）。求负 = 全部位取反再加 1。越界不做声张：16 位数从 32767 再加 1 直接绕回 −32768。传感器原始读数几乎都是补码，要拼进 int16_t 这类有符号类型；若按无符号类型解释，一个小负数会变成一个大正数。",
      en: "Signed integers are stored in two's complement: N bits represent −2^(N−1) … 2^(N−1) − 1, and the top bit is not a sign flag but a bit carrying a negative weight (−32768 at 16 bits). Negating is invert-all-bits then add 1. Overflow is silent: starting from 32767, adding 1 to a 16-bit number wraps straight to −32768. Raw sensor readings are almost always two's complement — they must be assembled into a signed type such as int16_t; interpret the same bytes as unsigned and a small negative number turns into a large positive one.",
    },
    example: {
      zh: "第 2 个月《传感器、I2C 与互补滤波》\nMPU-6050 的原始值是有符号 16 位：raw gy = −262，(−262) / 131 = −2.0 °/s。\n−262 的 16 位补码是 1111 1110 1111 1010 = 0xFEFA：最高位为 1，它的位权是 −32768。\n同一个数按无符号读就变成 0xFEFA = 65274 = 65536 − 262，不再是传感器读数，而是一个无意义的大数。",
      en: "Month 2 · Sensors, I2C & the complementary filter\nThe MPU-6050's raw values are 16-bit signed: raw gy = −262, and (−262) / 131 = −2.0 °/s.\n−262 as a 16-bit two's-complement pattern is 1111 1110 1111 1010 = 0xFEFA: the top bit carries the negative weight −32768.\nRead the same pattern unsigned and it becomes 0xFEFA = 65274 = 65536 − 262 — no longer the sensor's reading but a meaningless large number.",
    },
    lessons: ["sensors-fusion", "arduino-io"],
    links: [
      {
        label: "cppreference · C++ arithmetic operators (overflow, unary −)",
        url: "https://en.cppreference.com/w/cpp/language/operator_arithmetic",
      },
      {
        label: "Python 3 docs · Built-in types · Bitwise operations on integer types",
        url: "https://docs.python.org/3/library/stdtypes.html#bitwise-operations-on-integer-types",
      },
    ],
  },
  {
    id: "bitwise",
    title: { zh: "位运算：AND、OR、XOR、取反、移位与掩码", en: "Bitwise AND, OR, XOR, NOT, shifts and masks" },
    definition: {
      zh: "位运算逐位进行：& 两位全 1 才是 1（读第 n 位：(x >> n) & 1）；| 任一位为 1 就是 1（置第 n 位：x |= 1 << n）；^ 两位相异为 1；~ 逐位取反；<< 左移一位相当于乘以 2。掩码（如 & 0xFF）把数值限制在一个字节的宽度里；移位加 | 把两个小来源的位拼成一个更大的整数。这些操作在单片机上都是一条整数指令。",
      en: "Bitwise operations work one bit position at a time: & gives 1 only where both bits are 1 (read bit n: (x >> n) & 1); | gives 1 where either bit is 1 (set bit n: x |= 1 << n); ^ where the bits differ; ~ inverts every bit; << shifts left, multiplying by 2 per bit. A mask (e.g. & 0xFF) clamps a value to one byte's width, and shifts plus | combine bits from two small sources into a larger integer. On a microcontroller each of these is a single integer instruction.",
    },
    example: {
      zh: "第 2 个月《电机、驱动器与编码器闭环》\n本课 one_rev.ino 的正交解码只用移位和 |：ab = (digitalRead(ENC_A) << 1) | digitalRead(ENC_B) 把 A 拼到高位、B 拼到低位。\n再查表：encoderCount += QDEC[(lastAB << 2) | ab]，索引是「上次 AB 左移两位后接上本次 AB」，即上次 AB × 4 + 本次 AB；两个位各两种取值，共 4 × 4 = 16 种索引，QDEC 表把每种组合译成 +1、−1 或 0。",
      en: "Month 2 · Motors, drivers & your first encoder loop\nThe lesson's one_rev.ino decodes quadrature with only a shift and |: ab = (digitalRead(ENC_A) << 1) | digitalRead(ENC_B) places A in the high bit and B in the low bit.\nThen the table lookup: encoderCount += QDEC[(lastAB << 2) | ab] — the index is the previous AB shifted two bits up with the new AB appended, i.e. previous AB × 4 + new AB; two bits with two values each give 4 × 4 = 16 indices, and the QDEC table translates each combination into +1, −1 or 0.",
    },
    lessons: ["motors-drivers", "sensors-fusion", "so101-arm"],
    links: [
      {
        label: "cppreference · C++ arithmetic operators (bit-wise, shift operators)",
        url: "https://en.cppreference.com/w/cpp/language/operator_arithmetic",
      },
      {
        label: "Python 3 docs · Built-in types · Bitwise operations on integer types",
        url: "https://docs.python.org/3/library/stdtypes.html#bitwise-operations-on-integer-types",
      },
    ],
  },
  {
    id: "trig-components",
    title: { zh: "正弦与余弦：向量的两个分量与 atan2", en: "Sine and cosine: two components of a vector, and atan2" },
    definition: {
      zh: "直角三角形里，长 r 的斜边被 θ 角拆到两条互相垂直的直角边上：邻边 r cos θ，对边 r sin θ，且 cos² θ + sin² θ = 1。反过来，给出两个分量 (x, y)，atan2(y, x) 求出它们所属向量的方向角，返回弧度、范围 (−π, π]。机器人代码里的投影与反投影几乎全用这一对关系：重力力矩是水平力矩的 cos θ 分量，加速度计读数是重力向量在两条机体轴上的分解（θ = atan2(ax, az)）。",
      en: "In a right triangle, a hypotenuse of length r is split by the angle θ onto two perpendicular legs: the adjacent r cos θ and the opposite r sin θ, with cos² θ + sin² θ = 1. Going the other way, given two components (x, y), atan2(y, x) returns the direction angle of their vector, in radians over (−π, π]. Nearly every projection and back-projection on a robot uses this pair: the gravity torque is the cos θ component of the horizontal torque, and accelerometer readings are the gravity vector split onto the body's two axes (θ = atan2(ax, az)).",
    },
    example: {
      zh: "第 3 个月《PID 与控制：积分饱和与串级回路》\n手臂水平时重力力矩最大，为 0.4 N·m；转到 θ 角只剩它的竖直分量 0.4 N·m × cos θ。\n只用 P 控制、Kp = 0.2 N·m/° 时，关节停在电机力矩与重力力矩相等处：0.2 × (60 − θ) = 0.4 × cos θ，解得 θ = 58.97°，脚本打印为 59.0°。\n验算：0.2 × 1.03 = 0.206 N·m，0.4 × cos 58.97° = 0.4 × 0.5155 = 0.206 N·m。",
      en: "Month 3 · PID & control: windup and cascade loops\nThe gravity torque on the arm is largest, 0.4 N·m, when the arm is horizontal; at angle θ only the vertical component 0.4 N·m × cos θ remains.\nWith P only and Kp = 0.2 N·m/°, the joint stops where the motor torque equals the gravity torque: 0.2 × (60 − θ) = 0.4 × cos θ, which gives θ = 58.97°, printed by the script as 59.0°.\nCheck: 0.2 × 1.03 = 0.206 N·m and 0.4 × cos 58.97° = 0.4 × 0.5155 = 0.206 N·m.",
    },
    lessons: ["pid-control", "sensors-fusion"],
    links: [
      {
        label: "OpenStax · Algebra and Trigonometry 2e · 7.2 Right Triangle Trigonometry",
        url: "https://openstax.org/books/algebra-and-trigonometry-2e/pages/7-2-right-triangle-trigonometry",
      },
      {
        label: "OpenStax · Algebra and Trigonometry 2e · 8.3 Inverse Trigonometric Functions",
        url: "https://openstax.org/books/algebra-and-trigonometry-2e/pages/8-3-inverse-trigonometric-functions",
      },
    ],
  },
  {
    id: "radians",
    title: { zh: "弧度：rad ↔ deg、角速度与弧长 s = r θ", en: "Radians: rad ↔ deg, angular speed and arc length s = r θ" },
    definition: {
      zh: "弧度用弧长量角度：弧长等于半径时的圆心角是 1 rad，一整圈是 2π rad，所以 180° = π rad。换算是乘 π/180 或 180/π。角速度也以弧度计量：rad/s 除以 2π 再乘 60 就是 rpm。弧长公式 s = r θ 把一段角换回沿圆周走过的距离；代码里喂给 sin、cos 的一律是弧度。",
      en: "A radian measures an angle by arc length: the angle is 1 rad when the arc equals the radius, and a full turn is 2π rad, so 180° = π rad. Converting is ×π/180 one way and ×180/π the other. Angular speed is measured in radians too: divide rad/s by 2π and multiply by 60 to get rpm. The arc formula s = r θ converts an angle back into the distance travelled along the circle; whatever goes into sin or cos must be radians.",
    },
    example: {
      zh: "第 2 个月《电机、驱动器与编码器闭环》\n12 CPR 编码器配 120:1 减速箱：一个车轮 12 × 120 = 1440 个计数。\n一个计数 = 360° / 1440 = 0.25°，换成弧度：0.25 × π / 180 = 0.004363 rad。\n70 mm 轮的半径 r = 35 mm，弧长 s = r θ = 35 × 0.004363 = 0.1527 mm——正是课文按整圈算的 π × 70 mm / 1440 = 219.91 / 1440。",
      en: "Month 2 · Motors, drivers & your first encoder loop\nA 12 CPR encoder behind a 120:1 gearbox gives 12 × 120 = 1440 counts per wheel revolution.\nOne count = 360° / 1440 = 0.25°, which is 0.25 × π / 180 = 0.004363 rad.\nThe 70 mm wheel has r = 35 mm, so the arc is s = r θ = 35 × 0.004363 = 0.1527 mm — exactly the lesson's per-full-circle π × 70 mm / 1440 = 219.91 / 1440.",
    },
    lessons: ["motors-drivers", "sensors-fusion", "pid-control"],
    links: [
      {
        label: "OpenStax · Algebra and Trigonometry 2e · 7.1 Angles",
        url: "https://openstax.org/books/algebra-and-trigonometry-2e/pages/7-1-angles",
      },
      {
        label: "OpenStax · University Physics Volume 1 · 10.3 Relating Angular and Translational Quantities",
        url: "https://openstax.org/books/university-physics-volume-1/pages/10-3-relating-angular-and-translational-quantities",
      },
    ],
  },
  {
    id: "rate-accumulation",
    title: { zh: "变化率与累积：导数与积分的直觉", en: "Rate of change and accumulation: derivative and integral intuition" },
    definition: {
      zh: "导数的直觉版：一个量在小窗口 dt 里的平均变化率 (x[t+dt] − x[t]) / dt，窗口越小越接近真实变化率。积分是反向操作：把瞬时值 × dt 一遍遍加起来，得到累积量。每个控制循环都在同时做这两件事：编码器先累积计数，再除以时间窗变成速度；PID 的 D 项用变化率、I 项用累积；互补滤波里 rate × dt 那一步就是对陀螺仪积分。形式化的导数记号见「导数记号 q′、q″ 与偏导（雅可比）」一条。",
      en: "The intuition behind the derivative: the average rate of change of a quantity over a small window dt, (x[t+dt] − x[t]) / dt — the smaller the window, the closer to the true rate. The integral is the reverse operation: repeatedly adding value × dt to get an accumulated quantity. Every control loop does both at once — an encoder accumulates counts first, and dividing by the window turns them into speed; PID's D term uses a rate and its I term an accumulation; the complementary filter's rate × dt step integrates the gyro. The formal derivative notation has its own entry, q′, q″, partial derivatives (Jacobian).",
    },
    example: {
      zh: "第 3 个月《PID 与控制：积分饱和与串级回路》\nD 项是变化率：rate = (测量 − 上次测量) / dt，200 Hz 循环下 dt = 0.005 s。\nI 项是累积：integral += error × dt，起步时误差是 60°，电机已饱和在 1 N·m；若误差在 0.1 s 内保持 60°，积分累积 60 × 0.1 = 6 °·s，Ki = 0.1 时 I 项为 0.1 × 6 = 0.6 N·m，Ki = 0.4 时为 0.4 × 6 = 2.4 N·m。电机输出不了这些额外力矩，积分却一直保留着，这就是积分饱和。\n编码器测速也是变化率：串级平衡车每计数 0.00227 m，外环 25 Hz 的 40 ms 窗口里多一个计数，速度就多 0.00227 / 0.04 = 0.057 m/s；位置本身就是计数的累积。",
      en: "Month 3 · PID & control: windup and cascade loops\nThe D term is a rate: rate = (measurement − previous measurement) / dt, with dt = 0.005 s in the 200 Hz loop.\nThe I term is an accumulation: integral += error × dt — at the start the error is 60° and the motor is already saturated at 1 N·m; if the error stays at 60° for 0.1 s, the integral accumulates 60 × 0.1 = 6 °·s, so the I term is 0.1 × 6 = 0.6 N·m with Ki = 0.1 and 0.4 × 6 = 2.4 N·m with Ki = 0.4. The motor cannot deliver this extra torque, yet the integral keeps it; that is windup.\nEncoder speed is a rate as well: the cascade balancer moves 0.00227 m per count, so one extra count in the 40 ms window of the 25 Hz outer loop adds 0.00227 / 0.04 = 0.057 m/s; position itself is the accumulated count.",
    },
    lessons: ["pid-control", "motors-drivers", "sensors-fusion"],
    links: [
      {
        label: "OpenStax · Calculus Volume 1 · 3.1 Defining the Derivative",
        url: "https://openstax.org/books/calculus-volume-1/pages/3-1-defining-the-derivative",
      },
      {
        label: "OpenStax · Calculus Volume 1 · 5.1 Approximating Areas",
        url: "https://openstax.org/books/calculus-volume-1/pages/5-1-approximating-areas",
      },
    ],
  },
  {
    id: "stddev-rms",
    title: { zh: "均值、标准差与 RMS", en: "Mean, standard deviation and RMS" },
    definition: {
      zh: "均值 = Σx / n，是数据的中心。样本标准差 = √(Σ(x − x̄)² / (n − 1))，描述围绕均值的典型偏差，分母 n − 1 是小样本修正。RMS = √(Σx² / n) 不减均值：对零均值信号，RMS 就是标准差；正弦信号的 RMS 是峰值的 1/√2 ≈ 0.707。均值说「整体偏多少」，标准差说「散得多开」，RMS 说「幅度多大」。",
      en: "The mean is Σx / n, the centre of the data. The sample standard deviation is √(Σ(x − x̄)² / (n − 1)), the typical deviation about the mean, with the denominator n − 1 correcting for small samples. RMS = √(Σx² / n) skips the mean: for a zero-mean signal the RMS is its standard deviation, and the RMS of a sine is peak/√2 ≈ 0.707 of the peak. The mean says how far the whole batch is biased, the standard deviation how widely it scatters, the RMS how large the amplitude is.",
    },
    example: {
      zh: "第 2 个月《传感器、I2C 与互补滤波》\nfilter_sim.py 里陀螺仪静止读数 = 偏置 1.5 °/s + 标准差 0.3 °/s 的零均值噪声：均值 1.5 °/s，标准差 0.3 °/s，RMS = √(1.5² + 0.3²) = 1.530 °/s。\n噪声部分单独看是零均值，所以它的 RMS 就是标准差 0.3 °/s。\n静止时平均 100 个样本来估计偏置，均值的标准差降到 0.3 / √100 = 0.03 °/s。\nα = 0.98 那一行：平放时误差的均值（offset_flat）0.72°，离散度（noise_flat，脚本按 n 计算）0.07°，误差的 RMS = √(0.72² + 0.07²) = 0.72°，几乎全部来自偏移。",
      en: "Month 2 · Sensors, I2C & the complementary filter\nIn filter_sim.py the gyro at rest reads a 1.5 °/s bias plus zero-mean noise with a 0.3 °/s standard deviation: mean 1.5 °/s, standard deviation 0.3 °/s, RMS = √(1.5² + 0.3²) = 1.530 °/s.\nThe noise part alone has zero mean, so its RMS is its standard deviation, 0.3 °/s.\nAveraging 100 samples at rest to estimate the bias brings the standard deviation of that mean down to 0.3 / √100 = 0.03 °/s.\nThe α = 0.98 row: while flat the error has mean (offset_flat) 0.72° and spread (noise_flat, computed by the script with n) 0.07°, so the RMS error is √(0.72² + 0.07²) = 0.72°, almost all of it offset.",
    },
    lessons: ["sensors-fusion"],
    links: [
      {
        label: "OpenStax · Introductory Statistics 2e · 2.7 Measures of the Spread of the Data",
        url: "https://openstax.org/books/introductory-statistics-2e/pages/2-7-measures-of-the-spread-of-the-data",
      },
      {
        label: "OpenStax · Introductory Statistics 2e · 2.3 Measures of the Location of the Data",
        url: "https://openstax.org/books/introductory-statistics-2e/pages/2-3-measures-of-the-location-of-the-data",
      },
    ],
  },
  {
    id: "radians-trig",
    title: { zh: "弧度、三角函数与 atan2", en: "Radians, sin/cos and atan2" },
    definition: {
      zh: "弧度是角度的国际单位：弧长等于半径时对应的角是 1 rad，转一整圈是 2π rad，所以 1 rad = 180/π ≈ 57.3°。sin、cos 把角度映到 [−1, 1]，在机器人代码里输入的一律是弧度。atan2(y, x) 是带象限的反正切，返回弧度、范围 (−π, π]，它给出向量 (x, y) 的方向角，向量的长度则是 √(x² + y²)。",
      en: "A radian is the angle for which the arc length equals the radius: a full turn is 2π rad, so 1 rad = 180/π ≈ 57.3°. sin and cos map an angle to [−1, 1], and robot code always feeds them radians. atan2(y, x) is the quadrant-aware arctangent: it returns radians in (−π, π] so it gives the direction of the vector (x, y), whose length is √(x² + y²).",
    },
    example: {
      zh: "第 5 个月《运动学：正解、数值逆解与奇异点》\nq = [30, 45, −60]°，于是 q1 + q2 = −15°。\nr = 0.12 × cos 45° + 0.14 × cos(−15°) = 0.12 × 0.7071 + 0.14 × 0.9659 = 0.2201 m\nx = 0.2201 × cos 30° = 0.1906 m，y = 0.2201 × sin 30° = 0.1100 m",
      en: "Month 5 · Kinematics: forward, numerical IK and singularities\nQ = [30, 45, −60]°, so q1 + q2 = −15°.\nr = 0.12 × cos 45° + 0.14 × cos(−15°) = 0.12 × 0.7071 + 0.14 × 0.9659 = 0.2201 m\nx = 0.2201 × cos 30° = 0.1906 m, y = 0.2201 × sin 30° = 0.1100 m",
    },
    lessons: ["kinematics-ik", "sensors-fusion", "control-modelling", "urdf-tf"],
    links: [
      {
        label: "OpenStax · Algebra and Trigonometry 2e · 7.1 Angles",
        url: "https://openstax.org/books/algebra-and-trigonometry-2e/pages/7-1-angles",
      },
      {
        label: "OpenStax · Algebra and Trigonometry 2e · 8.3 Inverse Trigonometric Functions",
        url: "https://openstax.org/books/algebra-and-trigonometry-2e/pages/8-3-inverse-trigonometric-functions",
      },
    ],
  },
  {
    id: "vectors",
    title: { zh: "向量：加法、点积、范数与欧氏距离", en: "Vectors: addition, dot product, norm, Euclidean distance" },
    definition: {
      zh: "向量既有大小又有方向，写成列 a = [a1, a2]ᵀ；加法逐分量相加，数乘把每个分量乘以标量。点积 a·b = a1b1 + a2b2 = |a| |b| cos θ，衡量两个方向的夹角。范数是 |a| = √(a1² + a2²)，两点之间的欧氏距离就是差向量的范数 ‖p − q‖。机器人里的位姿、速度、力与关节速度都是向量，v = J q′ 就是关节速度到末端速度的线性关系。",
      en: "A vector has magnitude and direction, written as a column a = [a1, a2]ᵀ; addition adds components and scalar multiplication scales each one. The dot product a·b = a1b1 + a2b2 = |a| |b| cos θ measures the angle between two directions. The norm is |a| = √(a1² + a2²), and the Euclidean distance between two points is the norm of the difference, ‖p − q‖. Poses, velocities, forces and joint rates on a robot are all vectors, and v = J q′ is the linear map from joint rates to tip velocity.",
    },
    example: {
      zh: "第 6 个月《模仿学习（二）：多模态示范、动作分块（ACT）与扩散策略》\n从岔口 (0, 0.23) 出发，方向 (−0.3, 0.2) 的长度是 √(0.3² + 0.2²) = √0.13 = 0.361 m。\n走 5 cm 的一步，横向分量 = 5 × 0.3 / 0.361 = 4.16 cm。",
      en: "Month 6 · Imitation learning II: multimodal demos, action chunking (ACT) and diffusion policy\nLeaving the fork at (0, 0.23) along the direction (−0.3, 0.2), whose length is √(0.3² + 0.2²) = √0.13 = 0.361 m.\nA 5 cm step therefore has a sideways part of 5 × 0.3 / 0.361 = 4.16 cm.",
    },
    lessons: ["act-diffusion", "gazebo-sim", "kinematics-ik", "urdf-tf"],
    links: [
      {
        label: "OpenStax · Precalculus 2e · 8.8 Vectors",
        url: "https://openstax.org/books/precalculus-2e/pages/8-8-vectors",
      },
      {
        label: "OpenStax · Calculus Volume 3 · 2.3 The Dot Product",
        url: "https://openstax.org/books/calculus-volume-3/pages/2-3-the-dot-product",
      },
    ],
  },
  {
    id: "matrices",
    title: { zh: "矩阵：矩阵–向量乘积、单位阵、对角阵、转置与求逆", en: "Matrices: matrix–vector product, identity, diag, transpose, inverse" },
    definition: {
      zh: "矩阵是按行列排好的数表；矩阵–向量乘积 y = A x 把 x 映成 y，状态空间模型 x′ = A x + B u 就是这样写的。单位阵 I 满足 I x = x，对角阵 diag(d1, …, dn) 只有对角线上非零，转置 Aᵀ 互换行列，A⁻¹ 只在 A 非奇异时存在并满足 A A⁻¹ = I。Riccati 迭代 P ← Q + Aᵀ P A − Aᵀ P B (R + Bᵀ P B)⁻¹ Bᵀ P A 正是这几种运算的组合。",
      en: "A matrix is a rectangular array of numbers; the matrix–vector product y = A x maps x to y, which is how the state-space model x′ = A x + B u is written. The identity I satisfies I x = x, a diagonal matrix diag(d1, …, dn) has entries only on its diagonal, the transpose Aᵀ swaps rows with columns, and A⁻¹ exists only when A is nonsingular and satisfies A A⁻¹ = I. The Riccati iteration P ← Q + Aᵀ P A − Aᵀ P B (R + Bᵀ P B)⁻¹ Bᵀ P A is nothing but these operations combined.",
    },
    example: {
      zh: "第 5 个月《状态空间、LQR 与 MPC》\n关节 J = 0.004 kg·m²、B = 0.05 N·m/(rad/s)。\nw′ = −(B/J) w + (1/J) u = −12.5 w + 250 u，所以 A = [[0, 1], [0, −12.5]]、B = [[0], [250]]。\n取 Q = diag(400, 0.01)、R = 1，LQR 给出 K = [15.93, 0.323]，即 u = −K x = −15.93 q − 0.323 w。",
      en: "Month 5 · State space, LQR and MPC\nThe joint has J = 0.004 kg·m² and B = 0.05 N·m per rad/s.\nw′ = −(B/J) w + (1/J) u = −12.5 w + 250 u, so A = [[0, 1], [0, −12.5]] and B = [[0], [250]].\nWith Q = diag(400, 0.01) and R = 1 the LQR gains are K = [15.93, 0.323], i.e. u = −K x = −15.93 q − 0.323 w.",
    },
    lessons: ["state-space-lqr", "kinematics-ik", "camera-calibration", "urdf-tf"],
    links: [
      {
        label: "Boyd & Vandenberghe · Introduction to Applied Linear Algebra · 6.4 Matrix-vector multiplication",
        url: "https://web.stanford.edu/~boyd/vmls/vmls.pdf",
      },
      {
        label: "Boyd & Vandenberghe · Introduction to Applied Linear Algebra · 11.2 Inverse",
        url: "https://web.stanford.edu/~boyd/vmls/vmls.pdf",
      },
      {
        label: "Åström & Murray · Feedback Systems (2nd ed., free) · Chapter 3: System Modeling",
        url: "https://fbswiki.org/",
      },
    ],
  },
  {
    id: "transforms",
    title: { zh: "旋转矩阵、齐次变换与变换复合", en: "Rotation matrices, homogeneous transforms, composing transforms" },
    definition: {
      zh: "旋转矩阵 R（3×3，正交且 det R = +1）把向量从一个坐标系搬到另一个；绕 z 轴转 θ 的矩阵是 [[cos θ, −sin θ, 0], [sin θ, cos θ, 0], [0, 0, 1]]。齐次变换把旋转和平移放进同一个 4×4 矩阵 T = [[R, p], [0, 1]]，T 乘以齐次点 [x, y, z, 1]ᵀ 就得到该点在另一坐标系中的坐标。复合就是连乘：先 T₁ 后 T₂ 等于乘 T₂ T₁，次序换一下结果就变，这是「变换顺序」出错的根源。",
      en: "A rotation matrix R (3×3, orthogonal with det R = +1) carries vectors from one frame into another; rotation by θ about z is [[cos θ, −sin θ, 0], [sin θ, cos θ, 0], [0, 0, 1]]. A homogeneous transform packs rotation and translation into one 4×4 matrix T = [[R, p], [0, 1]], and T times a homogeneous point [x, y, z, 1]ᵀ gives the point's coordinates in the other frame. Composing transforms is multiplication: applying T₁ and then T₂ means multiplying by T₂ T₁, and the order matters — the usual source of transform-order bugs.",
    },
    example: {
      zh: "第 4 个月《URDF 与 TF：描述一台机器人》\n云台 pan 30° 时 tf2_echo 给出 base_link → camera_link 的平移 [−0.043, 0.010, 0.305] m。\n手算：x = 0.02 × cos 30° = 0.0173，加桅杆的 −0.06 得 −0.0427 ≈ −0.043；y = 0.02 × sin 30° = 0.0100；z = 0.07 + 0.20 + 0.035 = 0.305。\n同一输出里的 4×4 齐次矩阵，左上 3×3 是旋转（0.866 = cos 30°），最右一列是平移。",
      en: "Month 4 · URDF and TF: describing a robot\nWith the head panned 30°, tf2_echo reports the base_link → camera_link translation [−0.043, 0.010, 0.305] m.\nBy hand: x = 0.02 × cos 30° = 0.0173 plus the mast's −0.06 gives −0.0427 ≈ −0.043; y = 0.02 × sin 30° = 0.0100; z = 0.07 + 0.20 + 0.035 = 0.305.\nThe same output's 4×4 homogeneous matrix carries the rotation (0.866 = cos 30°) in its top-left 3×3 block and the translation in its last column.",
    },
    lessons: ["urdf-tf", "kinematics-ik", "gazebo-sim"],
    links: [
      {
        label: "Lynch & Park · Modern Robotics · 3.3.1 Homogeneous Transformation Matrices",
        url: "https://hades.mech.northwestern.edu/images/2/25/MR-v2.pdf",
      },
      {
        label: "Lynch & Park · Modern Robotics Videos · Chapter 3: Rigid-Body Motions",
        url: "https://hades.mech.northwestern.edu/index.php/Modern_Robotics_Videos#Chapter_3:_Rigid-Body_Motions",
      },
    ],
  },
  {
    id: "rpy-quaternion",
    title: { zh: "欧拉角（RPY）、旋转顺序与四元数", en: "RPY Euler angles, rotation order, quaternions" },
    definition: {
      zh: "一个三维朝向可以写成按固定顺序施加的三个旋转；URDF 里的 rpy = (roll, pitch, yaw) 依次绕 x、y、z 轴旋转，这个顺序是定义的一部分，换顺序同样的数字就是另一个姿态。四元数 q = (x, y, z, w) 用绕轴 n 转 θ 角表示同一个旋转，没有万向锁奇异点，所以 TF 存四元数而不是欧拉角。同一个朝向有多种写法，URDF 用 rpy、TF 用四元数，互转时必须把顺序和约定写下来。",
      en: "A 3D orientation can be written as three rotations applied in a fixed order; URDF's rpy = (roll, pitch, yaw) rotates about x, then y, then z, and that order is part of the definition — the same three numbers under another order are another pose. A quaternion q = (x, y, z, w) stores the same rotation as an axis n and an angle θ, has no gimbal-lock singularity, and is therefore what TF keeps instead of Euler angles. One orientation has several representations, so URDF (rpy) and TF (quaternion) only agree once the order and the conventions are written down.",
    },
    example: {
      zh: "第 4 个月《URDF 与 TF：描述一台机器人》\npan 30°、tilt 0° 时 tf2_echo 同时给出\n四元数 (xyzw) = [0.000, 0.000, 0.259, 0.966]，RPY（弧度）= [0.000, −0.000, 0.524]，RPY（度）= [0.000, −0.000, 30.000]。\n0.259 = sin 15°、0.966 = cos 15°，正好是 30° 的一半角。",
      en: "Month 4 · URDF and TF: describing a robot\nWith pan 30° and tilt 0°, tf2_echo reports\nquaternion (xyzw) = [0.000, 0.000, 0.259, 0.966], RPY (radian) = [0.000, −0.000, 0.524], RPY (degree) = [0.000, −0.000, 30.000].\n0.259 = sin 15° and 0.966 = cos 15°, the half-angle of that 30° yaw.",
    },
    lessons: ["urdf-tf", "slam-nav"],
    links: [
      {
        label: "Lynch & Park · Modern Robotics · Appendix B: Other Representations of Rotations",
        url: "https://hades.mech.northwestern.edu/images/2/25/MR-v2.pdf",
      },
    ],
  },
  {
    id: "det-rank",
    title: { zh: "行列式、秩与条件数（奇异点）", en: "Determinant, rank, condition number (singularity)" },
    definition: {
      zh: "方阵的行列式是一个标量：det A = 0 当且仅当 A 奇异（不可逆），此时 A 把某些方向压成了零。矩阵的秩是线性无关的行（或列）的最大个数，秩亏意味着系统失去了某些方向，既不可控也不可观测。对雅可比矩阵，行列式直接给出离奇异点还有多远：|det J| → 0 表示某个末端方向需要无穷大的关节速度；条件数 κ(A) 衡量同一个扰动被放大多少倍，κ 很大就说明矩阵接近奇异。",
      en: "The determinant of a square matrix is a scalar: det A = 0 exactly when A is singular (not invertible), which means A squashes some directions to zero. The rank is the number of linearly independent rows (or columns), so a rank-deficient matrix has lost directions the system can neither control nor observe. For a Jacobian the determinant says how close a configuration is to a singularity: |det J| → 0 means some tip direction would need infinite joint speed. The condition number κ(A) measures how much A amplifies a small perturbation; a large κ means the matrix is close to singular.",
    },
    example: {
      zh: "第 5 个月《运动学：正解、数值逆解与奇异点》\n|det J| = L1 L2 r |sin(肘角)|，肩在 20°、肘 −60° 时 r = 0.2200 m。\n0.12 × 0.14 × 0.2200 × 0.8660 = 0.0032 m³，正是表里的 3.20e-03；肘角 = 0 时行列式归零。\n此时精确求逆要 7965.0 °/s，阻尼最小二乘只给 3.3 °/s，但末端在那个方向上根本动不了。",
      en: "Month 5 · Kinematics: forward, numerical IK and singularities: |det J| = L1 L2 r |sin(elbow)|; with the shoulder at 20° and the elbow at −60°, r = 0.2200 m.\n0.12 × 0.14 × 0.2200 × 0.8660 = 0.0032 m³, exactly the 3.20e-03 in the table; at elbow = 0 the determinant vanishes.\nThere the exact inverse asks for 7965.0 °/s while the damped solver returns 3.3 °/s — and the tip still cannot move in that direction.",
    },
    lessons: ["kinematics-ik", "moveit-pick-place"],
    links: [
      {
        label: "Lynch & Park · Modern Robotics · 5.3 Singularity Analysis",
        url: "https://hades.mech.northwestern.edu/images/2/25/MR-v2.pdf",
      },
      {
        label: "OpenStax · Calculus Volume 3 · 2.4 The Cross Product",
        url: "https://openstax.org/books/calculus-volume-3/pages/2-4-the-cross-product",
      },
    ],
  },
  {
    id: "eigen-stability",
    title: { zh: "特征值与稳定性（极点）", en: "Eigenvalues and stability (poles)" },
    definition: {
      zh: "连续状态矩阵 A 的特征值决定系统的模态：x′ = A x 的解是若干 e^(λt) 模态的组合。实部为负的特征值给出衰减模态，实部为正给出发散模态；传递函数的极点就是 A 的特征值，所以「极点在左半平面」就是连续时间系统稳定的条件。线性化只在平衡点附近有效：离平衡点越远，局部模型给出的预测越不可信。",
      en: "The eigenvalues of the continuous state matrix A set the modes of the system: the solution of x′ = A x is a sum of modal terms e^(λt). Eigenvalues with negative real part give decaying modes and positive real part give growing ones; the poles of a transfer function are the eigenvalues of A, so poles in the left half-plane is the stability condition for a continuous-time system. A linearisation is valid only near its equilibrium point, so the further the system is driven from it, the less the local model can be trusted.",
    },
    example: {
      zh: "第 5 个月《状态空间、LQR 与 MPC》\n小车倒立摆在直立位线性化后 A 的第四行是 [0, 0, 45.78, 0]，\n45.78 = (M + m) g / (M L) = (0.5 + 0.2) × 9.81 / (0.5 × 0.3) = 6.867 / 0.15 = 45.78 1/s²。\n摆角那两行给出 θ″ = 45.78 θ，特征值为 ±√45.78 = ±6.766 1/s；+6.766 对应随 e^(6.766 t) 增长的模态，所以直立位不稳定。\n同一组增益在非线性模型上最多只能从 53° 摆角救回来。",
      en: "Month 5 · State space, LQR and MPC\nLinearised about upright, row 4 of the cart-pole's A is [0, 0, 45.78, 0],\n45.78 = (M + m) g / (M L) = (0.5 + 0.2) × 9.81 / (0.5 × 0.3) = 6.867 / 0.15 = 45.78 1/s².\nThe two angle rows give θ″ = 45.78 θ, so the eigenvalues are ±√45.78 = ±6.766 1/s; +6.766 is a mode growing as e^(6.766 t), so upright is unstable.\nThe same gains recover from a start angle of 53° on the nonlinear model and no further.",
    },
    lessons: ["state-space-lqr", "control-modelling"],
    links: [
      {
        label: "Åström & Murray · Feedback Systems (2nd ed., free) · Chapter 5: Dynamic Behavior",
        url: "https://fbswiki.org/",
      },
      {
        label: "OpenStax · Calculus Volume 3 · 7.1 Second-Order Linear Equations",
        url: "https://openstax.org/books/calculus-volume-3/pages/7-1-second-order-linear-equations",
      },
    ],
  },
  {
    id: "derivatives",
    title: { zh: "导数记号 q′、q″ 与偏导（雅可比）", en: "Derivative notation q′, q″, partial derivatives (Jacobian)" },
    definition: {
      zh: "q′ 是位置对时间的导数（速度），q″ 是加速度；在代码里它们用差分近似：(q[k] − q[k−1]) / dt。多元函数对一个变量求导叫偏导 ∂f/∂x_i，其余变量保持不变；把所有偏导收集成矩阵就是雅可比 J = ∂p/∂q。机器人上雅可比既把关节速度变成末端速度 v = J q′，也决定某个末端方向能否被关节带动。",
      en: "q′ is the derivative of position with respect to time (velocity) and q″ is the acceleration; in code they are approximated by differences, (q[k] − q[k−1]) / dt. Differentiating one variable of a multivariable function and holding the others fixed gives a partial derivative ∂f/∂x_i; collecting all of them into a matrix gives the Jacobian J = ∂p/∂q. On a robot the Jacobian converts joint rates into tip velocity, v = J q′, and it also decides whether a direction in task space can be produced by the joints at all.",
    },
    example: {
      zh: "第 5 个月《运动学：正解、数值逆解与奇异点》\n脚本不做符号微分，而是数值求雅可比——算一次 FK(q)，再把 q_i 加 1e-6 rad 算一次 FK，两者相减除以 1e-6。\n从 q = [0, 30, −30]° 到目标 (0.10, 0.15, 0.12) m，误差从 208.120 mm 用 14 次迭代降到 0.009 mm。",
      en: "Month 5 · Kinematics: forward, numerical IK and singularities\nThe script does not differentiate symbolically — it computes a numerical Jacobian by evaluating FK(q), evaluating FK again with q_i nudged by 1e-6 rad, then subtracting and dividing by 1e-6.\nFrom q = [0, 30, −30]° towards (0.10, 0.15, 0.12) m the error falls from 208.120 mm to 0.009 mm in 14 iterations.",
    },
    lessons: ["kinematics-ik", "sensors-fusion", "pid-control"],
    links: [
      {
        label: "OpenStax · Calculus Volume 1 · 3.1 Defining the Derivative",
        url: "https://openstax.org/books/calculus-volume-1/pages/3-1-defining-the-derivative",
      },
      {
        label: "OpenStax · Calculus Volume 3 · 4.3 Partial Derivatives",
        url: "https://openstax.org/books/calculus-volume-3/pages/4-3-partial-derivatives",
      },
    ],
  },
  {
    id: "exp-first-order",
    title: { zh: "指数函数与一阶响应 e^(−t/τ)、63 %", en: "Exponential, first-order response e^(−t/τ), 63 %" },
    definition: {
      zh: "指数函数 e^(−t/τ) 描述一阶惯性环节的响应，τ 是时间常数，τ 越大响应越慢。t = τ 时响应到达最终值的 1 − e^(−1) ≈ 0.632，也就是常说的 63 %；2τ 时为 86.5 %，3τ 时为 95.0 %。一阶系统的传递函数是 1/(τ s + 1)，它的极点是 s = −1/τ。",
      en: "The exponential e^(−t/τ) describes the response of a first-order lag: τ is the time constant, and the larger τ is the slower the response. At t = τ the response has reached 1 − e^(−1) ≈ 0.632 of its final value — the familiar 63 %; at 2τ it is 86.5 % and at 3τ 95.0 %. The transfer function of a first-order system is 1/(τ s + 1), whose pole is s = −1/τ.",
    },
    example: {
      zh: "第 5 个月《控制理论：先建模，再看频域》\n关节 J = 0.004 kg·m²、B = 0.05 N·m/(rad/s)。\n时间常数 τ = J/B = 0.004 / 0.05 = 0.08 s，所以力矩阶跃之后速度在 0.08 s 达到最终值的 63 %。\n开环加 u = 0.2 N·m，终速应为 u/B = 0.2 / 0.05 = 4 rad/s；记录到 0.5 s（约六个时间常数）读到 3.99 rad/s，还差 0.2 %。",
      en: "Month 5 · Control theory: model the plant, then read the loop\nThe joint has J = 0.004 kg·m² and B = 0.05 N·m per rad/s.\nThe time constant is τ = J/B = 0.004 / 0.05 = 0.08 s, so after a torque step the speed reaches 63 % of its final value at 0.08 s.\nOpen loop with u = 0.2 N·m the ideal final speed is u/B = 0.2 / 0.05 = 4 rad/s; the log ends at 0.5 s, about six time constants, and reads 3.99 rad/s — still 0.2 % short.",
    },
    lessons: ["control-modelling", "pid-control", "first-robots"],
    links: [
      {
        label: "Åström & Murray · Feedback Systems (2nd ed., free) · Chapter 6: Linear Systems",
        url: "https://fbswiki.org/",
      },
      {
        label: "OpenStax · Calculus Volume 1 · 3.9 Derivatives of Exponential and Logarithmic Functions",
        url: "https://openstax.org/books/calculus-volume-1/pages/3-9-derivatives-of-exponential-and-logarithmic-functions",
      },
    ],
  },
  {
    id: "log-db",
    title: { zh: "对数与分贝", en: "Logarithms and decibels" },
    definition: {
      zh: "对数把乘除换成加减：log(ab) = log a + log b，log(aᵇ) = b log a，它也是指数函数的反函数。分贝是以 10 为底、用来表示比值的对数：dB = 20 log10(|L|)，其中 |L| 是幅值比。于是 0 dB 表示 |L| = 1，幅值放大 10 倍对应 20 dB。",
      en: "A logarithm turns products and quotients into sums and differences — log(ab) = log a + log b, log(aᵇ) = b log a — and it is the inverse of the exponential. The decibel is a base-10 logarithm used to express ratios: dB = 20 log10(|L|) for an amplitude ratio. So 0 dB means |L| = 1, and an amplitude ratio of 10 is 20 dB.",
    },
    example: {
      zh: "第 5 个月《控制理论：先建模，再看频域》\nkp = 2.86 N·m/rad、kd = 0.115 N·m/(rad/s) 时，|L| 在 1 rad/s 是 35.1 dB，在 30 rad/s 是 1.5 dB，在 100 rad/s 是 −10.3 dB。\n只用 P、kp = 1.0 时增益裕度为 16.6 dB，对应 10^(16.6/20) = 6.8 倍增益，所以回路在 kp ≈ 6.79 附近失稳。",
      en: "Month 5 · Control theory: model the plant, then read the loop\nWith kp = 2.86 N·m/rad and kd = 0.115 N·m/(rad/s), |L| is 35.1 dB at 1 rad/s, 1.5 dB at 30 rad/s and −10.3 dB at 100 rad/s.\nWith P only at kp = 1.0 the gain margin is 16.6 dB, a factor of 10^(16.6/20) = 6.8 in gain, so the loop turns unstable near kp ≈ 6.79.",
    },
    lessons: ["control-modelling"],
    links: [
      {
        label: "Åström & Murray · Feedback Systems (2nd ed., free) · Chapter 10: Frequency Domain Analysis",
        url: "https://fbswiki.org/",
      },
      {
        label: "OpenStax · Calculus Volume 1 · 3.9 Derivatives of Exponential and Logarithmic Functions",
        url: "https://openstax.org/books/calculus-volume-1/pages/3-9-derivatives-of-exponential-and-logarithmic-functions",
      },
    ],
  },
  {
    id: "complex",
    title: { zh: "复数、jω、幅值与相位", en: "Complex numbers, jω, magnitude and phase" },
    definition: {
      zh: "复数 a + jb 用 j² = −1 扩展实数；极坐标写法是 z = |z| e^(jφ)，幅值 |z| = √(a² + b²)，相位 φ = atan2(b, a)。在频域里把 Laplace 变量放到虚轴上，s = jω：|G(jω)| 是幅频响应，∠G(jω) 是相频响应。纯延迟 T 秒在频率 ω 处带来 ω T 弧度的相位滞后，所以延迟在高频处更贵。",
      en: "A complex number a + jb extends the reals with j² = −1; in polar form z = |z| e^(jφ), the magnitude is |z| = √(a² + b²) and the phase is φ = atan2(b, a). In the frequency domain the Laplace variable is placed on the imaginary axis, s = jω: |G(jω)| is the magnitude response and ∠G(jω) the phase response. A pure delay of T seconds costs ω T radians of phase, so delay is always more expensive at high frequency.",
    },
    example: {
      zh: "第 5 个月《控制理论：先建模，再看频域》\n控制器跑 200 Hz，脚本用 z = e^(jωT) 在复平面上求环路增益 L = C × P。\n在增益穿越频率 34.6 rad/s 处，一个采样周期的延迟就是 34.6 × 0.005 = 0.17 rad ≈ 10°，零阶保持再加约 5°。",
      en: "Month 5 · Control theory: model the plant, then read the loop\nThe controller runs at 200 Hz and the script evaluates the loop gain L = C × P on the complex plane with z = e^(jωT).\nAt the 34.6 rad/s gain crossover one sample of delay costs 34.6 × 0.005 = 0.17 rad ≈ 10°, and the zero-order hold adds about 5° more.",
    },
    lessons: ["control-modelling", "state-space-lqr"],
    links: [
      {
        label: "OpenStax · Precalculus 2e · 8.5 Polar Form of Complex Numbers",
        url: "https://openstax.org/books/precalculus-2e/pages/8-5-polar-form-of-complex-numbers",
      },
      {
        label: "Åström & Murray · Feedback Systems (2nd ed., free) · Chapter 10: Frequency Domain Analysis",
        url: "https://fbswiki.org/",
      },
    ],
  },
  {
    id: "laplace-freq",
    title: {
      zh: "拉普拉斯变换、传递函数、频响、伯德图与奈奎斯特频率",
      en: "Laplace transform, transfer function, frequency response, Bode plot, Nyquist frequency",
    },
    definition: {
      zh: "拉普拉斯变换把微分方程变成代数方程：s 把「求导」换成「乘以 s」；零初始条件下 Y(s) = G(s) U(s) 就定义了传递函数。G(s) 分母的根是极点，决定稳定性和响应速度，分子根是零点。把 s = jω 代入得到频响，幅值与相位画成伯德图；采样之后只能分辨低于奈奎斯特频率 ω_N = π/T 的内容，T 是采样周期。",
      en: "The Laplace transform turns differential equations into algebra: s replaces differentiation. With zero initial conditions Y(s) = G(s) U(s) defines the transfer function. The roots of its denominator are the poles, which set stability and speed; the roots of the numerator are the zeros. Putting s = jω gives the frequency response, whose magnitude and phase form the Bode plot. A sampled loop can only represent content below the Nyquist frequency ω_N = π/T, where T is the sampling period.",
    },
    example: {
      zh: "第 5 个月《控制理论：先建模，再看频域》\n关节模型 G(s) = 1 / (J s² + B s) = 1 / (s (J s + B))，两个极点是 s = 0 和 s = −B/J = −12.5 1/s。\n|L| 在 34.6 rad/s 穿过 0 dB（相位裕度 56°），相位在 150.8 rad/s 到达 −180°（增益裕度 14.2 dB）。\n控制器 200 Hz，T = 0.005 s，频率扫描的上限就是奈奎斯特频率 π/T ≈ 628 rad/s。",
      en: "Month 5 · Control theory: model the plant, then read the loop\nThe joint model G(s) = 1 / (J s² + B s) = 1 / (s (J s + B)) has poles at s = 0 and s = −B/J = −12.5 1/s.\n|L| crosses 0 dB at 34.6 rad/s (phase margin 56°) and the phase reaches −180° at 150.8 rad/s (gain margin 14.2 dB).\nThe controller runs at 200 Hz, so T = 0.005 s and the frequency sweep stops at the Nyquist frequency π/T ≈ 628 rad/s.",
    },
    lessons: ["control-modelling", "state-space-lqr", "pid-control"],
    links: [
      {
        label: "Åström & Murray · Feedback Systems (2nd ed., free) · Chapter 9: Transfer Functions",
        url: "https://fbswiki.org/",
      },
      {
        label: "Åström & Murray · Feedback Systems (2nd ed., free) · Chapter 10: Frequency Domain Analysis",
        url: "https://fbswiki.org/",
      },
    ],
  },
  {
    id: "linearise-discretise",
    title: { zh: "线性化（小角度）与离散化（零阶保持）", en: "Linearisation (small-angle) and discretisation (ZOH)" },
    definition: {
      zh: "线性化：在平衡点附近用一阶泰勒展开代替非线性模型，x ≈ x0 + A (x − x0)，A 是雅可比，只在该点附近有效。倒立摆在直立位线性化时用 sin θ ≈ θ、cos θ ≈ 1，于是得到常系数矩阵 A、B。离散化：把连续模型按采样周期 T 离散，零阶保持假设输入在每个周期内保持不变，得到 x[k+1] = Φ x[k] + Γ u[k]，其中 Φ = e^(A T)。",
      en: "Linearisation replaces a nonlinear model by its first-order Taylor expansion near an equilibrium, x ≈ x0 + A (x − x0), with A the Jacobian; it holds only near that point. Linearising the cart-pole about upright uses sin θ ≈ θ and cos θ ≈ 1, which yields constant matrices A and B. Discretisation turns the continuous model into a sampled one with period T; the zero-order hold assumes the input stays constant over each period, giving x[k+1] = Φ x[k] + Γ u[k] with Φ = e^(A T).",
    },
    example: {
      zh: "第 5 个月《状态空间、LQR 与 MPC》\n小车倒立摆 M = 0.5 kg、m = 0.2 kg、L = 0.3 m，绕直立位线性化后\nA 的第二行是 [0, 0, −3.92, 0]，其中 −3.92 = −m g / M = −0.2 × 9.81 / 0.5；\n第四行是 [0, 0, 45.78, 0]，其中 45.78 = (M + m) g / (M L) = 0.7 × 9.81 / 0.15。\n控制器跑 100 Hz，所以模型按 T = 0.01 s 用零阶保持离散。",
      en: "Month 5 · State space, LQR and MPC\nFor the cart-pole with M = 0.5 kg, m = 0.2 kg and L = 0.3 m, linearised about upright\nrow 2 of A is [0, 0, −3.92, 0] with −3.92 = −m g / M = −0.2 × 9.81 / 0.5,\nrow 4 is [0, 0, 45.78, 0] with 45.78 = (M + m) g / (M L) = 0.7 × 9.81 / 0.15.\nThe controller runs at 100 Hz, so the model is discretised with a zero-order hold over T = 0.01 s.",
    },
    lessons: ["state-space-lqr", "control-modelling"],
    links: [
      {
        label: "Åström & Murray · Feedback Systems (2nd ed., free) · Chapter 6: Linear Systems",
        url: "https://fbswiki.org/",
      },
      {
        label: "OpenStax · Calculus Volume 3 · 4.4 Tangent Planes and Linear Approximations",
        url: "https://openstax.org/books/calculus-volume-3/pages/4-4-tangent-planes-and-linear-approximations",
      },
    ],
  },
  {
    id: "optimisation",
    title: { zh: "argmin、最小二乘与梯度下降", en: "argmin, least squares, gradient descent" },
    definition: {
      zh: "argmin_x J(x) 给出使目标函数 J 最小的那个自变量；最小二乘就是 argmin ‖Ax − b‖²，正规方程给出解析解 (AᵀA)⁻¹ Aᵀ b。目标不可微或带约束时改用梯度下降，沿 −∇J(x) 更新 x ← x − η ∇J(x)，步长 η 与迭代次数决定能否收敛。MPC 把「先预测再优化」搬上实时回路：每个控制周期只执行最优序列的第一步，然后重新规划。",
      en: "argmin_x J(x) returns the argument that minimises the objective J; least squares is argmin ‖Ax − b‖², whose solution is the normal equation (AᵀA)⁻¹ Aᵀ b. When the objective is non-smooth or constrained, gradient descent steps along −∇J(x): x ← x − η ∇J(x), and the step size η together with the iteration count decides whether it converges. MPC puts predict-then-optimise on the real-time loop: at every control period only the first step of the optimal sequence is applied, then the plan is rebuilt.",
    },
    example: {
      zh: "第 5 个月《状态空间、LQR 与 MPC》\nMPC 在 |u| ≤ 0.6 N·m 的约束下最小化 Σ kq (q − 目标)² + 0.01 w² + u²，\n用投影梯度下降求解，每个 5 ms 周期跑 150 步、前瞻 40 步（40 × 5 ms = 0.2 s）。\n结果：MPC 超调 0.86°、0.160 s 进入 1°；被削顶的 LQR 超调 2.24°、0.210 s 才进入 1°。",
      en: "Month 5 · State space, LQR and MPC\nThe MPC minimises Σ kq (q − target)² + 0.01 w² + u² subject to |u| ≤ 0.6 N·m,\nsolved by projected gradient descent: 150 steps per 5 ms period over a 40-step horizon (40 × 5 ms = 0.2 s).\nResult: MPC overshoots 0.86° and is within 1° from 0.160 s; the clipped LQR overshoots 2.24° and reaches 1° only at 0.210 s.",
    },
    lessons: ["state-space-lqr", "moveit-pick-place", "behaviour-cloning"],
    links: [
      {
        label: "Boyd & Vandenberghe · Introduction to Applied Linear Algebra · 12.1 Least squares problem",
        url: "https://web.stanford.edu/~boyd/vmls/vmls.pdf",
      },
      {
        label: "Boyd & Vandenberghe · Introduction to Applied Linear Algebra · 18.1 Nonlinear equations and least squares",
        url: "https://web.stanford.edu/~boyd/vmls/vmls.pdf",
      },
      {
        label: "Lynch & Park · Modern Robotics · Appendix D: Optimization and Lagrange Multipliers",
        url: "https://hades.mech.northwestern.edu/images/2/25/MR-v2.pdf",
      },
    ],
  },
  {
    id: "inertia",
    title: { zh: "惯量张量与平行轴定理", en: "Inertia tensor and the parallel-axis theorem" },
    definition: {
      zh: "惯量张量 I 描述刚体绕各轴转动的难易，单位 kg·m²；均匀长方体的分量是 Ixx = m/12 (y² + z²)、Iyy = m/12 (x² + z²)、Izz = m/12 (x² + y²)。平行轴定理把惯量搬到另一个原点：绕平行轴时 I_O = I_C + m d²，d 是两轴间距。惯量写错——取错原点、质量为零，或违反三角不等式 Ixx + Iyy ≥ Izz——会让物理引擎在仿真里抖动甚至穿透地面。",
      en: "The inertia tensor I describes how hard a body is to spin about each axis, in kg·m²; for a uniform box the components are Ixx = m/12 (y² + z²), Iyy = m/12 (x² + z²) and Izz = m/12 (x² + y²). The parallel-axis theorem moves the inertia to another origin: for parallel axes I_O = I_C + m d², with d the distance between them. A wrong inertia — taken about the wrong origin, with zero mass, or breaking the triangle rule Ixx + Iyy ≥ Izz — makes a physics engine jitter or sink through the floor in simulation.",
    },
    example: {
      zh: "第 4 个月《URDF 与 TF：描述一台机器人》\nm4bot 底盘是 m = 2.0 kg 的长方体，0.30 × 0.24 × 0.08 m。\nIxx = 2.0/12 × (0.24² + 0.08²) = 0.010667 kg·m²，Iyy = 2.0/12 × (0.30² + 0.08²) = 0.016067 kg·m²，\nIzz = 2.0/12 × (0.30² + 0.24²) = 0.024600 kg·m²。\n底盘中心在轮轴前方 0.05 m（chassis_offset_x）。绕轮轴中点原地转向时，按平行轴定理 Izz(轴) = 0.024600 + 2.0 × 0.05² = 0.024600 + 0.005 = 0.029600 kg·m²；偏移沿 x 方向，所以 Ixx 不变。（这一行是按课程数据计算的，课文本身没有。）",
      en: "Month 4 · URDF and TF: describing a robot\nThe m4bot chassis is a box of m = 2.0 kg measuring 0.30 × 0.24 × 0.08 m.\nIxx = 2.0/12 × (0.24² + 0.08²) = 0.010667 kg·m², Iyy = 2.0/12 × (0.30² + 0.08²) = 0.016067 kg·m²,\nIzz = 2.0/12 × (0.30² + 0.24²) = 0.024600 kg·m².\nThe chassis centre sits 0.05 m ahead of the axle (chassis_offset_x). For turning in place about the axle midpoint, the parallel-axis theorem gives Izz(axle) = 0.024600 + 2.0 × 0.05² = 0.024600 + 0.005 = 0.029600 kg·m²; the offset lies along x, so Ixx is unchanged. (This line is computed from the course data; the lesson itself does not show it.)",
    },
    lessons: ["urdf-tf", "gazebo-sim", "state-space-lqr", "pid-control", "transmissions"],
    links: [
      {
        label: "OpenStax · University Physics Volume 1 · 10.4 Moment of Inertia and Rotational Kinetic Energy",
        url: "https://openstax.org/books/university-physics-volume-1/pages/10-4-moment-of-inertia-and-rotational-kinetic-energy",
      },
      {
        label: "OpenStax · University Physics Volume 1 · 10.5 Calculating Moments of Inertia",
        url: "https://openstax.org/books/university-physics-volume-1/pages/10-5-calculating-moments-of-inertia",
      },
      {
        label: "Lynch & Park · Modern Robotics · 8.1.3 Understanding the Mass Matrix",
        url: "https://hades.mech.northwestern.edu/images/2/25/MR-v2.pdf",
      },
    ],
  },
  {
    id: "gaussian",
    title: { zh: "概率、高斯分布、标准差与方差相加", en: "Probability, Gaussian distribution, standard deviation, adding variances" },
    definition: {
      zh: "概率是 0 到 1 之间的数，描述事件发生的可能性；独立事件的联合概率是各自概率的乘积。高斯（正态）分布 N(μ, σ²) 的密度是 (1 / (σ√(2π))) e^(−(x−μ)²/(2σ²))，其中 σ 是标准差。独立误差叠加时方差相加：σ_total² = σ1² + σ2² + …，所以 n 步同样大小的独立噪声累积出来的标准差是 σ√n。",
      en: "A probability is a number between 0 and 1 describing how likely an event is; the joint probability of independent events is the product of their probabilities. The Gaussian (normal) density is (1 / (σ√(2π))) e^(−(x−μ)²/(2σ²)), with σ the standard deviation. Independent errors add in quadrature: σ_total² = σ1² + σ2² + …, so n steps of independent noise of the same size accumulate a standard deviation of σ√n.",
    },
    example: {
      zh: "第 6 个月《模仿学习（一）：示范数据、行为克隆与 DAgger》\n夹爪每步有 1 cm 的独立执行器噪声，38 步之后单轴漂移的标准差是 1 cm × √38 = 6.2 cm。\n走廊半宽只有 10 cm，所以一个从不修正方向的策略有实打实的概率撞墙。",
      en: "Month 6 · Imitation learning I: demonstrations, behaviour cloning and DAgger\nThe gripper takes 1 cm of independent actuator noise per step, so after 38 steps the one-axis drift has a standard deviation of 1 cm × √38 = 6.2 cm.\nThe corridor is only 10 cm half-width, so a policy that never steers back has a real chance of hitting a wall.",
    },
    lessons: ["behaviour-cloning", "gazebo-sim", "sensors-fusion", "policy-evaluation"],
    links: [
      {
        label: "OpenStax · Introductory Statistics 2e · 6.1 The Standard Normal Distribution",
        url: "https://openstax.org/books/introductory-statistics-2e/pages/6-1-the-standard-normal-distribution",
      },
      {
        label: "OpenStax · Introductory Statistics 2e · 2.7 Measures of the Spread of the Data",
        url: "https://openstax.org/books/introductory-statistics-2e/pages/2-7-measures-of-the-spread-of-the-data",
      },
    ],
  },
  {
    id: "bayes",
    title: { zh: "似然与后验（贝叶斯）", en: "Likelihood and posterior (Bayes)" },
    definition: {
      zh: "似然是「在某个假设下看到这批数据的可能性」，后验是「看到数据之后这个假设为真的概率」，两者由先验联系起来。贝叶斯公式是 P(假设 | 数据) = P(数据 | 假设) P(假设) / P(数据)，分母把各个假设的似然归一化。在参数估计里它就是「先验 × 似然 ∝ 后验」，扩散模型每一步去噪算的正是这个加权平均。",
      en: "The likelihood is how probable the data are under a hypothesis; the posterior is how probable the hypothesis is given the data. The two are tied together by the prior. Bayes' rule reads P(hypothesis | data) = P(data | hypothesis) P(hypothesis) / P(data), where the denominator normalises the likelihoods of the competing hypotheses. In parameter estimation this is prior × likelihood ∝ posterior, and each denoising step of a diffusion model computes exactly that weighted average.",
    },
    example: {
      zh: "第 6 个月《模仿学习（二）：多模态示范、动作分块（ACT）与扩散策略》\n精确去噪器把 10 个最近的示范帧按「各自产生当前噪声样本的可能性」加权平均，就是一次贝叶斯更新。\n这 10 帧里 7 个向左、3 个向右（每个横向约 4.2 cm），200 次采样得到 144 : 56，与示范的 7 : 3 一致；\n而取平均的策略每次都落在 −3 到 −1 cm 那一格，也就是 (−7 + 3)/10 × 4.16 = −1.66 cm。",
      en: "Month 6 · Imitation learning II: multimodal demos, action chunking (ACT) and diffusion policy\nThe exact denoiser weights the 10 nearest demonstration frames by how likely each is to have produced the current noisy sample — a Bayesian update.\nSeven of those frames go left and three go right (about 4.2 cm sideways each), and 200 draws come out 144 : 56, matching the data's 7 : 3;\nthe averaging policy instead lands in the −3 to −1 cm bin every time, namely (−7 + 3)/10 × 4.16 = −1.66 cm.",
    },
    lessons: ["act-diffusion", "sensors-fusion", "policy-evaluation"],
    links: [
      {
        label: "Goodfellow et al. · Deep Learning · Chapter 3: Probability Theory",
        url: "https://www.deeplearningbook.org/contents/prob.html",
      },
      {
        label: "Goodfellow et al. · Deep Learning · Chapter 6: Deep Feedforward Networks",
        url: "https://www.deeplearningbook.org/contents/mlp.html",
      },
    ],
  },
  {
    id: "percentile-norm",
    title: { zh: "百分位数、归一化与均值 vs 中位数", en: "Percentiles, normalisation, mean vs median" },
    definition: {
      zh: "百分位数把排序后的数据分成 100 份：第 p 百分位数是有 p % 的数据不超过它的那个值，中位数就是 50 百分位数。归一化把数值映射到固定区间（常用 −1..1 或 0..1），让量纲不再影响计算；机器人上常用数据集的 1 与 99 百分位数做 min-max 归一化，落在范围之外的值被截断。均值对极端值敏感，中位数不敏感，所以同一组数据的均值和中位数可以差很远。",
      en: "A percentile cuts sorted data into 100 parts: the p-th percentile is the value that p % of the data do not exceed, and the median is the 50th percentile. Normalisation maps values onto a fixed range (−1..1 or 0..1) so that units stop mattering; on robots the 1st and 99th percentiles of the dataset are often used for min–max normalisation, with values outside them clipped. The mean is sensitive to outliers and the median is not, so for the same data the two can be far apart.",
    },
    example: {
      zh: "第 6 个月《VLA 模型：动作如何变成词元，哪些开放权重》\n某个关节的第 1 到第 99 百分位范围是 −84° 到 +77°，跨度 161°。\n切成 256 个区间，每个区间宽 (77 − (−84)) / 256 = 161 / 256 = 0.63°，范围内的值能还原到 0.31° 以内。\n超出范围的 6 个值被截断，最大误差就来自那里：6.194°。",
      en: "Month 6 · VLA models: how actions become tokens, and which have open weights\nOne joint's 1st-to-99th-percentile range is −84° to +77°, a span of 161°.\nCut into 256 bins, each bin is (77 − (−84)) / 256 = 161 / 256 = 0.63° wide, and a value inside the range is reconstructed to within 0.31°.\nThe 6 values outside the range are clipped, and that is where the maximum error comes from: 6.194°.",
    },
    lessons: ["vla-models", "behaviour-cloning", "policy-evaluation"],
    links: [
      {
        label: "OpenStax · Introductory Statistics 2e · 2.3 Measures of the Location of the Data",
        url: "https://openstax.org/books/introductory-statistics-2e/pages/2-3-measures-of-the-location-of-the-data",
      },
      {
        label: "Boyd & Vandenberghe · Introduction to Applied Linear Algebra · 3.3 Standard deviation",
        url: "https://web.stanford.edu/~boyd/vmls/vmls.pdf",
      },
    ],
  },
  {
    id: "nn-loss",
    title: { zh: "神经网络、监督学习与损失函数", en: "Neural networks, supervised learning, loss function" },
    definition: {
      zh: "监督学习是「输入–标签」配对：观测 o 是输入，专家动作 a 是标签，训练的目标就是缩小预测与标签之间的差距。损失函数把差距变成一个标量 J(θ)，行为克隆用平方误差 J = Σ ‖π(o) − a‖²，于是网络学到的是同一观测下各个动作的平均。平方误差要求唯一正确答案；示范里有两个都对的动作时，它学到的那个平均值谁也没做过。",
      en: "Supervised learning pairs inputs with labels: the observation o is the input, the expert's action a is the label, and training shrinks the gap between prediction and label. The loss function turns that gap into a scalar J(θ); behaviour cloning uses the squared error J = Σ ‖π(o) − a‖², so the network learns the average of the recorded actions at a given observation. A squared error wants a single right answer, and when the demonstrations contain two correct actions it learns their mean, which nobody performed.",
    },
    example: {
      zh: "第 6 个月《模仿学习（一）：示范数据、行为克隆与 DAgger》\n1-最近邻行为克隆在 L 形走廊上，5 条示范 61/100 成功，20 条示范 67/100，80 条示范还是 67/100。\n失败几乎都在目标端（goal end），因为无噪声的示范几步之内就贴到中心线上，数据里根本没有「偏回来」的状态。",
      en: "Month 6 · Imitation learning I: demonstrations, behaviour cloning and DAgger\n1-nearest-neighbour behaviour cloning in the L-shaped corridor reaches 61/100 with 5 demos, 67/100 with 20 demos and still 67/100 with 80 demos.\nNearly all the failures are at the goal end, because the noise-free demonstrations collapse onto the centre line within a few steps, so the dataset holds no off-path states.",
    },
    lessons: ["behaviour-cloning", "act-diffusion", "vla-models"],
    links: [
      {
        label: "Goodfellow et al. · Deep Learning · Chapter 5: Machine Learning Basics",
        url: "https://www.deeplearningbook.org/contents/ml.html",
      },
      {
        label: "Goodfellow et al. · Deep Learning · Chapter 6: Deep Feedforward Networks",
        url: "https://www.deeplearningbook.org/contents/mlp.html",
      },
    ],
  },
  {
    id: "dct",
    title: { zh: "离散余弦变换（DCT）与频率分解", en: "DCT and frequency decomposition" },
    definition: {
      zh: "离散余弦变换把 N 个样本写成 N 个余弦基函数的加权和：c_k = α_k Σ x_n cos(π k (2n + 1) / (2N))，α_k 随 k 变化以保持基的正交归一。它把一段轨迹拆成快慢不同的成分：平滑运动几乎全部落在低阶系数里，高阶系数四舍五入后变成 0。所以 DCT 是有损压缩：系数取整后再逆变换会引入误差，量化步长（scale）越小越准，但需要的数越多。",
      en: "The discrete cosine transform writes N samples as a weighted sum of N cosine basis functions: c_k = α_k Σ x_n cos(π k (2n + 1) / (2N)), with α_k chosen so the basis stays orthonormal. It splits a trajectory into components of different speed: smooth motion puts almost everything into the low-order coefficients and the high-order ones round to zero. A DCT is therefore lossy compression — rounding the coefficients and transforming back introduces an error, and a smaller quantisation step (scale) is more accurate but needs more numbers.",
    },
    example: {
      zh: "第 6 个月《VLA 模型：动作如何变成词元，哪些开放权重》\n对 30 步 × 6 关节 = 180 个数做 DCT，scale 30 时只要 41 个非零系数（180 / 41 = 4.4 倍更少），rms 误差 0.499°、最大 1.350°；\nscale 10 时是 28 个系数、rms 1.103°、最大 3.535°。关节 0 在 scale 10 的系数序列是 −1 4 5 0 1 0 0 0 …，五个小整数加一串零。",
      en: "Month 6 · VLA models: how actions become tokens, and which have open weights\nA DCT of the 30-step × 6-joint = 180 numbers needs 41 nonzero coefficients at scale 30 (180 / 41 = 4.4 times fewer), with rms error 0.499° and a maximum of 1.350°;\nat scale 10 it needs 28 coefficients, rms 1.103°, maximum 3.535°. Joint 0's coefficients at scale 10 are −1 4 5 0 1 0 0 0 …: five small integers and then zeros.",
    },
    lessons: ["vla-models"],
    links: [
      {
        label: "Boyd & Vandenberghe · Introduction to Applied Linear Algebra · 5.3 Orthonormal vectors",
        url: "https://web.stanford.edu/~boyd/vmls/vmls.pdf",
      },
      {
        label: "Åström & Murray · Feedback Systems (2nd ed., free) · Chapter 10: Frequency Domain Analysis",
        url: "https://fbswiki.org/",
      },
    ],
  },
  {
    id: "inference",
    title: { zh: "统计推断：置信区间、p 值、二项分布与样本量", en: "Statistical inference: confidence interval, p-value, binomial, sample size" },
    definition: {
      zh: "从 n 次试验得到的成功率 k/n 只是点估计；置信区间给出真实概率的范围，Wilson 区间在 k = 0 或 k = n 时依然可用。p 值是「若原假设为真，观察到这么极端或更极端的数据的概率」，只有 p 很小才说明差异不像偶然。二项分布 X ~ B(n, p) 描述 n 次独立成/败试验中的成功次数，μ = np、σ² = npq。要比较两个成功率，所需试验次数随差异的平方增长。",
      en: "A success rate k/n from n trials is only a point estimate; a confidence interval gives a range for the true rate, and the Wilson interval stays valid at k = 0 and at k = n. The p-value is the probability of data at least as extreme as what was seen, assuming the null hypothesis, and only a small p-value says a difference is unlikely to be chance. The binomial distribution X ~ B(n, p) counts successes in n independent success/failure trials, with μ = np and σ² = npq. The number of trials needed to separate two success rates grows with the square of the difference.",
    },
    example: {
      zh: "第 6 个月《评估一个策略：置信区间、配对试验与失败分析》\n8/10 的 Wilson 95 % 区间是 49.0 .. 94.3 %，10/10 只说明真实成功率大概高于 72.2 %。\n配对比较中 35 次分歧全部同向，McNemar 精确检验 p = 2 × 0.5³⁵ = 5.8 × 10⁻¹¹。\n所需试验次数：67 % 对 99 % 每边约 21 次，80 % 对 90 % 每边约 199 次。",
      en: "Month 6 · Evaluating a policy: intervals, paired trials and failure analysis\nThe Wilson 95 % interval for 8/10 is 49.0 .. 94.3 %, and 10/10 only shows the true rate is probably above 72.2 %.\nIn the paired comparison all 35 disagreements go the same way, and McNemar's exact test gives p = 2 × 0.5³⁵ = 5.8 × 10⁻¹¹.\nTrials needed: 67 % against 99 % takes about 21 per policy, 80 % against 90 % about 199.",
    },
    lessons: ["policy-evaluation", "behaviour-cloning", "act-diffusion"],
    links: [
      {
        label: "OpenStax · Introductory Statistics 2e · 8.3 A Population Proportion",
        url: "https://openstax.org/books/introductory-statistics-2e/pages/8-3-a-population-proportion",
      },
      {
        label: "OpenStax · Introductory Statistics 2e · 9.4 Rare Events, the Sample, Decision and Conclusion",
        url: "https://openstax.org/books/introductory-statistics-2e/pages/9-4-rare-events-the-sample-decision-and-conclusion",
      },
      {
        label: "OpenStax · Introductory Statistics 2e · 4.3 Binomial Distribution",
        url: "https://openstax.org/books/introductory-statistics-2e/pages/4-3-binomial-distribution",
      },
    ],
  },
];
