// Blink with an uneven rhythm: 200 ms on, 800 ms off.
const int LED_PIN = LED_BUILTIN;  // pin 13 on an Uno

void setup() {
  pinMode(LED_PIN, OUTPUT);
}

void loop() {
  digitalWrite(LED_PIN, HIGH);
  delay(200);
  digitalWrite(LED_PIN, LOW);
  delay(800);
}
