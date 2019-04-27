#include "LEDController.h"

const RGB_t LEDController::Black = {0, 0, 0};
const RGB_t LEDController::White = {255, 255, 255};

LEDController::LEDController(int pin_r_, int pin_g_, int pin_b_)
{
	pin_r = pin_r_;
	pin_g = pin_g_;
	pin_b = pin_b_;
	type = BALANCE_LED_TYPE_OFF;
	period = 1000;
}

void LEDController::begin()
{
	pinMode(pin_r, OUTPUT);
	pinMode(pin_g, OUTPUT);
	pinMode(pin_b, OUTPUT);
	type = BALANCE_LED_TYPE_OFF;
}

void LEDController::setColor(RGB_t new_color)
{
	analogWrite(pin_r, new_color.r);
	analogWrite(pin_g, new_color.g);
	analogWrite(pin_b, new_color.b);
	current_color = new_color;
}

void LEDController::update(bool force)
{
	unsigned long temp_millis = millis();

	switch (type)
	{

	case BALANCE_LED_TYPE_CONTINOUS:
	{
		if (force)
		{
			setColor(color_A);
		}
	}
	break;

	case BALANCE_LED_TYPE_OFF:
	{
		if (force)
			setColor(Black);
	}
	break;

	case BALANCE_LED_TYPE_BLINK:
	{
		if (temp_millis >= last_change + (period / 2) || force)
		{
			if (even)
				setColor(color_A);
			else
				setColor(color_B);
			even = !even;
			last_change = temp_millis;
		}
	}
	break;

	case BALANCE_LED_TYPE_FADE:
	{
		if (force)
			fade_start = temp_millis;
		RGB_t new_color;
		while (temp_millis > fade_start + (period / 2))
		{
			//invert direction
			fade_start += (period / 2);
			even = !even;
		}
		if (even)
			new_color = getFadedColor(color_A, color_B, (float)(temp_millis - fade_start) / (period / 2));
		else
			new_color = getFadedColor(color_B, color_A, (float)(temp_millis - fade_start) / (period / 2));
		setColor(new_color);
	}
	break;
	}
}

RGB_t LEDController::getFadedColor(RGB_t from, RGB_t to, float relative)
{
	if (relative < 0)
		relative = 0;
	else if (relative > 1)
		relative = 1;
	return {
		(byte)(from.r + (to.r - from.r) * relative),
		(byte)(from.g + (to.g - from.g) * relative),
		(byte)(from.b + (to.b - from.b) * relative)};
}

RGB_t LEDController::getCurrentColor()
{
	return current_color;
}

void LEDController::setColorA(RGB_t new_color)
{
	color_A = new_color;
}
void LEDController::setColorA(byte *raw_color)
{
	RGB_t newColor;
	memcpy(&newColor, raw_color, 3);
	setColorA(newColor);
}
void LEDController::setColorB(RGB_t new_color)
{
	color_B = new_color;
}
void LEDController::setColorB(byte *raw_color)
{
	RGB_t newColor;
	memcpy(&newColor, raw_color, 3);
	setColorB(newColor);
}

void LEDController::setType(byte new_type)
{
	type = new_type;
	update(true);
}

void LEDController::setPeriod(unsigned int new_period)
{
	period = new_period;
}