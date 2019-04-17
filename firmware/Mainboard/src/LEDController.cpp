#include "LEDController.h"
LEDAnimator::LEDAnimator()
{
  stripe = new NeoPixelBus<NeoGrbFeature, Neo800KbpsMethod>(PIXEL_COUNT, PIN_NEOPIXEL);
}

void LEDAnimator::begin()
{
  stripe->Begin();
}

void LEDAnimator::update()
{
    
}

void LEDAnimator::Test(int selectedEffect){
    switch (selectedEffect)
    {

    case LED_ANIMATION_RGBLOOP:
    {
        // RGBLoop - no parameters
        RGBLoop();
        break;
    }

    case LED_ANIMATION_FADE_IN_OUT:
    {
        // FadeInOut - Color (red, green. blue)
        FadeInOut(0xff, 0x00, 0x00); // red
        FadeInOut(0xff, 0xff, 0xff); // white
        FadeInOut(0x00, 0x00, 0xff); // blue
        break;
    }

    case LED_ANIMATION_STROBE:
    {
        // Strobe - Color (red, green, blue), number of flashes, flash speed, end pause
        Strobe(0xff, 0xff, 0xff, 10, 50, 1000);
        break;
    }

    case LED_ANIMATION_HALLOWEEN:
    {
        // HalloweenEyes - Color (red, green, blue), Size of eye, space between eyes, fade (true/false), steps, fade delay, end pause
        HalloweenEyes(0xff, 0x00, 0x00,
                      1, 4,
                      true, random(5, 50), random(50, 150),
                      random(1000, 10000));
        HalloweenEyes(0xff, 0x00, 0x00,
                      1, 4,
                      true, random(5, 50), random(50, 150),
                      random(1000, 10000));
        break;
    }

    case LED_ANIMATION_CYLON_BOUNCE:
    {
        // CylonBounce - Color (red, green, blue), eye size, speed delay, end pause
        CylonBounce(0xff, 0x00, 0x00, 4, 10, 50);
        break;
    }

    case LED_ANIMATION_NEW_KITT:
    {
        // NewKITT - Color (red, green, blue), eye size, speed delay, end pause
        //NewKITT(0xff, 0x00, 0x00, 5, 10, 50);
        break;
    }

    case LED_ANIMATION_TWINKLE:
    {
        // Twinkle - Color (red, green, blue), count, speed delay, only one twinkle (true/false)
        Twinkle(0xff, 0x00, 0x00, 10, 100, false);
        break;
    }

    case LED_ANIMATION_TWINKLE_RANDOM:
    {
        // TwinkleRandom - twinkle count, speed delay, only one (true/false)
        TwinkleRandom(20, 100, false);
        break;
    }

    case LED_ANIMATION_SPARKLE:
    {
        // Sparkle - Color (red, green, blue), speed delay
        Sparkle(0xff, 0xff, 0xff, 0);
        break;
    }

    case LED_ANIMATION_SNOW_SPARKLE:
    {
        // SnowSparkle - Color (red, green, blue), sparkle delay, speed delay
        SnowSparkle(0x10, 0x10, 0x10, 20, random(100, 1000));
        break;
    }

    case LED_ANIMATION_RUNNING_LIGHTS:
    {
        // Running Lights - Color (red, green, blue), wave dealy
        RunningLights(0xff, 0x00, 0x00, 50); // red
        RunningLights(0xff, 0xff, 0xff, 50); // white
        RunningLights(0x00, 0x00, 0xff, 50); // blue
        break;
    }

    case LED_ANIMATION_COLOR_WHIPE:
    {
        // colorWipe - Color (red, green, blue), speed delay
        colorWipe(0x00, 0xff, 0x00, 50);
        colorWipe(0x00, 0x00, 0x00, 50);
        break;
    }

    case LED_ANIMATION_RAINBOW_CYCLE:
    {
        // rainbowCycle - speed delay
        rainbowCycle(20);
        break;
    }

    case LED_ANIMATION_THEATER_CHASE:
    {
        // theatherChase - Color (red, green, blue), speed delay
        theaterChase(0xff, 0, 0, 50);
        break;
    }

    case LED_ANIMATION_THEATER_CHASE_RAINBOW:
    {
        // theaterChaseRainbow - Speed delay
        theaterChaseRainbow(50);
        break;
    }

    case LED_ANIMATION_FIRE:
    {
        // Fire - Cooling rate, Sparking rate, speed delay
        Fire(55, 120, 15);
        break;
    }

        // simple bouncingBalls not included, since BouncingColoredBalls can perform this as well as shown below
        // BouncingColoredBalls - Number of balls, color (red, green, blue) array, continuous
        // CAUTION: If set to continuous then this effect will never stop!!!

    case LED_ANIMATION_BOUNCING_BALL:
    {
        // mimic BouncingBalls
        byte onecolor[1][3] = {{0xff, 0x00, 0x00}};
        BouncingColoredBalls(1, onecolor, false);
        break;
    }

    case LED_ANIMATION_BOUNCING_BALL_MULTICOLOR:
    {
        // multiple colored balls
        byte colors[3][3] = {{0xff, 0x00, 0x00},
                             {0xff, 0xff, 0xff},
                             {0x00, 0x00, 0xff}};
        BouncingColoredBalls(3, colors, false);
        break;
    }

    case LED_ANIMATION_METEOR_RAIN:
    {
        // meteorRain - Color (red, green, blue), meteor size, trail decay, random trail decay (true/false), speed delay
        meteorRain(0xff, 0xff, 0xff, 10, 64, true, 30);
        break;
    }
    }
}


