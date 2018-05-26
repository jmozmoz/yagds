#include <Homie.h>
#include <jled.h>

class DebugOutput {
private:
    bool use_serial;
    JLed led;

public:
    DebugOutput();

    void enable_serial(bool s);
    void update();
    void mqtt_ready();
    void connectionTimedOut();
    void checkGotoSleep();
};