// Reaction-timer game.
// LED on pin 13 lights after a random 2-5 s wait; press the button (pin 2 to GND)
// as fast as you can. Pressing before the LED lights is a foul.
const int LED_PIN = 13;
const int BUTTON_PIN = 2;               // pin 2 = external interrupt INT0 on the Uno
const unsigned long DEBOUNCE_MS = 30;

enum State { WAITING, LIT, SHOW_RESULT };
State state = WAITING;

volatile unsigned long pressedAt = 0;   // written by the ISR, read by loop()
volatile bool pressed = false;

unsigned long waitStart = 0;
unsigned long waitTime = 0;
unsigned long litAt = 0;
unsigned long best = 0;
unsigned long resultAt = 0;

void onButton() {                       // interrupt service routine: keep it tiny
  unsigned long t = millis();
  static unsigned long lastEdge = 0;
  bool isDown = digitalRead(BUTTON_PIN) == LOW;
  if (isDown && t - lastEdge > DEBOUNCE_MS) {  // a quiet line that just went LOW = real press
    pressedAt = t;
    pressed = true;
  }
  lastEdge = t;                         // every edge, including bounces, restarts the quiet timer
}

void startRound() {
  digitalWrite(LED_PIN, LOW);
  waitTime = random(2000, 5001);
  waitStart = millis();
  noInterrupts();
  pressed = false;
  interrupts();
  state = WAITING;
  Serial.println(F("Get ready..."));
}

void setup() {
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  Serial.begin(115200);
  randomSeed(analogRead(A0));           // floating analog pin = noisy seed
  attachInterrupt(digitalPinToInterrupt(BUTTON_PIN), onButton, CHANGE);
  startRound();
}

void loop() {
  unsigned long now = millis();

  noInterrupts();                       // copy shared variables atomically
  bool gotPress = pressed;
  unsigned long t = pressedAt;
  pressed = false;
  interrupts();

  switch (state) {
    case WAITING:
      if (gotPress) {
        Serial.println(F("Foul! You pressed too early."));
        resultAt = now;
        state = SHOW_RESULT;
      } else if (now - waitStart >= waitTime) {
        digitalWrite(LED_PIN, HIGH);
        litAt = millis();
        state = LIT;
      }
      break;

    case LIT:
      if (gotPress) {
        unsigned long reaction = t - litAt;
        digitalWrite(LED_PIN, LOW);
        Serial.print(F("Reaction: "));
        Serial.print(reaction);
        Serial.print(F(" ms"));
        if (best == 0 || reaction < best) {
          best = reaction;
          Serial.print(F("  (new best!)"));
        }
        Serial.println();
        resultAt = now;
        state = SHOW_RESULT;
      }
      break;

    case SHOW_RESULT:
      if (now - resultAt >= 2000) startRound();   // next round after 2 s
      break;
  }
}
