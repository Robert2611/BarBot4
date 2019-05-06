#include "Arduino.h"
#include "HX711.h"
#include "Butterworth.h"
#include "Wire.h"
#include "Shared.h"
#include "LEDController.h"

#ifdef __AVR_ATmega328P__
//arduino nano
#define BALANCE_PIN_DATA A2
#define BALANCE_PIN_CLOCK A3
#define BALANCE_GAIN 128
#define LED_PIN_R 9
#define LED_PIN_G 10
#define LED_PIN_B 11
#else
//atmega48
#define BALANCE_PIN_DATA 1
#define BALANCE_PIN_CLOCK 0
#define BALANCE_GAIN 128
#define LED_PIN_R 6
#define LED_PIN_G 5
#define LED_PIN_B 3
#endif

#define SERIAL_DEBUG

//used for butterorth filter
#define FILTER_CUTOFF_FREQUENCY 5 //Hz
#define BALANCE_SAMPLING_RATE 89  //Hz

//instatiate classes
HX711 balance;
Butterworth butterworth;
LEDController LEDC(LED_PIN_R, LED_PIN_G, LED_PIN_B);

//variables
bool new_data = false;
byte i2c_command = 0xFF;
float raw_value, filtered_value;

void commandRecieved(int parameters_count)
{
  switch (i2c_command)
  {
  case BALANCE_CMDLED_SET_COLOR_A:
  {
    if (parameters_count != 3)
      break;
    byte data[3];
    Wire.readBytes(data, 3);
    LEDC.setColorA(data);
  }
  break;
  case BALANCE_CMDLED_SET_COLOR_B:
  {
    if (parameters_count != 3)
      break;
    byte data[3];
    Wire.readBytes(data, 3);
    LEDC.setColorB(data);
  }
  break;
  case BALANCE_CMDLED_SET_TYPE:
  {
    if (parameters_count != 1)
      break;
    byte data;
    data = Wire.read();
    LEDC.setType(data);
  }
  case BALANCE_CMDLED_SET_TIME:
  {
    byte s = sizeof(unsigned int);
    if (parameters_count != s)
      break;
    byte data[s];
    Wire.readBytes(data, s);
    LEDC.setPeriod((unsigned int)data);
  }
  break;
  }
}

void request()
{
  switch (i2c_command)
  {
  case BALANCE_CMDBALANCE_HAS_NEW_DATA:
  {
    Wire.write(new_data);
    new_data = false;
  }
  break;
  case BALANCE_CMDBALANCE_GET_DATA_RAW:
  {
    I2C_SEND_FLOAT(raw_value);
  }
  break;
  case BALANCE_CMDBALANCE_GET_DATA:
  {
    I2C_SEND_FLOAT(filtered_value);
  }
  break;
  //no register set or unknown register
  case 0xFF:
  default:
#ifdef SERIAL_DEBUG
    Serial.println("Wrong request");
#endif
    Wire.write(0);
    i2c_command = 0xFF;
    break;
  }
}


void recieved(int count)
{
  //continue only if command byte was set
  if (count < 1)
    return;
  //save the command byte
  i2c_command = Wire.read();
  //handle messages that are only setters
  commandRecieved(count - 1);
}

void setup()
{
#ifdef SERIAL_DEBUG
  Serial.begin(115200);
  Serial.println("Serial debug enabled");
#endif
  //initialize balance
  balance.begin(BALANCE_PIN_DATA, BALANCE_PIN_CLOCK, BALANCE_GAIN);
  //initialize filter
  butterworth.calculateCoefficients((float)FILTER_CUTOFF_FREQUENCY / BALANCE_SAMPLING_RATE);
  //disable pullups for i2c
  digitalWrite(SCL, LOW);
  digitalWrite(SDA, LOW);
  //start i2c communication
  Wire.begin(BALANCE_BOARD_ADDRESS);
  Wire.onReceive(recieved);
  Wire.onRequest(request);
  //start the LED Controller
  LEDC.begin();
  LEDC.setColorA({255, 0, 0});
  LEDC.setColorB({0, 255, 0});
  LEDC.setPeriod(1000);
  LEDC.setType(BALANCE_LED_TYPE_BLINK);
}

void loop()
{
  //get data from HX711 if it has new
  if (balance.is_ready())
  {
    raw_value = balance.read();
    filtered_value = butterworth.filter(raw_value);
    new_data = true;
  }
  //update the LEDs
  LEDC.update();
}