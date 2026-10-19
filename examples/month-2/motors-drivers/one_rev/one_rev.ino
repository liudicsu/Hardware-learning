// Turn a wheel exactly one revolution using a quadrature encoder.
// Driver: TB6612FNG channel A. Encoder: Pololu-style 12 CPR, 120:1 gearbox.
const int PWMA = 5;      // speed (PWM pin)
const int AIN1 = 7;      // direction
const int AIN2 = 8;
const int STBY = 9;      // HIGH = driver enabled
const int ENC_A = 2;     // both encoder channels on interrupt pins
const int ENC_B = 3;

const long COUNTS_PER_REV = 1440;   // 12 counts per motor turn x 120:1
const float KP = 0.4;               // PWM steps per count of error
const int MIN_PWM = 40;             // smallest PWM that still moves the wheel
const int MAX_PWM = 150;
const long TOLERANCE = 2;           // counts

volatile long encoderCount = 0;
volatile uint8_t lastAB = 0;

// Quadrature decoding: every edge on A or B moves the count by +1 or -1.
// Index = previous AB (2 bits) followed by new AB (2 bits).
const int8_t QDEC[16] = {0, -1, +1, 0, +1, 0, 0, -1, -1, 0, 0, +1, 0, +1, -1, 0};

void onEncoder() {
  uint8_t ab = (digitalRead(ENC_A) << 1) | digitalRead(ENC_B);
  encoderCount += QDEC[(lastAB << 2) | ab];
  lastAB = ab;
}

long readCount() {
  noInterrupts();
  long c = encoderCount;
  interrupts();
  return c;
}

void drive(int pwm) {                 // -255..255, sign = direction
  digitalWrite(AIN1, pwm > 0);
  digitalWrite(AIN2, pwm < 0);
  analogWrite(PWMA, abs(pwm));
}

void brake() {                        // TB6612: IN1 = IN2 = HIGH shorts the motor -> fast stop
  digitalWrite(AIN1, HIGH);
  digitalWrite(AIN2, HIGH);
}

bool turnCounts(long target, unsigned long timeoutMs) {
  noInterrupts();
  encoderCount = 0;
  interrupts();
  unsigned long start = millis();
  while (millis() - start < timeoutMs) {
    long error = target - readCount();
    if (abs(error) <= TOLERANCE) {
      brake();
      return true;
    }
    int pwm = constrain((int)(KP * error), -MAX_PWM, MAX_PWM);
    if (abs(pwm) < MIN_PWM) pwm = (error > 0) ? MIN_PWM : -MIN_PWM;
    drive(pwm);
  }
  drive(0);                           // never leave a motor running after a timeout
  return false;
}

void setup() {
  pinMode(PWMA, OUTPUT);
  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(STBY, OUTPUT);
  pinMode(ENC_A, INPUT_PULLUP);       // the encoder outputs are open-drain
  pinMode(ENC_B, INPUT_PULLUP);
  lastAB = (digitalRead(ENC_A) << 1) | digitalRead(ENC_B);
  attachInterrupt(digitalPinToInterrupt(ENC_A), onEncoder, CHANGE);
  attachInterrupt(digitalPinToInterrupt(ENC_B), onEncoder, CHANGE);
  digitalWrite(STBY, HIGH);
  Serial.begin(115200);

  bool ok = turnCounts(COUNTS_PER_REV, 5000);
  delay(300);                         // let the wheel settle, then report
  Serial.print(ok ? F("done, count = ") : F("timeout, count = "));
  Serial.println(readCount());
}

void loop() {}