void LEDAnimator::RGBLoop(){
  for(int j = 0; j < 3; j++ ) { 
    // Fade IN
    for(int k = 0; k < 256; k++) { 
      switch(j) { 
        case 0: setAll(k,0,0); break;
        case 1: setAll(0,k,0); break;
        case 2: setAll(0,0,k); break;
      }
      show();
      delay(3);
    }
    // Fade OUT
    for(int k = 255; k >= 0; k--) { 
      switch(j) { 
        case 0: setAll(k,0,0); break;
        case 1: setAll(0,k,0); break;
        case 2: setAll(0,0,k); break;
      }
      show();
      delay(3);
    }
  }
}

void LEDAnimator::FadeInOut(byte red, byte green, byte blue){
  float r, g, b;
      
  for(int k = 0; k < 256; k=k+1) { 
    r = (k/256.0)*red;
    g = (k/256.0)*green;
    b = (k/256.0)*blue;
    setAll(r,g,b);
    show();
  }
     
  for(int k = 255; k >= 0; k=k-2) {
    r = (k/256.0)*red;
    g = (k/256.0)*green;
    b = (k/256.0)*blue;
    setAll(r,g,b);
    show();
  }
}

void LEDAnimator::Strobe(byte red, byte green, byte blue, int StrobeCount, int FlashDelay, int EndPause){
  for(int j = 0; j < StrobeCount; j++) {
    setAll(red,green,blue);
    show();
    delay(FlashDelay);
    setAll(0,0,0);
    show();
    delay(FlashDelay);
  }
 
 delay(EndPause);
}

void LEDAnimator::HalloweenEyes(byte red, byte green, byte blue, 
                   int EyeWidth, int EyeSpace, 
                   boolean Fade, int Steps, int FadeDelay,
                   int EndPause){
  randomSeed(analogRead(0));
  
  int i;
  int StartPoint  = random( 0, PIXEL_COUNT - (2*EyeWidth) - EyeSpace );
  int Start2ndEye = StartPoint + EyeWidth + EyeSpace;
  
  for(i = 0; i < EyeWidth; i++) {
    setPixel(StartPoint + i, red, green, blue);
    setPixel(Start2ndEye + i, red, green, blue);
  }
  
  show();
  
  if(Fade==true) {
    float r, g, b;
  
    for(int j = Steps; j >= 0; j--) {
      r = j*(red/Steps);
      g = j*(green/Steps);
      b = j*(blue/Steps);
      
      for(i = 0; i < EyeWidth; i++) {
        setPixel(StartPoint + i, r, g, b);
        setPixel(Start2ndEye + i, r, g, b);
      }
      
      show();
      delay(FadeDelay);
    }
  }
  
  setAll(0,0,0); // Set all black
  
  delay(EndPause);
}

