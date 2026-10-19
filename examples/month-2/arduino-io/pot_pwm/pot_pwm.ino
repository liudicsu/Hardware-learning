// Potentiometer wiper on A0 sets the brightness of an LED on pin 9 (PWM).
const int POT_PIN = A0;
const int LED_PIN = 9;  // a pin marked ~ on the Uno

void setup() {
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(115200);
}

void loop() {
  int raw = analogRead(POT_PIN);       // 0..1023
  int duty = raw / 4;                  // 0..255 for analogWrite
  float volts = raw * 5.0 / 1023.0;    // what the pin actually saw
  analogWrite(LED_PIN, duty);

  // "name:value" pairs separated by commas -> one line per trace in the Serial Plotter
  Serial.print("raw:");
  Serial.print(raw);
  Serial.print(",duty:");
  Serial.print(duty);
  Serial.print(",volts:");
  Serial.println(volts, 2);
  delay(20);  // ~50 lines per second is plenty for a human
}
