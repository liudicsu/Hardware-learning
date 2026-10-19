// Two LEDs blinking at different rates, no delay() anywhere.
const int LED_A = 8;
const int LED_B = 9;
const unsigned long PERIOD_A = 250;  // ms between toggles
const unsigned long PERIOD_B = 400;

unsigned long lastA = 0;
unsigned long lastB = 0;
bool stateA = false;
bool stateB = false;

void setup() {
  pinMode(LED_A, OUTPUT);
  pinMode(LED_B, OUTPUT);
  Serial.begin(115200);
}

void loop() {
  unsigned long now = millis();

  if (now - lastA >= PERIOD_A) {
    lastA += PERIOD_A;          // keep a steady rhythm
    stateA = !stateA;
    digitalWrite(LED_A, stateA);
    Serial.print(now);
    Serial.println(" A");
  }

  if (now - lastB >= PERIOD_B) {
    lastB += PERIOD_B;
    stateB = !stateB;
    digitalWrite(LED_B, stateB);
    Serial.print(now);
    Serial.println(" B");
  }

  // ...room for reading sensors, here, every pass through loop()
}