void LEDAnimator::CylonBounce(byte red, byte green, byte blue, int EyeSize, int SpeedDelay, int ReturnDelay){

  for(int i = 0; i < PIXEL_COUNT-EyeSize-2; i++) {
    setAll(0,0,0);
    setPixel(i, red/10, green/10, blue/10);
    for(int j = 1; j <= EyeSize; j++) {
      setPixel(i+j, red, green, blue); 
    }
    setPixel(i+EyeSize+1, red/10, green/10, blue/10);
    show();
    delay(SpeedDelay);
  }

  delay(ReturnDelay);

  for(int i = PIXEL_COUNT-EyeSize-2; i > 0; i--) {
    setAll(0,0,0);
    setPixel(i, red/10, green/10, blue/10);
    for(int j = 1; j <= EyeSize; j++) {
      setPixel(i+j, red, green, blue); 
    }
    setPixel(i+EyeSize+1, red/10, green/10, blue/10);
    show();
    delay(SpeedDelay);
  }
  
  delay(ReturnDelay);
}

void LEDAnimator::NewKITT(byte red, byte green, byte blue, int EyeSize, int SpeedDelay, int ReturnDelay){
  RightToLeft(red, green, blue, EyeSize, SpeedDelay, ReturnDelay);
  LeftToRight(red, green, blue, EyeSize, SpeedDelay, ReturnDelay);
  OutsideToCenter(red, green, blue, EyeSize, SpeedDelay, ReturnDelay);
  CenterToOutside(red, green, blue, EyeSize, SpeedDelay, ReturnDelay);
  LeftToRight(red, green, blue, EyeSize, SpeedDelay, ReturnDelay);
  RightToLeft(red, green, blue, EyeSize, SpeedDelay, ReturnDelay);
  OutsideToCenter(red, green, blue, EyeSize, SpeedDelay, ReturnDelay);
  CenterToOutside(red, green, blue, EyeSize, SpeedDelay, ReturnDelay);
}

// used by NewKITT
void LEDAnimator::CenterToOutside(byte red, byte green, byte blue, int EyeSize, int SpeedDelay, int ReturnDelay) {
  for(int i =((PIXEL_COUNT-EyeSize)/2); i>=0; i--) {
    setAll(0,0,0);
    
    setPixel(i, red/10, green/10, blue/10);
    for(int j = 1; j <= EyeSize; j++) {
      setPixel(i+j, red, green, blue); 
    }
    setPixel(i+EyeSize+1, red/10, green/10, blue/10);
    
    setPixel(PIXEL_COUNT-i, red/10, green/10, blue/10);
    for(int j = 1; j <= EyeSize; j++) {
      setPixel(PIXEL_COUNT-i-j, red, green, blue); 
    }
    setPixel(PIXEL_COUNT-i-EyeSize-1, red/10, green/10, blue/10);
    
    show();
    delay(SpeedDelay);
  }
  delay(ReturnDelay);
}

// used by NewKITT
void LEDAnimator::OutsideToCenter(byte red, byte green, byte blue, int EyeSize, int SpeedDelay, int ReturnDelay) {
  for(int i = 0; i<=((PIXEL_COUNT-EyeSize)/2); i++) {
    setAll(0,0,0);
    
    setPixel(i, red/10, green/10, blue/10);
    for(int j = 1; j <= EyeSize; j++) {
      setPixel(i+j, red, green, blue); 
    }
    setPixel(i+EyeSize+1, red/10, green/10, blue/10);
    
    setPixel(PIXEL_COUNT-i, red/10, green/10, blue/10);
    for(int j = 1; j <= EyeSize; j++) {
      setPixel(PIXEL_COUNT-i-j, red, green, blue); 
    }
    setPixel(PIXEL_COUNT-i-EyeSize-1, red/10, green/10, blue/10);
    
    show();
    delay(SpeedDelay);
  }
  delay(ReturnDelay);
}

