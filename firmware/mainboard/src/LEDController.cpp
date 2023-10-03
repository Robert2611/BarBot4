#include "LEDController.h"
LEDController::LEDController()
{
	stripe = new NeoPixelBus<NeoGrbFeature, Neo800KbpsMethod>(PIXEL_COUNT, PIN_NEOPIXEL);
}

void LEDController::begin()
{
	pinMode(PIN_NEOPIXEL, OUTPUT);
	stripe->Begin();
	setType(LEDType::LED_TYPE_OFF);
}

void LEDController::update(bool force)
{
	unsigned long temp_millis = millis();
	switch (type)
	{

	case LEDType::LED_TYPE_OFF:
	{
		if (force)
		{
			stripe->ClearTo({0, 0, 0});
			stripe->Show();
		}
	}
	break;

	case LEDType::LED_TYPE_CONTINOUS:
	{
		if (force)
		{
			stripe->ClearTo({0, 255, 0});
			stripe->Show();
		}
	}
	break;

	case LEDType::LED_TYPE_BLINK:
	{
		if (force || (temp_millis >= last_change + 1000))
		{
			//blink green
			if (frame == 1)
				stripe->ClearTo({255, 255, 0});
			else
				stripe->ClearTo({0, 0, 0});

			stripe->Show();
			frame = !frame;
			last_change = temp_millis;
		}
	}
	break;

	case LEDType::LED_TYPE_RAINBOW:
	{
		if (force || (temp_millis > frame_start_millis + 50))
		{
			if (!force)
				frame++;
			if (frame >= PIXEL_COUNT)
				frame = 0;
			frame_start_millis = temp_millis;
			for (int i = 0; i < PIXEL_COUNT; i++)
			{
				int pos = (i + frame) % PIXEL_COUNT;
				HsbColor color = {(float)pos / (PIXEL_COUNT - 1), 1.0, 0.8};
				stripe->SetPixelColor(i, color);
			}
			stripe->Show();
		}
	}
	break;

	case LEDType::LED_TYPE_POSITION_WATERFALL:
	{
		if (force || (temp_millis > frame_start_millis + 50))
		{
			int period = 10;
			if (!force)
				frame++;
			if (frame >= period)
				frame = 0;
			frame_start_millis = temp_millis;
			for (int i = 0; i < PIXEL_COUNT; i++)
			{
				int dist = (abs(i - platform_position) + frame) % period;
				if (dist > (period - 1) / 2)
					dist = period - dist;
				float brightness = max(1 - dist / 3.0, 0.0);
				RgbColor color = {0, 0, (byte)(255 * brightness * brightness)};
				stripe->SetPixelColor(i, color);
			}
			stripe->Show();
		}
	}
	break;

	case LEDType::LED_TYPE_DRAFT_POSITION:
	{
		if (force || (temp_millis > frame_start_millis + 80))
		{
			int period = 20;
			if (!force)
				frame++;
			if (frame >= period)
				frame = 0;
			frame_start_millis = temp_millis;
			for (int i = 0; i < PIXEL_COUNT; i++)
			{
				int dist = (abs(i - draft_position) + frame) % period;
				if (dist > (period - 1) / 2)
					dist = period - dist;
				float brightness = max(1 - dist / 3.0, 0.0);
				if (abs(i - draft_position) < 2)
					brightness = 1;
				RgbColor color = {0, (byte)(255 * brightness * brightness), 0};
				stripe->SetPixelColor(i, color);
			}
			stripe->Show();
		}
	}
	break;
	}
}

void LEDController::setType(int new_type)
{
	type = new_type;
	frame = 0;
	//update calling with force attribute
	update(true);
}

void LEDController::setPlatformPosition(float position_in_mm)
{
	platform_position = position_in_mm / 1000 * PIXEL_COUNT;
}

void LEDController::setDraftPosition(float position_in_mm)
{
	draft_position = position_in_mm / 1000 * PIXEL_COUNT;
}