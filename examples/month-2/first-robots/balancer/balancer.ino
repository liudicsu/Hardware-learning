// Self-balancer skeleton: MPU-6050 + complementary filter + PD at a fixed 200 Hz.
// Uno + TB6612FNG (both channels) + two gearmotors. Mount the MPU-6050 so that
// tilting forward makes the pitch positive. Tune KP first, then KD (see the lesson).
#include <Wire.h>

const int PWMA = 5, AIN1 = 7, AIN2 = 8;     // left motor
const int PWMB = 6, BIN1 = 4, BIN2 = 12;    // right motor
const int STBY = 9;

const uint8_t MPU = 0x68;
const float ACCEL_LSB_PER_G = 16384.0;      // +-2 g (default)
const float GYRO_LSB_PER_DPS = 131.0;       // +-250 deg/s (default)

const unsigned long PERIOD_US = 5000;       // 200 Hz control loop
const float DT = PERIOD_US / 1e6;
const float TAU = 0.5;                      // filter time constant, s
const float ALPHA = TAU / (TAU + DT);       // = 0.990 at 200 Hz

float KP = 25.0;                            // PWM per degree
float KD = 0.8;                             // PWM per deg/s
const float SETPOINT = 0.0;                 // pitch when balanced, deg (trim this)
const float CUTOFF_DEG = 40.0;              // beyond this it has fallen: motors off

float pitch = 0, gyroBias = 0;
bool running = false;
unsigned long nextTick = 0, worstLoopUs = 0, lastReport = 0;

void setMotor(int pwmPin, int in1, int in2, int speed) {   // -255..255
  speed = constrain(speed, -255, 255);
  digitalWrite(in1, speed > 0);
  digitalWrite(in2, speed < 0);
  analogWrite(pwmPin, abs(speed));
}

void stopMotors() {
  setMotor(PWMA, AIN1, AIN2, 0);
  setMotor(PWMB, BIN1, BIN2, 0);
}

void readImu(float &accelPitch, float &rate) {
  Wire.beginTransmission(MPU);
  Wire.write(0x3B);                         // ACCEL_XOUT_H
  Wire.endTransmission(false);
  Wire.requestFrom(MPU, (uint8_t)14);
  int16_t v[7];
  for (int i = 0; i < 7; i++) v[i] = (Wire.read() << 8) | Wire.read();
  accelPitch = atan2(v[0] / ACCEL_LSB_PER_G, v[2] / ACCEL_LSB_PER_G) * 180.0 / PI;
  rate = v[5] / GYRO_LSB_PER_DPS - gyroBias; // gyro Y
}

void setup() {
  int outs[] = {PWMA, AIN1, AIN2, PWMB, BIN1, BIN2, STBY};
  for (int p : outs) pinMode(p, OUTPUT);
  digitalWrite(STBY, HIGH);
  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(400000);                    // fast-mode I2C: shorter reads
  Wire.beginTransmission(MPU);
  Wire.write(0x6B);                         // PWR_MGMT_1: wake up
  Wire.write(0);
  Wire.endTransmission();

  // Gyro bias: hold the robot still for one second at power-up.
  float sum = 0, a, r;
  for (int i = 0; i < 200; i++) { readImu(a, r); sum += r; delay(5); }
  gyroBias = sum / 200;
  readImu(a, r);
  pitch = a;                                // start the filter from the accelerometer
  Serial.print(F("gyro bias (deg/s): "));
  Serial.println(gyroBias, 2);
  nextTick = micros();
}

void loop() {
  if ((long)(micros() - nextTick) < 0) return;   // wait for the next 5 ms tick
  unsigned long start = micros();
  nextTick += PERIOD_US;

  float accelPitch, rate;
  readImu(accelPitch, rate);
  pitch = ALPHA * (pitch + rate * DT) + (1 - ALPHA) * accelPitch;

  if (fabs(pitch) > CUTOFF_DEG) running = false;   // fallen: stop
  if (!running && fabs(pitch) < 5.0) running = true; // stood back up by hand: go

  if (running) {
    int out = (int)(KP * (pitch - SETPOINT) + KD * rate);
    setMotor(PWMA, AIN1, AIN2, out);
    setMotor(PWMB, BIN1, BIN2, out);
  } else {
    stopMotors();
  }

  unsigned long used = micros() - start;
  if (used > worstLoopUs) worstLoopUs = used;
  if (millis() - lastReport >= 1000) {      // once a second; printing takes time too
    lastReport = millis();
    Serial.print(F("pitch "));
    Serial.print(pitch, 1);
    Serial.print(F("  worst loop us "));
    Serial.println(worstLoopUs);
    worstLoopUs = 0;
  }
}