// used by NewKITT
void LEDAnimator::LeftToRight(byte red, byte green, byte blue, int EyeSize, int SpeedDelay, int ReturnDelay) {
  for(int i = 0; i < PIXEL_COUNT-EyeSize-2; i++) {
    setAll(0,0,0);
    setPixel(i, red/10, green/10, blue/10);
    for(int j = 1; j <= EyeSize; j++) {
      setPixel(i+j, red, green, blue); 
    }
    setPixel(i+EyeSize+1, red/10, green/10, blue/10);
    show();
    delay(SpeedDelay);
  }
  delay(ReturnDelay);
}

// used by NewKITT
void LEDAnimator::RightToLeft(byte red, byte green, byte blue, int EyeSize, int SpeedDelay, int ReturnDelay) {
  for(int i = PIXEL_COUNT-EyeSize-2; i > 0; i--) {
    setAll(0,0,0);
    setPixel(i, red/10, green/10, blue/10);
    for(int j = 1; j <= EyeSize; j++) {
      setPixel(i+j, red, green, blue); 
    }
    setPixel(i+EyeSize+1, red/10, green/10, blue/10);
    show();
    delay(SpeedDelay);
  }
  delay(ReturnDelay);
}

void LEDAnimator::Twinkle(byte red, byte green, byte blue, int Count, int SpeedDelay, boolean OnlyOne) {
  setAll(0,0,0);
  
  for (int i=0; i<Count; i++) {
     setPixel(random(PIXEL_COUNT),red,green,blue);
     show();
     delay(SpeedDelay);
     if(OnlyOne) { 
       setAll(0,0,0); 
     }
   }
  
  delay(SpeedDelay);
}

void LEDAnimator::TwinkleRandom(int Count, int SpeedDelay, boolean OnlyOne) {
  setAll(0,0,0);
  
  for (int i=0; i<Count; i++) {
     setPixel(random(PIXEL_COUNT),random(0,255),random(0,255),random(0,255));
     show();
     delay(SpeedDelay);
     if(OnlyOne) { 
       setAll(0,0,0); 
     }
   }
  
  delay(SpeedDelay);
}

void LEDAnimator::Sparkle(byte red, byte green, byte blue, int SpeedDelay) {
  int Pixel = random(PIXEL_COUNT);
  setPixel(Pixel,red,green,blue);
  show();
  delay(SpeedDelay);
  setPixel(Pixel,0,0,0);
}

void LEDAnimator::SnowSparkle(byte red, byte green, byte blue, int SparkleDelay, int SpeedDelay) {
  setAll(red,green,blue);
  
  int Pixel = random(PIXEL_COUNT);
  setPixel(Pixel,0xff,0xff,0xff);
  show();
  delay(SparkleDelay);
  setPixel(Pixel,red,green,blue);
  show();
  delay(SpeedDelay);
}

void LEDAnimator::RunningLights(byte red, byte green, byte blue, int WaveDelay) {
  int Position=0;
  
  for(int i=0; i<PIXEL_COUNT*2; i++)
  {
      Position++; // = 0; //Position + Rate;
      for(int i=0; i<PIXEL_COUNT; i++) {
        // sine wave, 3 offset waves make a rainbow!
        //float level = sin(i+Position) * 127 + 128;
        //setPixel(i,level,0,0);
        //float level = sin(i+Position) * 127 + 128;
        setPixel(i,((sin(i+Position) * 127 + 128)/255)*red,
                   ((sin(i+Position) * 127 + 128)/255)*green,
                   ((sin(i+Position) * 127 + 128)/255)*blue);
      }
      
      show();
      delay(WaveDelay);
  }
}

void LEDAnimator::colorWipe(byte red, byte green, byte blue, int SpeedDelay) {
  for(uint16_t i=0; i<PIXEL_COUNT; i++) {
      setPixel(i, red, green, blue);
      show();
      delay(SpeedDelay);
  }
}

void LEDAnimator::rainbowCycle(int SpeedDelay) {
  byte *c;
  uint16_t i, j;

  for(j=0; j<256*5; j++) { // 5 cycles of all colors on wheel
    for(i=0; i< PIXEL_COUNT; i++) {
      c = Wheel((byte)(((i * 256 / PIXEL_COUNT) + j) & 255));
      setPixel(i, *c, *(c+1), *(c+2));
    }
    show();
    delay(SpeedDelay);
  }
}

