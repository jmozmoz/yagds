#include "debug_output.hpp"

DebugOutput::DebugOutput() : 
    use_serial(false), led(JLed(LED_BUILTIN).LowActive())
{};

void DebugOutput::enable_serial(bool s) {
    use_serial = s;

    if (use_serial) {
        Homie.disableLedFeedback();
        Serial.begin(115200);
        Serial << endl << endl;
    }
    else {
        Homie.disableLogging();
    }
}

void DebugOutput::update() {
    if (!use_serial) {
        led.Update();
    }
};

void DebugOutput::mqtt_ready() {
    if (!use_serial) {
            led.Blink(100, 900).Forever();
    }
};

void DebugOutput::connectionTimedOut() {
    Homie.getLogger() << F("Initiate go to sleep, because connection timeout was reached") << endl;
    if (!use_serial) {
        led.Blink(500, 100).Forever();
    }
};

void DebugOutput::checkGotoSleep() {
    Homie.getLogger() << F("Prepare to sleep") << endl;
    if (!use_serial) {
        led.Blink(100, 100).Forever();
    }
}
