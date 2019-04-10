#ifndef LED_CONTROLLER_H
#define LED_CONTROLLER_H

#include "FastLED.h"
#include "Configuration.h"

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

class LEDController
{
public:
    LEDController();
    void begin();
    void update();
    void Test(int selectedEffect);

private:
    CRGB LEDs[PIXEL_COUNT];

    void RGBLoop();
    void FadeInOut(byte red, byte green, byte blue);
    void Strobe(byte red, byte green, byte blue, int StrobeCount, int FlashDelay, int EndPause);
    void HalloweenEyes(byte red, byte green, byte blue, int EyeWidth, int EyeSpace, boolean Fade, int Steps, int FadeDelay, int EndPause);
    void CylonBounce(byte red, byte green, byte blue, int EyeSize, int SpeedDelay, int ReturnDelay);
    void NewKITT(byte red, byte green, byte blue, int EyeSize, int SpeedDelay, int ReturnDelay);
    void CenterToOutside(byte red, byte green, byte blue, int EyeSize, int SpeedDelay, int ReturnDelay);
    void OutsideToCenter(byte red, byte green, byte blue, int EyeSize, int SpeedDelay, int ReturnDelay);
    void LeftToRight(byte red, byte green, byte blue, int EyeSize, int SpeedDelay, int ReturnDelay);
    void RightToLeft(byte red, byte green, byte blue, int EyeSize, int SpeedDelay, int ReturnDelay);
    void Twinkle(byte red, byte green, byte blue, int Count, int SpeedDelay, boolean OnlyOne);
    void TwinkleRandom(int Count, int SpeedDelay, boolean OnlyOne);
    void Sparkle(byte red, byte green, byte blue, int SpeedDelay);
    void SnowSparkle(byte red, byte green, byte blue, int SparkleDelay, int SpeedDelay);
    void RunningLights(byte red, byte green, byte blue, int WaveDelay);
    void colorWipe(byte red, byte green, byte blue, int SpeedDelay);
    void rainbowCycle(int SpeedDelay);
    byte * Wheel(byte WheelPos);
    void theaterChase(byte red, byte green, byte blue, int SpeedDelay);
    void theaterChaseRainbow(int SpeedDelay);
    void Fire(int Cooling, int Sparking, int SpeedDelay);
    void setPixelHeatColor (int Pixel, byte temperature);
    void BouncingColoredBalls(int BallCount, byte colors[][3], boolean continuous);
    void meteorRain(byte red, byte green, byte blue, byte meteorSize, byte meteorTrailDecay, boolean meteorRandomDecay, int SpeedDelay);  
    void fadeToBlack(int ledNo, byte fadeValue);
    void showStrip();
    void setPixel(int Pixel, byte red, byte green, byte blue);
    void setAll(byte red, byte green, byte blue);
};

#endif