#ifndef LEDCONTROLLER_H
#define LEDCONTROLLER_H

#include "Shared.h"

#if defined(ARDUINO) && ARDUINO >= 100
  #include "Arduino.h"
#else
  #include "WProgram.h"
#endif

class LEDController {
public:
	static const RGB Black;
	static const RGB White;

	LEDController(int pin_r, int pin_g, int pin_b);
	void begin();
	RGB getCurrentColor();

	void update(bool force = false);
	void setColorA(RGB new_color);
	void setColorA(byte* new_color);
	void setColorB(RGB new_color);
	void setColorB(byte* new_color);	
	void setType(byte type);
	void setPeriod(unsigned int new_period);
	RGB getFadedColor(RGB from, RGB to, float relative);

private:
	unsigned long period;
	RGB current_color;
	int pin_r, pin_g, pin_b;
	int type;
	RGB color_A;
	RGB color_B;
	unsigned long last_change;
	void setColor(RGB new_color);
	bool even;
	unsigned long fade_start;
};

#endif
