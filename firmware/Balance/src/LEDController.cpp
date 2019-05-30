#include "LEDController.h"

LEDController::LEDController(int data_pin_)
{
	data_pin = data_pin_;
	//initialize as off state
	type = BALANCE_LED_TYPE_OFF;
}

void LEDController::begin()
{
	stripe = new NeoPixelBus<NeoGrbFeature, Neo800KbpsMethod>(BALANCE_LED_PIXEL_COUNT, data_pin);
	//force writing the state
	setType(BALANCE_LED_TYPE_OFF);
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
			stripe->ClearTo({255, 0, 0});
			stripe->Show();
		}
	}
	break;

	case BALANCE_LED_TYPE_OFF:
	{
		if (force)
		{
			stripe->ClearTo({0, 0, 0});
			stripe->Show();
		}
	}
	break;

	case BALANCE_LED_TYPE_BLINK:
	{
		if (force || temp_millis >= last_change + 1000)
		{
			//blink green
			if (frame == 1)
				stripe->ClearTo({255, 0, 0});
			else
				stripe->ClearTo({0, 0, 0});

			stripe->Show();
			frame = !frame;
			last_change = temp_millis;
		}
	}
	break;

	case BALANCE_LED_TYPE_ROTATE:
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
				if ((i - frame) % 3 == 0)
					color = {0, 255, 0};
				stripe->SetPixelColor(i, color);
			}
			stripe->Show();
		}
	}
	break;

	case BALANCE_LED_TYPE_PULSING:
	{
		if (force || temp_millis > frame_start_millis + 50)
		{
			if (!force)
				frame++;
			if (frame >= 50)
				frame = 0;
			frame_start_millis = temp_millis;
			byte brightness = 255 * (2 * frame / 50.0 - 1) * (2 * frame / 50.0 - 1);
			RgbColor color = {0, brightness, 0};
			stripe->ClearTo(color);
			stripe->Show();
		}
	}
	break;

	case BALANCE_LED_TYPE_CHASE:
	{
		if (force || temp_millis > frame_start_millis + 50)
		{
			int half = BALANCE_LED_PIXEL_COUNT / 2;
			if (!force)
				frame++;
			if (frame >= half)
				frame = 0;
			float pos = frame;
			frame_start_millis = temp_millis;
			for (int i = 0; i < BALANCE_LED_PIXEL_COUNT; i++)
			{
				int dist = abs(i % half - pos);
				if (dist > (half - 1) / 2)
					dist = half - dist;
				float brightness = max(1 - dist / 6.0, 0);
				RgbColor color = {0, (byte)(255 * brightness * brightness), 0};
				stripe->SetPixelColor(i, color);
			}
			stripe->Show();
		}
	}
	break;
	}
}

void LEDController::setType(byte new_type)
{
	frame = 0;
	type = new_type;
	//update calling with force attribute
	update(true);
}