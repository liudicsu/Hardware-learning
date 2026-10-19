// Button between pin 2 and GND, internal pull-up enabled.
// Pressed = LOW. Print only when the state changes.
const int BUTTON_PIN = 2;
const int LED_PIN = LED_BUILTIN;

int lastState = HIGH;  // not pressed

void setup() {
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(115200);
  Serial.println("ready");
}

void loop() {
  int state = digitalRead(BUTTON_PIN);
  digitalWrite(LED_PIN, state == LOW ? HIGH : LOW);
  if (state != lastState) {
    Serial.println(state == LOW ? "pressed" : "released");
    lastState = state;
  }
}
