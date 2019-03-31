#include "NeoPixelBus.h"
#include "NeoPixelAnimator.h"

#define PIXEL_COUNT 60
#define PIN_NEOPIXEL 12

class LEDController{
public:
    LEDController();
    void begin();
    void update();
private:
    NeoPixelBus<NeoGrbFeature, Neo800KbpsMethod> * NPBus;
    NeoPixelAnimator* animator;
    long currentFrame;
};