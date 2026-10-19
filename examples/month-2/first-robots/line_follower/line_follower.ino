// PD line follower: QTR-8RC array + TB6612FNG + two gearmotors (Arduino Uno).
// Library: "QTRSensors" by Pololu (Library Manager).
#include <QTRSensors.h>

// TB6612FNG
const int PWMA = 5, AIN1 = 7, AIN2 = 8;     // left motor
const int PWMB = 6, BIN1 = 4, BIN2 = 12;    // right motor
const int STBY = 9;

const uint8_t SENSOR_PINS[8] = {A0, A1, A2, A3, A4, A5, 10, 11};
QTRSensors qtr;
uint16_t values[8];

const float KP = 0.06;          // PWM per unit of position error  (start here)
const float KD = 0.0;           // add D after P is working: try 0.3, then tune
const int BASE_PWM = 120;       // straight-line speed
const unsigned long PERIOD_MS = 10;   // 100 Hz control loop

int lastError = 0;
unsigned long last = 0;

void setMotor(int pwmPin, int in1, int in2, int speed) {   // speed -255..255
  speed = constrain(speed, -255, 255);
  digitalWrite(in1, speed > 0);
  digitalWrite(in2, speed < 0);
  analogWrite(pwmPin, abs(speed));
}

void setup() {
  int outs[] = {PWMA, AIN1, AIN2, PWMB, BIN1, BIN2, STBY};
  for (int p : outs) pinMode(p, OUTPUT);
  digitalWrite(STBY, HIGH);

  qtr.setTypeRC();
  qtr.setSensorPins(SENSOR_PINS, 8);

  // Calibrate for ~5 s: slide the robot by hand so every sensor sees black and white.
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);
  for (int i = 0; i < 200; i++) qtr.calibrate();
  digitalWrite(LED_BUILTIN, LOW);
  last = millis();
}

void loop() {
  unsigned long now = millis();
  if (now - last < PERIOD_MS) return;
  last += PERIOD_MS;

  uint16_t position = qtr.readLineBlack(values);   // 0..7000, 3500 = centred
  int error = (int)position - 3500;
  int derivative = error - lastError;              // per loop period (fixed 10 ms)
  lastError = error;

  int correction = (int)(KP * error + KD * derivative);
  setMotor(PWMA, AIN1, AIN2, BASE_PWM + correction);
  setMotor(PWMB, BIN1, BIN2, BASE_PWM - correction);
}
