#ifndef LED_CONTROLLER_H
#define LED_CONTROLLER_H

#include "Configuration.h"
#include "Shared.h"
#include "NeoPixelBus.h"

// Animations taken from
// https://www.tweaking4all.com/hardware/arduino/adruino-led-strip-effects/

#define LED_ANIMATION_RGBLOOP 0
#define LED_ANIMATION_FADE_IN_OUT 1
#define LED_ANIMATION_STROBE 2
#define LED_ANIMATION_HALLOWEEN 3
#define LED_ANIMATION_CYLON_BOUNCE 4
#define LED_ANIMATION_NEW_KITT 5
#define LED_ANIMATION_TWINKLE 6
#define LED_ANIMATION_TWINKLE_RANDOM 7
#define LED_ANIMATION_SPARKLE 8
#define LED_ANIMATION_SNOW_SPARKLE 9
#define LED_ANIMATION_RUNNING_LIGHTS 10
#define LED_ANIMATION_COLOR_WHIPE 11
#define LED_ANIMATION_RAINBOW_CYCLE 12
#define LED_ANIMATION_THEATER_CHASE 13
#define LED_ANIMATION_THEATER_CHASE_RAINBOW 14
#define LED_ANIMATION_FIRE 15
#define LED_ANIMATION_BOUNCING_BALL 16
#define LED_ANIMATION_BOUNCING_BALL_MULTICOLOR 17
#define LED_ANIMATION_METEOR_RAIN 18

class LEDAnimator
{
public:
    LEDAnimator();
    void begin();
    void update();
    void Test(int selectedEffect);
    void show();

private:
    NeoPixelBus<NeoGrbFeature, Neo800KbpsMethod>* stripe;

    void RGBLoop();
    void FadeInOut(uint8_t red, uint8_t green, uint8_t blue);
    void Strobe(uint8_t red, uint8_t green, uint8_t blue, int StrobeCount, int FlashDelay, int EndPause);
    void HalloweenEyes(uint8_t red, uint8_t green, uint8_t blue, int EyeWidth, int EyeSpace, bool Fade, int Steps, int FadeDelay, int EndPause);
    void CylonBounce(uint8_t red, uint8_t green, uint8_t blue, int EyeSize, int SpeedDelay, int ReturnDelay);
    void NewKITT(uint8_t red, uint8_t green, uint8_t blue, int EyeSize, int SpeedDelay, int ReturnDelay);
    void CenterToOutside(uint8_t red, uint8_t green, uint8_t blue, int EyeSize, int SpeedDelay, int ReturnDelay);
    void OutsideToCenter(uint8_t red, uint8_t green, uint8_t blue, int EyeSize, int SpeedDelay, int ReturnDelay);
    void LeftToRight(uint8_t red, uint8_t green, uint8_t blue, int EyeSize, int SpeedDelay, int ReturnDelay);
    void RightToLeft(uint8_t red, uint8_t green, uint8_t blue, int EyeSize, int SpeedDelay, int ReturnDelay);
    void Twinkle(uint8_t red, uint8_t green, uint8_t blue, int Count, int SpeedDelay, boolean OnlyOne);
    void TwinkleRandom(int Count, int SpeedDelay, boolean OnlyOne);
    void Sparkle(uint8_t red, uint8_t green, uint8_t blue, int SpeedDelay);
    void SnowSparkle(uint8_t red, uint8_t green, uint8_t blue, int SparkleDelay, int SpeedDelay);
    void RunningLights(uint8_t red, uint8_t green, uint8_t blue, int WaveDelay);
    void colorWipe(uint8_t red, uint8_t green, uint8_t blue, int SpeedDelay);
    void rainbowCycle(int SpeedDelay);
    uint8_t * Wheel(uint8_t WheelPos);
    void theaterChase(uint8_t red, uint8_t green, uint8_t blue, int SpeedDelay);
    void theaterChaseRainbow(int SpeedDelay);
    void Fire(int Cooling, int Sparking, int SpeedDelay);
    void setPixelHeatColor (int Pixel, uint8_t temperature);
    void BouncingColoredBalls(int BallCount, uint8_t colors[][3], boolean continuous);
    void meteorRain(uint8_t red, uint8_t green, uint8_t blue, uint8_t meteorSize, uint8_t meteorTrailDecay, boolean meteorRandomDecay, int SpeedDelay);  
    void fadeToBlack(int ledNo, uint8_t fadeValue);
    void showStrip();
    void setPixel(int Pixel, uint8_t red, uint8_t green, uint8_t blue);
    void setAll(uint8_t red, uint8_t green, uint8_t blue);
};

#endif