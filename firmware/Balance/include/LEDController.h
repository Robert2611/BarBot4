#ifndef LEDCONTROLLER_H
#define LEDCONTROLLER_H

#include "Shared.h"
#include "Arduino.h"

class LEDController {
public:
	static const RGB_t Black;
	static const RGB_t White;

	LEDController(int pin_r, int pin_g, int pin_b);
	void begin();
	RGB_t getCurrentColor();

	void update(bool force = false);
	void setColorA(RGB_t new_color);
	void setColorA(byte* new_color);
	void setColorB(RGB_t new_color);
	void setColorB(byte* new_color);	
	void setType(byte type);
	void setPeriod(unsigned int new_period);
	RGB_t getFadedColor(RGB_t from, RGB_t to, float relative);

private:
	unsigned long period;
	RGB_t current_color;
	int pin_r, pin_g, pin_b;
	int type;
	RGB_t color_A;
	RGB_t color_B;
	unsigned long last_change;
	void setColor(RGB_t new_color);
	bool even;
	unsigned long fade_start;
};

#endif
