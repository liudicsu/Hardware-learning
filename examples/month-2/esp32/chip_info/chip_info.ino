// Blink an LED and report which chip this is.
// LED_PIN drives an external LED through a 220 Ω resistor on GPIO 2. That works on every
// board; on many classic ESP32 DevKits GPIO 2 is also the on-board LED.
// The ESP32-S3-DevKitC-1 has no plain on-board LED: it has one addressable RGB LED, on
// GPIO 38 on board v1.1 and on GPIO 48 on the initial v1.0 (Espressif user guide).
const int LED_PIN = 2;
#if CONFIG_IDF_TARGET_ESP32S3
const int RGB_PIN = 38;  // DevKitC-1 v1.1; set 48 for the initial v1.0 board
#endif

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
#if CONFIG_IDF_TARGET_ESP32S3
  rgbLedWrite(RGB_PIN, 0, 32, 0);  // dim green
#endif
  delay(200);
  digitalWrite(LED_PIN, LOW);
#if CONFIG_IDF_TARGET_ESP32S3
  rgbLedWrite(RGB_PIN, 0, 0, 0);   // off
#endif
  delay(800);
}