// used by rainbowCycle and theaterChaseRainbow
byte * LEDAnimator::Wheel(byte WheelPos) {
  static byte c[3];
  
  if(WheelPos < 85) {
   c[0]=WheelPos * 3;
   c[1]=255 - WheelPos * 3;
   c[2]=0;
  } else if(WheelPos < 170) {
   WheelPos -= 85;
   c[0]=255 - WheelPos * 3;
   c[1]=0;
   c[2]=WheelPos * 3;
  } else {
   WheelPos -= 170;
   c[0]=0;
   c[1]=WheelPos * 3;
   c[2]=255 - WheelPos * 3;
  }

  return c;
}

void LEDAnimator::theaterChase(byte red, byte green, byte blue, int SpeedDelay) {
  for (int j=0; j<10; j++) {  //do 10 cycles of chasing
    for (int q=0; q < 3; q++) {
      for (int i=0; i < PIXEL_COUNT; i=i+3) {
        setPixel(i+q, red, green, blue);    //turn every third pixel on
      }
      show();
     
      delay(SpeedDelay);
     
      for (int i=0; i < PIXEL_COUNT; i=i+3) {
        setPixel(i+q, 0,0,0);        //turn every third pixel off
      }
    }
  }
}

void LEDAnimator::theaterChaseRainbow(int SpeedDelay) {
  byte *c;
  
  for (int j=0; j < 256; j++) {     // cycle all 256 colors in the wheel
    for (int q=0; q < 3; q++) {
        for (int i=0; i < PIXEL_COUNT; i=i+3) {
          c = Wheel( (i+j) % 255);
          setPixel(i+q, *c, *(c+1), *(c+2));    //turn every third pixel on
        }
        show();
       
        delay(SpeedDelay);
       
        for (int i=0; i < PIXEL_COUNT; i=i+3) {
          setPixel(i+q, 0,0,0);        //turn every third pixel off
        }
    }
  }
}

void LEDAnimator::Fire(int Cooling, int Sparking, int SpeedDelay) {
  static byte heat[PIXEL_COUNT];
  int cooldown;
  
  // Step 1.  Cool down every cell a little
  for( int i = 0; i < PIXEL_COUNT; i++) {
    cooldown = random(0, ((Cooling * 10) / PIXEL_COUNT) + 2);
    
    if(cooldown>heat[i]) {
      heat[i]=0;
    } else {
      heat[i]=heat[i]-cooldown;
    }
  }
  
  // Step 2.  Heat from each cell drifts 'up' and diffuses a little
  for( int k= PIXEL_COUNT - 1; k >= 2; k--) {
    heat[k] = (heat[k - 1] + heat[k - 2] + heat[k - 2]) / 3;
  }
    
  // Step 3.  Randomly ignite new 'sparks' near the bottom
  if( random(255) < Sparking ) {
    int y = random(7);
    heat[y] = heat[y] + random(160,255);
    //heat[y] = random(160,255);
  }

  // Step 4.  Convert heat to LED colors
  for( int j = 0; j < PIXEL_COUNT; j++) {
    setPixelHeatColor(j, heat[j] );
  }

  show();
  delay(SpeedDelay);
}

void LEDAnimator::setPixelHeatColor (int Pixel, byte temperature) {
  // Scale 'heat' down from 0-255 to 0-191
  byte t192 = round((temperature/255.0)*191);
 
  // calculate ramp up from
  byte heatramp = t192 & 0x3F; // 0..63
  heatramp <<= 2; // scale up to 0..252
 
  // figure out which third of the spectrum we're in:
  if( t192 > 0x80) {                     // hottest
    setPixel(Pixel, 255, 255, heatramp);
  } else if( t192 > 0x40 ) {             // middle
    setPixel(Pixel, 255, heatramp, 0);
  } else {                               // coolest
    setPixel(Pixel, heatramp, 0, 0);
  }
}

