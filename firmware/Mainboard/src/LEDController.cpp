#include "LEDController.h"

LEDController::LEDController(int _pixel_count, int _pin)
{
    pixel_count = _pixel_count;
    NPBus = new NeoPixelBus<NeoGrbFeature, Neo800KbpsMethod>(pixel_count, _pin);
}

void LEDController::begin()
{
    // this resets all the neopixels to an off state
    NPBus->Begin();
    NPBus->Show();
}

void LEDController::update()
{
    for (int i = 0; i < pixel_count; i++)
    {
        if (i == currentFrame)
            NPBus->SetPixelColor(i, RgbColor(150, 0, 0));
        else
            NPBus->SetPixelColor(i, RgbColor(0, 0, 0));
    }
    NPBus->Show();
    currentFrame++;
    if (currentFrame >= pixel_count)
        currentFrame = 0;
}