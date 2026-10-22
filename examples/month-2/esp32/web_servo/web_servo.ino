// ESP32 web servo: a phone on the same Wi-Fi sees a live reading
// and moves a hobby servo with three buttons.
#include <WiFi.h>
#include <WebServer.h>

const char *WIFI_SSID = "your-network";
const char *WIFI_PASS = "your-password";

const int SERVO_PIN = 18;
const int POT_PIN = 34;        // classic ESP32: GPIO 34 is on ADC1 (works with Wi-Fi on). ESP32-S3: use GPIO 4.
const int SERVO_HZ = 50;       // standard hobby servo frame: 20 ms
const int SERVO_BITS = 14;     // duty resolution: 0..16384

WebServer server(80);
int servoAngle = 90;

// 0..180 degrees -> 1000..2000 us pulse -> LEDC duty value
uint32_t angleToDuty(int angle) {
  uint32_t us = 1000 + (uint32_t)angle * 1000 / 180;
  return us * (1UL << SERVO_BITS) / 20000;
}

void setServo(int angle) {
  servoAngle = constrain(angle, 0, 180);
  ledcWrite(SERVO_PIN, angleToDuty(servoAngle));
}

const char PAGE[] = R"HTML(<!doctype html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ESP32 servo</title></head>
<body style="font-family:sans-serif;text-align:center">
<h1>ESP32 servo</h1>
<p>Knob: <b id="mv">-</b> mV &middot; Servo: <b id="deg">-</b>&deg;</p>
<p><button onclick="go(0)">0&deg;</button>
<button onclick="go(90)">90&deg;</button>
<button onclick="go(180)">180&deg;</button></p>
<script>
function go(a){fetch('/servo?angle='+a);}
async function poll(){
  try{const r=await fetch('/reading');const j=await r.json();
  document.getElementById('mv').textContent=j.mv;
  document.getElementById('deg').textContent=j.angle;}catch(e){}
  setTimeout(poll,500);}
poll();
</script></body></html>)HTML";

void handleRoot() { server.send(200, "text/html", PAGE); }

void handleReading() {
  char json[48];
  snprintf(json, sizeof json, "{\"mv\":%lu,\"angle\":%d}",
           (unsigned long)analogReadMilliVolts(POT_PIN), servoAngle);
  server.send(200, "application/json", json);
}

void handleServo() {
  if (!server.hasArg("angle")) { server.send(400, "text/plain", "missing angle"); return; }
  setServo(server.arg("angle").toInt());
  server.send(200, "text/plain", "ok");
}

void setup() {
  Serial.begin(115200);
  ledcAttach(SERVO_PIN, SERVO_HZ, SERVO_BITS);   // Arduino-ESP32 core 3.x API
  setServo(90);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting");
  while (WiFi.status() != WL_CONNECTED) {         // fine in setup(); never do this in loop()
    delay(250);
    Serial.print('.');
  }
  Serial.println();
  Serial.print("Open http://");
  Serial.println(WiFi.localIP());

  server.on("/", handleRoot);
  server.on("/reading", handleReading);
  server.on("/servo", handleServo);
  server.begin();
}

void loop() {
  server.handleClient();   // non-blocking: answers any waiting request and returns
}
