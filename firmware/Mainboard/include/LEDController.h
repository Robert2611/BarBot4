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
    LED_TYPE_POSITION_WATERFALL = 4,
    LED_TYPE_DRAFT_POSITION = 5
};

class LEDController
{
public:
    LEDController();
    void begin();
    void update(bool force = false);
    void setType(int type);
    void setPlatformPosition(float position_in_mm);
    void setDraftPosition(float position_in_mm);

private:
    NeoPixelBus<NeoGrbFeature, Neo800KbpsMethod> *stripe;
    int platform_position;
    int draft_position;
    int data_pin;
    int type;
    unsigned long last_change;
    int frame;
    unsigned long frame_start_millis;
};

#endif