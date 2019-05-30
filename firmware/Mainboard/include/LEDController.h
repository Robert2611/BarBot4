#ifndef LED_CONTROLLER_H
#define LED_CONTROLLER_H

#include "Configuration.h"
#include "Shared.h"
#include "NeoPixelBus.h"

enum LEDType
{
    LED_TYPE_OFF = 0,
    LED_TYPE_CONTINOUS = 1,
    LED_TYPE_BLINK = 2,
    LED_TYPE_RAINBOW = 3,
    LED_TYPE_POSITION_WATERFALL = 4
};

class LEDController
{
public:
    LEDController();
    void begin();
    void update(bool force = false);
    void setType(int type);
    void setPosition(int position);

private:
    NeoPixelBus<NeoGrbFeature, Neo800KbpsMethod> *stripe;
    int position;
    int data_pin;
    int type;
    unsigned long last_change;
    int frame;
    unsigned long frame_start_millis;
};

#endif