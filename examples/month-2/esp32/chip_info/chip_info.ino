// Blink the on-board LED and report which chip this is.
// Set LED_PIN to your board's LED (many classic DevKits: 2; check your board's pinout).
const int LED_PIN = 2;

void setup() {
  Serial.begin(115200);
  delay(1000);  // give the USB serial port a moment to appear
  pinMode(LED_PIN, OUTPUT);
  Serial.printf("Chip: %s rev %d, %d core(s), %lu MHz\n",
                ESP.getChipModel(), ESP.getChipRevision(),
                ESP.getChipCores(), (unsigned long)ESP.getCpuFreqMHz());
  Serial.printf("Flash: %lu bytes\n", (unsigned long)ESP.getFlashChipSize());
}

void loop() {
  digitalWrite(LED_PIN, HIGH);
  delay(200);
  digitalWrite(LED_PIN, LOW);
  delay(800);
}
