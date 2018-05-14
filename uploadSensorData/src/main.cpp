#include <Homie.h>

#define MQTT_SERVER_FINGERPRINT {0xd6, 0x27, 0x18, 0xdd, 0x09, 0xce, 0x3d, 0x80, 0x1f, 0x59, 0x7a, 0x2b, 0x29, 0x78, 0x93, 0xe8, 0x0b, 0x82, 0x8a, 0x5d}

ADC_MODE(ADC_VCC);

const unsigned int upperReed = 0;     // GPIO0
const unsigned int lowerReed = 3;     // RX

const unsigned int REED_INTERVAL = 2;
const unsigned int CONNECTION_TIMEOUT = 60;
const unsigned int SLEEP_TIMEOUT = 10;

unsigned long lastReedSent = 0;
unsigned long sleepStarted = 0;
unsigned long startupTime = 0;

bool doSleepFlag = false;
bool reachedSleepFlag = false;

bool waitForConnection = true;

HomieNode reedNode("reeds", "state");
HomieNode vccNode("powerSupply", "voltage");

void checkGotoSleep(int upperReedState, int lowerReedState) {
  if (!upperReedState || !lowerReedState) {
    sleepStarted = millis();
    Homie.getLogger() << F("Prepare to sleep") << endl;
    doSleepFlag = true;
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
  if (millis() - lastReedSent >= REED_INTERVAL * 1000UL || lastReedSent == 0) {
    publishStates();
    lastReedSent = millis();
  }
}

void onHomieEvent(const HomieEvent& event) {
  switch(event.type) {
    case HomieEventType::MQTT_READY:
      waitForConnection = false;
      break;
    case HomieEventType::MQTT_DISCONNECTED:
      waitForConnection = true;
      startupTime = millis();
      break;
    case HomieEventType::READY_TO_SLEEP:
      Homie.getLogger() << F("Ready to sleep") << endl;
      reachedSleepFlag = true;
      break;
    default:
      break;
  }
}

void setup() {
  Homie.disableLedFeedback();
  Homie.disableResetTrigger();  // we do not want to trigger config mode by sensor input
  Serial.begin(115200);
  Serial << endl << endl;

  startupTime = millis();

  pinMode(upperReed, INPUT);
  pinMode(lowerReed, INPUT_PULLUP);
  
  Homie_setFirmware("uploadSensorData", "1.0.0"); // The underscore is not a typo! See Magic bytes

  Homie.setLoopFunction(loopHandler);
  Homie.onEvent(onHomieEvent);
  Homie.setup();

#if ASYNC_TCP_SSL_ENABLED
  Homie.getLogger() << endl << endl << F("ESP Homie Using TLS") << endl;
  Homie.getMqttClient().setSecure(true);
  Homie.getMqttClient().addServerFingerprint((const uint8_t[])MQTT_SERVER_FINGERPRINT);
#endif
  Homie.getLogger() << endl << endl << F("setup finished") << endl;  
}

void loop() {
  if (waitForConnection && millis() - startupTime > CONNECTION_TIMEOUT * 1000UL) {
    Homie.getLogger() << F("Initiate go to sleep, because connection timeout was reached") << endl;
    Homie.prepareToSleep();
  }

  if (reachedSleepFlag || 
    (doSleepFlag && (millis() - sleepStarted >= SLEEP_TIMEOUT * 1000UL))
    ) {
    Homie.getLogger() << "Really goto sleep" << endl;   
    Homie.doDeepSleep(0UL, RF_DEFAULT);
    ESP.deepSleep(0UL, RF_DEFAULT);
  }

  if (!doSleepFlag) {
    Homie.loop();
  }
}