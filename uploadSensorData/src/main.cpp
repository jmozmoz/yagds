#include <Homie.h>

#define MQTT_SERVER_FINGERPRINT {0xd6, 0x27, 0x18, 0xdd, 0x09, 0xce, 0x3d, 0x80, 0x1f, 0x59, 0x7a, 0x2b, 0x29, 0x78, 0x93, 0xe8, 0x0b, 0x82, 0x8a, 0x5d}

ADC_MODE(ADC_VCC);

const unsigned int upperReed = 0;     // GPIO0
const unsigned int lowerReed = 3;     // RX

const unsigned int REED_INTERVAL = 2;
const unsigned int SLEEP_INTERVAL = 2;

unsigned long lastReedSent = 0;

bool prepareSleepFlag = false;
bool doSleepFlag = false;
bool reachedSleepFlag = false;

unsigned long sleepCounter = 0;

HomieNode reedNode("reeds", "state");
HomieNode vccNode("powerSupply", "voltage");

void checkGotoSleep(int upperReedState, int lowerReedState) {
  if ((!(upperReedState) || !(lowerReedState)) && !prepareSleepFlag) {
    Homie.getLogger() << "Want to sleep" << endl;
    prepareSleepFlag = true;
    sleepCounter = millis();
  }
}

void publishStates() {
  int upperReedState = digitalRead(upperReed);
  int lowerReedState = digitalRead(lowerReed);
  uint16_t voltage = ESP.getVcc();
  
  Homie.getLogger() << "Upper reed: " << upperReedState << endl;
  Homie.getLogger() << "Lower reed: " << lowerReedState << endl;
  Homie.getLogger() << "Voltage: " << voltage << endl;

  reedNode.setProperty("upperReed").send(String(upperReedState));
  reedNode.setProperty("lowerReed").send(String(lowerReedState));
  vccNode.setProperty("voltage").send(String(voltage));

  checkGotoSleep(upperReedState, lowerReedState);
}

void loopHandler() {
  if (millis() - lastReedSent >= REED_INTERVAL * 1000UL || lastReedSent == 0) {
    Homie.getLogger() << "start loop " << endl;

    publishStates();

    lastReedSent = millis();
    Homie.getLogger() << "stop loop " << endl;
  }

  if (prepareSleepFlag && (millis() - sleepCounter >= SLEEP_INTERVAL * 1000UL)) {
    doSleepFlag = true;
    prepareSleepFlag = false;
    Homie.prepareToSleep();
  }
}

void onHomieEvent(const HomieEvent& event) {
  switch(event.type) {
    case HomieEventType::MQTT_READY:
      // Do whatever you want when MQTT is connected in normal mode
      publishStates();
      break;
    case HomieEventType::READY_TO_SLEEP:
      Homie.getLogger() << "Ready to sleep" << endl;
      reachedSleepFlag = true;
      break;
    default:
      break;
  }
}

void setup() {
  Homie.disableLedFeedback();
  Serial.begin(115200);
  Serial << endl << endl;

  pinMode(upperReed, INPUT);
  pinMode(lowerReed, INPUT_PULLUP);
  
  Homie_setFirmware("uploadSensorData", "1.0.0"); // The underscore is not a typo! See Magic bytes
  Homie.disableResetTrigger(); // before Homie.setup()

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
  if (reachedSleepFlag) {
    //Homie.getLogger() << "Really goto sleep" << endl;   
    Homie.doDeepSleep(0UL, RF_DEFAULT);
    ESP.deepSleep(0UL, RF_DEFAULT);
  }

  if (!doSleepFlag) {
    Homie.loop();
  }
}