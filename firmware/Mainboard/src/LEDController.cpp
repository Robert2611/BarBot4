#include "LEDController.h"

LEDController::LEDController()
{
    NPBus = new NeoPixelBus<NeoGrbFeature, Neo800KbpsMethod>(PIXEL_COUNT, PIN_NEOPIXEL);
}

void LEDController::begin()
{
    // this resets all the neopixels to an off state
    NPBus->Begin();
    NPBus->Show();
    currentFrame = 0;
    animator = new NeoPixelAnimator(PIXEL_COUNT, NEO_CENTISECONDS);
}

void LEDController::update()
{
    for (int i = 0; i < PIXEL_COUNT; i++)
    {
        if (i == currentFrame)
            NPBus->SetPixelColor(i, RgbColor(150, 0, 0));
        else
            NPBus->SetPixelColor(i, RgbColor(0, 0, 0));
    }
    NPBus->Show();
    currentFrame++;
    if (currentFrame >= PIXEL_COUNT)
        currentFrame = 0;
}