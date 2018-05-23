#include <Homie.h>
#include <SimpleTimer.h>
#include <jled.h>

#define MQTT_SERVER_FINGERPRINT {0xd6, 0x27, 0x18, 0xdd, 0x09, 0xce, 0x3d, 0x80, 0x1f, 0x59, 0x7a, 0x2b, 0x29, 0x78, 0x93, 0xe8, 0x0b, 0x82, 0x8a, 0x5d}

ADC_MODE(ADC_VCC);

const unsigned int upperReed = 0;     // GPIO0
const unsigned int lowerReed = 3;     // RX

const unsigned int maxResendMessage = 3;
unsigned int resendMessage = 0;

HomieSetting<long> sensor_update_interval("sensor_update_interval", "interval for sensor updates");
HomieSetting<long> connection_timeout("connection_timeout", "timeout for connection establishing");
HomieSetting<long> sleep_timeout("sleep_timeout", "timeout for going to sleep");

const unsigned int SENSOR_UPDATE_INTERVAL_DEFAULT = 2;
const unsigned int CONNECTION_TIMEOUT_DEFAULT = 30;
const unsigned int SLEEP_TIMEOUT_DEFAULT = 10;

int publishTimerId;
int connectionTimeoutId;
int sleepTimeoutId;

HomieNode reedNode("reeds", "state");
HomieNode vccNode("powerSupply", "voltage");

SimpleTimer homieLoopTimer;
SimpleTimer mainLoopTimer;

JLed led = JLed(LED_BUILTIN).LowActive();

void gotoDeepSleep() {
    Homie.getLogger() << F("Really goto sleep") << endl;   
    Homie.doDeepSleep(0UL, RF_DEFAULT);
    ESP.deepSleep(0UL, RF_DEFAULT);
}

void checkGotoSleep(int upperReedState, int lowerReedState) {
  if ((!upperReedState || !lowerReedState) &&
      (Homie.getMqttClient().connected()) &&
      (++resendMessage >= maxResendMessage)) {
    Homie.getLogger() << F("Prepare to sleep") << endl;
    homieLoopTimer.deleteTimer(publishTimerId);
    sleepTimeoutId = mainLoopTimer.setTimeout(sleep_timeout.get() * 1000UL, gotoDeepSleep);
    led.Blink(100, 100).Forever();
    Homie.prepareToSleep();
  }
}

void publishStates() {
  int upperReedState = digitalRead(upperReed);
  int lowerReedState = digitalRead(lowerReed);
  uint16_t voltage = ESP.getVcc();
  
  Homie.getLogger() << F("Upper reed: ") << upperReedState << endl;
  Homie.getLogger() << F("Lower reed: ") << lowerReedState << endl;
  Homie.getLogger() << F("Voltage: ") << voltage << endl;

  reedNode.setProperty("upperReed").send(String(upperReedState));
  reedNode.setProperty("lowerReed").send(String(lowerReedState));
  vccNode.setProperty("voltage").send(String(voltage));

  checkGotoSleep(upperReedState, lowerReedState);
}

void loopHandler() {
  homieLoopTimer.run();
}

void onHomieEvent(const HomieEvent& event) {
  switch(event.type) {
    case HomieEventType::MQTT_READY:
      mainLoopTimer.disable(connectionTimeoutId);
      led.Blink(100, 900).Forever();
      break;
    case HomieEventType::MQTT_DISCONNECTED:
      mainLoopTimer.restartTimer(connectionTimeoutId);
      mainLoopTimer.enable(connectionTimeoutId);
      break;
    case HomieEventType::READY_TO_SLEEP:
      Homie.getLogger() << F("Ready to sleep") << endl;
      mainLoopTimer.setTimeout(0, gotoDeepSleep);
      break;
    default:
      break;
  }
}

void connectionTimedOut() {
  Homie.getLogger() << F("Initiate go to sleep, because connection timeout was reached") << endl;
  led.Blink(500, 100).Forever();
  Homie.prepareToSleep();
}

void setup() {
#ifdef SERIAL_LOG
  Homie.disableLedFeedback();
  Serial.begin(115200);
  Serial << endl << endl;
#else
  Homie.disableLogging();
#endif

  Homie.disableResetTrigger();  // we do not want to trigger config mode by sensor input

  pinMode(upperReed, INPUT);
  pinMode(lowerReed, INPUT_PULLUP);
  
  Homie_setFirmware("uploadSensorData", "1.0.0"); // The underscore is not a typo! See Magic bytes

  Homie.setLoopFunction(loopHandler);
  Homie.onEvent(onHomieEvent);

  sensor_update_interval.setDefaultValue(SENSOR_UPDATE_INTERVAL_DEFAULT);
  connection_timeout.setDefaultValue(CONNECTION_TIMEOUT_DEFAULT);
  sleep_timeout.setDefaultValue(SLEEP_TIMEOUT_DEFAULT);

  Homie.setup();

  publishTimerId = homieLoopTimer.setInterval(sensor_update_interval.get() * 1000UL, publishStates);
  connectionTimeoutId = mainLoopTimer.setTimeout(connection_timeout.get() * 1000UL, connectionTimedOut);

#if ASYNC_TCP_SSL_ENABLED
  Homie.getLogger() << endl << endl << F("ESP Homie Using TLS") << endl;
  Homie.getMqttClient().setSecure(true);
  Homie.getMqttClient().addServerFingerprint((const uint8_t[])MQTT_SERVER_FINGERPRINT);
#endif
  Homie.getLogger() << endl << endl << F("setup finished") << endl;  
}

void loop() {
  led.Update();
  if (homieLoopTimer.getNumTimers()) {
      Homie.loop();
  }
  mainLoopTimer.run();
}