void LEDAnimator::BouncingColoredBalls(int BallCount, byte colors[][3], boolean continuous) {
  float Gravity = -9.81;
  int StartHeight = 1;
  
  float Height[BallCount];
  float ImpactVelocityStart = sqrt( -2 * Gravity * StartHeight );
  float ImpactVelocity[BallCount];
  float TimeSinceLastBounce[BallCount];
  int   Position[BallCount];
  long  ClockTimeSinceLastBounce[BallCount];
  float Dampening[BallCount];
  boolean ballBouncing[BallCount];
  boolean ballsStillBouncing = true;
  
  for (int i = 0 ; i < BallCount ; i++) {   
    ClockTimeSinceLastBounce[i] = millis();
    Height[i] = StartHeight;
    Position[i] = 0; 
    ImpactVelocity[i] = ImpactVelocityStart;
    TimeSinceLastBounce[i] = 0;
    Dampening[i] = 0.90 - float(i)/pow(BallCount,2);
    ballBouncing[i]=true; 
  }

  while (ballsStillBouncing) {
    for (int i = 0 ; i < BallCount ; i++) {
      TimeSinceLastBounce[i] =  millis() - ClockTimeSinceLastBounce[i];
      Height[i] = 0.5 * Gravity * pow( TimeSinceLastBounce[i]/1000 , 2.0 ) + ImpactVelocity[i] * TimeSinceLastBounce[i]/1000;
  
      if ( Height[i] < 0 ) {                      
        Height[i] = 0;
        ImpactVelocity[i] = Dampening[i] * ImpactVelocity[i];
        ClockTimeSinceLastBounce[i] = millis();
  
        if ( ImpactVelocity[i] < 0.01 ) {
          if (continuous) {
            ImpactVelocity[i] = ImpactVelocityStart;
          } else {
            ballBouncing[i]=false;
          }
        }
      }
      Position[i] = round( Height[i] * (PIXEL_COUNT - 1) / StartHeight);
    }

    ballsStillBouncing = false; // assume no balls bouncing
    for (int i = 0 ; i < BallCount ; i++) {
      setPixel(Position[i],colors[i][0],colors[i][1],colors[i][2]);
      if ( ballBouncing[i] ) {
        ballsStillBouncing = true;
      }
    }
    
    show();
    setAll(0,0,0);
  }
}

void LEDAnimator::meteorRain(byte red, byte green, byte blue, byte meteorSize, byte meteorTrailDecay, boolean meteorRandomDecay, int SpeedDelay) {  
  setAll(0,0,0);
  
  for(int i = 0; i < PIXEL_COUNT+PIXEL_COUNT; i++) {
    
    
    // fade brightness all LEDs one step
    for(int j=0; j<PIXEL_COUNT; j++) {
      if( (!meteorRandomDecay) || (random(10)>5) ) {
        fadeToBlack(j, meteorTrailDecay );        
      }
    }
    
    // draw meteor
    for(int j = 0; j < meteorSize; j++) {
      if( ( i-j <PIXEL_COUNT) && (i-j>=0) ) {
        setPixel(i-j, red, green, blue);
      } 
    }
   
    show();
    delay(SpeedDelay);
  }
}

// used by meteorrain
void LEDAnimator::fadeToBlack(int ledNo, byte fadeValue) {
    // NeoPixel
    RgbColor oldColor;
    byte r,g,b;
    oldColor = stripe->GetPixelColor(ledNo);
    r=(oldColor.R<=10)? 0 : (int) oldColor.R-(oldColor.R*fadeValue/256);
    g=(oldColor.G<=10)? 0 : (int) oldColor.G-(oldColor.G*fadeValue/256);
    b=(oldColor.B<=10)? 0 : (int) oldColor.B-(oldColor.B*fadeValue/256);
    setPixel(ledNo, r,g,b);
}


// Set a LED color (not yet visible)
void LEDAnimator::setPixel(int Pixel, byte red, byte green, byte blue) {
  stripe->SetPixelColor(Pixel, RgbColor(red,green,blue));
}

// Set all LEDs to a given color and apply it (visible)
void LEDAnimator::setAll(byte red, byte green, byte blue) {
  for(int i = 0; i < PIXEL_COUNT; i++ ) {
    setPixel(i, red, green, blue); 
  }
  show();
}

void LEDAnimator::show(){
  stripe->Show();
}
