#ifndef LED_CONTROLLER_H
#define LED_CONTROLLER_H

#include "NeoPixelBus.h"
#include "NeoPixelAnimator.h"

class LEDController{
public:
    LEDController(int pixel_count, int pin);
    void begin();
    void update();
private:
    NeoPixelBus<NeoGrbFeature, Neo800KbpsMethod> * NPBus;
    NeoPixelAnimator* animator;
    long currentFrame;
    int pixel_count;
};

#endif