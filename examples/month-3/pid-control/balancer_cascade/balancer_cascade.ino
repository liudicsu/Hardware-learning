// Self-balancer with a cascade: the Month 2 balancer (inner PD on pitch, 200 Hz) plus an
// outer PI loop on wheel speed (25 Hz) that moves the inner loop's SETPOINT.
// Uno + TB6612FNG + two gearmotors with encoders + MPU-6050, wired as in Month 2 Lesson 6,
// plus: left encoder A -> D2, B -> D10; right encoder A -> D3, B -> D11.
// Get the inner loop balancing first (Month 2), then copy your KP/KD here.
#include <Wire.h>

const int PWMA = 5, AIN1 = 7, AIN2 = 8;     // left motor
const int PWMB = 6, BIN1 = 4, BIN2 = 12;    // right motor
const int STBY = 9;
const int ENC_LA = 2, ENC_LB = 10;          // A channels on the two interrupt pins
const int ENC_RA = 3, ENC_RB = 11;

const uint8_t MPU = 0x68;
const float ACCEL_LSB_PER_G = 16384.0;
const float GYRO_LSB_PER_DPS = 131.0;

const unsigned long PERIOD_US = 5000;       // inner loop: 200 Hz
const float DT = PERIOD_US / 1e6;
const int OUTER_EVERY = 8;                  // outer loop: every 8th tick = 25 Hz
const float OUTER_DT = DT * OUTER_EVERY;
const float ALPHA = 0.5 / (0.5 + DT);       // complementary filter, 0.5 s time constant

// Encoder: counting rising edges of A only = 1/4 of the full quadrature resolution.
// Example: 12 CPR motor encoder (3 rising edges of A per motor turn) x 30:1 gearbox, 65 mm wheel.
const float METERS_PER_COUNT = 3.14159 * 0.065 / (3 * 30);

float KP = 25.0, KD = 0.8;                  // inner PD: YOUR tuned Month 2 values
float KP_S = 3.0;                           // outer P: deg of setpoint per m/s of speed error
float KI_S = 3.0;                           // outer I: deg of setpoint per metre
const float SETPOINT_MAX = 3.0;             // the outer loop may lean the robot at most 3 deg
const float CUTOFF_DEG = 40.0;

volatile long leftCount = 0, rightCount = 0;
float pitch = 0, gyroBias = 0, setpoint = 0, integral = 0, speed = 0, targetSpeed = 0;
long lastPos = 0;
bool running = false;
unsigned int tick = 0;
unsigned long nextTick = 0, worstLoopUs = 0, lastReport = 0;

// If a wheel counts backwards when it rolls forward, swap that motor's A and B wires.
void leftEdge()  { leftCount  += digitalRead(ENC_LB) ? -1 : 1; }
void rightEdge() { rightCount += digitalRead(ENC_RB) ? -1 : 1; }

void setMotor(int pwmPin, int in1, int in2, int speed) {
  speed = constrain(speed, -255, 255);
  digitalWrite(in1, speed > 0);
  digitalWrite(in2, speed < 0);
  analogWrite(pwmPin, abs(speed));
}

void readImu(float &accelPitch, float &rate) {
  Wire.beginTransmission(MPU);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU, (uint8_t)14);
  int16_t v[7];
  for (int i = 0; i < 7; i++) v[i] = (Wire.read() << 8) | Wire.read();
  accelPitch = atan2(v[0] / ACCEL_LSB_PER_G, v[2] / ACCEL_LSB_PER_G) * 180.0 / PI;
  rate = v[5] / GYRO_LSB_PER_DPS - gyroBias;
}

void outerLoop() {                          // 25 Hz: wheel speed -> setpoint
  noInterrupts();
  long pos = (leftCount + rightCount) / 2;
  interrupts();
  speed = (pos - lastPos) * METERS_PER_COUNT / OUTER_DT;   // m/s
  lastPos = pos;
  float error = targetSpeed - speed;
  integral += error * OUTER_DT;
  float iMax = SETPOINT_MAX / KI_S;         // anti-windup: the I term alone stays within 3 deg
  integral = constrain(integral, -iMax, iMax);
  setpoint = constrain(KP_S * error + KI_S * integral, -SETPOINT_MAX, SETPOINT_MAX);
}

void setup() {
  int outs[] = {PWMA, AIN1, AIN2, PWMB, BIN1, BIN2, STBY};
  for (int p : outs) pinMode(p, OUTPUT);
  digitalWrite(STBY, HIGH);
  int ins[] = {ENC_LA, ENC_LB, ENC_RA, ENC_RB};
  for (int p : ins) pinMode(p, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ENC_LA), leftEdge, RISING);
  attachInterrupt(digitalPinToInterrupt(ENC_RA), rightEdge, RISING);
  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(400000);
  Wire.beginTransmission(MPU);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission();

  float sum = 0, a, r;                      // gyro bias: hold still for one second
  for (int i = 0; i < 200; i++) { readImu(a, r); sum += r; delay(5); }
  gyroBias = sum / 200;
  readImu(a, r);
  pitch = a;
  Serial.print(F("gyro bias (deg/s): "));
  Serial.println(gyroBias, 2);
  nextTick = micros();
}

void loop() {
  if ((long)(micros() - nextTick) < 0) return;
  unsigned long start = micros();
  nextTick += PERIOD_US;

  float accelPitch, rate;
  readImu(accelPitch, rate);
  pitch = ALPHA * (pitch + rate * DT) + (1 - ALPHA) * accelPitch;

  if (fabs(pitch) > CUTOFF_DEG) running = false;
  if (!running && fabs(pitch) < 5.0) {      // stood back up: start both loops from zero
    running = true;
    integral = 0;
    setpoint = 0;
    noInterrupts();
    lastPos = (leftCount + rightCount) / 2;
    interrupts();
  }

  if (running) {
    if (++tick % OUTER_EVERY == 0) outerLoop();
    int out = (int)(KP * (pitch - setpoint) + KD * rate);
    setMotor(PWMA, AIN1, AIN2, out);
    setMotor(PWMB, BIN1, BIN2, out);
  } else {
    setMotor(PWMA, AIN1, AIN2, 0);
    setMotor(PWMB, BIN1, BIN2, 0);
  }

  unsigned long used = micros() - start;
  if (used > worstLoopUs) worstLoopUs = used;
  if (millis() - lastReport >= 1000) {
    lastReport = millis();
    Serial.print(F("pitch "));
    Serial.print(pitch, 1);
    Serial.print(F("  setpoint "));
    Serial.print(setpoint, 2);
    Serial.print(F("  speed "));
    Serial.print(speed, 3);
    Serial.print(F("  worst loop us "));
    Serial.println(worstLoopUs);
    worstLoopUs = 0;
  }
}
