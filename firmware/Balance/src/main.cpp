#include "Arduino.h"
#include "HX711.h"
#include "Butterworth.h"
#include "Wire.h"
#include "Shared.h"
#include "LEDController.h"
#include "WireProtocol.h"

//arduino nano
#define BALANCE_PIN_DATA A2
#define BALANCE_PIN_CLOCK A3
#define BALANCE_GAIN 128
#define LED_DATA_PIN A0
#define LED_PIN 1

//#define SERIAL_DEBUG

//used for butterorth filter
#define FILTER_CUTOFF_FREQUENCY 5 //Hz
#define BALANCE_SAMPLING_RATE 89  //Hz

//instatiate classes
HX711 balance;
Butterworth butterworth;
LEDController LEDC(LED_DATA_PIN);

//variables
bool new_data = false;
byte i2c_command = 0xFF;
float raw_value, filtered_value;

bool LED_high = false;

void handleSetters(int parameters_count)
{
  switch (i2c_command)
  {
  case BALANCE_CMD_SET_LED_TYPE:
    if (parameters_count != 1)
      break;
    byte data;
    data = Wire.read();
    LEDC.setType(data);
    break;
  }
}

void handleGetters()
{
  switch (i2c_command)
  {
  case BALANCE_CMD_HAS_NEW_DATA:
    Wire.write(new_data);
    new_data = false;
    break;
  case BALANCE_CMD_GET_DATA_RAW:
    WireProtocol::sendFloat(raw_value);
    break;
  case BALANCE_CMD_GET_DATA:
    WireProtocol::sendFloat(filtered_value);
    digitalWrite(LED_PIN, LED_high ? HIGH : LOW);
    LED_high = !LED_high;
    break;
  //no command byte set or unknown command
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
  handleSetters(count - 1);
}

void setup()
{
#ifdef SERIAL_DEBUG
  Serial.begin(115200);
  Serial.println("Serial debug enabled");
#endif
  pinMode(LED_PIN, OUTPUT);
  //blink to signal ready
  digitalWrite(LED_PIN, HIGH);
  delay(100);
  digitalWrite(LED_PIN, LOW);
  delay(100);
  digitalWrite(LED_PIN, HIGH);
  delay(500);
  digitalWrite(LED_PIN, LOW);
  //initialize balance
  balance.begin(BALANCE_PIN_DATA, BALANCE_PIN_CLOCK, BALANCE_GAIN);
  //initialize filter
  butterworth.calculateCoefficients((float)FILTER_CUTOFF_FREQUENCY / BALANCE_SAMPLING_RATE);
  //start i2c communication
  Wire.begin(BALANCE_BOARD_ADDRESS);
  //disable pullups for i2c
  digitalWrite(SCL, LOW);
  digitalWrite(SDA, LOW);
  Wire.onReceive(recieved);
  Wire.onRequest(handleGetters);
  //start the LED Controller
  LEDC.begin();
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