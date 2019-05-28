#include "LEDController.h"

LEDController::LEDController(int data_pin_)
{
	data_pin = data_pin_;
	//initialize with all LEDs off
	type = BALANCE_LED_TYPE_OFF;
	period = 1000;
}

void LEDController::begin()
{
	stripe = new NeoPixelBus<NeoGrbFeature, Neo800KbpsMethod>(BALANCE_LED_PIXEL_COUNT, data_pin);
	type = BALANCE_LED_TYPE_OFF;
}

void LEDController::setColor(RgbColor new_color)
{
	stripe->ClearTo(new_color);
	stripe->Show();
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
			setColor({255, 0, 0});
		}
	}
	break;

	case BALANCE_LED_TYPE_OFF:
	{
		if (force)
			setColor({0, 0, 0});
	}
	break;

	case BALANCE_LED_TYPE_BLINK:
	{
		if (temp_millis >= last_change + (period / 2) || force)
		{
			//blink green
			if (frame == 1)
				setColor({0, 255, 0});
			else
				setColor({0, 0, 0});
			frame = frame ? 0 : 1;
			last_change = temp_millis;
		}
	}
	break;

	case BALANCE_LED_TYPE_FADE:
	{

		if (force || temp_millis > frame_start_millis + 100)
		{
			if (!force)
				frame++;
			if (frame >= 3)
				frame = 0;
			frame_start_millis = temp_millis;
			for (int i = 0; i < BALANCE_LED_PIXEL_COUNT; i++)
			{
				RgbColor color = {0, 0, 0};
				if ((i + frame) % 3 == 0)
					color = {0, 0, 255};
				stripe->SetPixelColor(i, color);
			}
			stripe->Show();
		}
		/* 		RGB_t new_color;
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
		setColor(new_color); */
	}
	break;
	}
}

/* RGB_t LEDController::getFadedColor(RGB_t from, RGB_t to, float relative)
{
	if (relative < 0)
		relative = 0;
	else if (relative > 1)
		relative = 1;
	return {
		(byte)(from.r + (to.r - from.r) * relative),
		(byte)(from.g + (to.g - from.g) * relative),
		(byte)(from.b + (to.b - from.b) * relative)};
} */

void LEDController::setType(byte new_type)
{
	type = new_type;
	frame = 0;
	//update calling with force attribute
	update(true);
}