// MPU-6050 pitch angle three ways: gyro only, accelerometer only, complementary filter.
// Wiring (Uno): VCC -> 5V (the common GY-521 breakout has a regulator), GND -> GND,
// SDA -> A4, SCL -> A5. AD0 left unconnected -> address 0x68.
#include <Wire.h>

const uint8_t MPU = 0x68;
const uint8_t REG_PWR_MGMT_1 = 0x6B;
const uint8_t REG_ACCEL_XOUT_H = 0x3B;
const uint8_t REG_WHO_AM_I = 0x75;

const float ACCEL_LSB_PER_G = 16384.0;   // +-2 g range (datasheet, default)
const float GYRO_LSB_PER_DPS = 131.0;    // +-250 deg/s range (datasheet, default)
const float ALPHA = 0.98;                // complementary filter weight on the gyro
const unsigned long PERIOD_MS = 10;      // 100 Hz loop

float gyroOnly = 0, fused = 0;
unsigned long last = 0, lastPrint = 0;

void writeReg(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(MPU);
  Wire.write(reg);
  Wire.write(value);
  Wire.endTransmission();
}

uint8_t readReg(uint8_t reg) {
  Wire.beginTransmission(MPU);
  Wire.write(reg);
  Wire.endTransmission(false);           // repeated start: keep the bus
  Wire.requestFrom(MPU, (uint8_t)1);
  return Wire.read();
}

int16_t read16() {                       // registers are big-endian: high byte first
  int16_t hi = Wire.read();
  return (hi << 8) | Wire.read();
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  writeReg(REG_PWR_MGMT_1, 0x00);        // the chip powers up asleep: clear SLEEP
  Serial.print(F("WHO_AM_I = 0x"));
  Serial.println(readReg(REG_WHO_AM_I), HEX);
  Serial.println(F("t_s,gyro_only,accel_only,fused"));
  last = millis();
}

void loop() {
  unsigned long now = millis();
  if (now - last < PERIOD_MS) return;
  float dt = (now - last) / 1000.0;
  last = now;

  Wire.beginTransmission(MPU);
  Wire.write(REG_ACCEL_XOUT_H);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU, (uint8_t)14);    // accel XYZ, temperature, gyro XYZ
  int16_t ax = read16(), ay = read16(), az = read16();
  read16();                              // temperature, unused
  read16();                              // gyro X, unused
  int16_t gy = read16();
  read16();                              // gyro Z, unused

  float accelPitch = atan2(ax / ACCEL_LSB_PER_G, az / ACCEL_LSB_PER_G) * 180.0 / PI;
  float rate = gy / GYRO_LSB_PER_DPS;    // deg/s around the Y axis

  gyroOnly += rate * dt;                                       // drifts
  fused = ALPHA * (fused + rate * dt) + (1 - ALPHA) * accelPitch;  // does not

  if (now - lastPrint >= 1000) {         // one line per second
    lastPrint = now;
    Serial.print(now / 1000.0, 1);
    Serial.print(',');
    Serial.print(gyroOnly, 1);
    Serial.print(',');
    Serial.print(accelPitch, 1);
    Serial.print(',');
    Serial.println(fused, 1);
  }
}
