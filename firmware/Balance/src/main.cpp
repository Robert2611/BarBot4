#include "Arduino.h"
#include "HX711.h"
#include "Butterworth.h"
#include "Wire.h"
#include "Shared.h"

#ifdef __AVR_ATmega328P__
//arduino nano
#define BALANCE_PIN_DATA 4
#define BALANCE_PIN_CLOCK 5
#define BALANCE_GAIN 128

#else
//actual
#define BALANCE_PIN_DATA 4
#define BALANCE_PIN_CLOCK 5
#define BALANCE_GAIN 128

#endif

#define SERIAL_DEBUG


// filter parameters
const float samplingrate = 89;    // Hz
const float cutoff_frequency = 5; // Hz

HX711 balance;
Butterworth butterworth;
bool new_data = false;
byte i2c_command = 0xFF;
float raw_value;
float filtered_value;
const float devider = 1000;

#define WIRE_SEND_FLOAT(data) Wire.write((uint8_t *)&data, sizeof(data));

void recieved(int count)
{
  //only one address accepted
  if (count != 1)
    return;
  //set the address to what the master sent
  i2c_command = Wire.read();
}

void request()
{
  switch (i2c_command)
  {
  case BALANCE_CMDBALANCE_HAS_NEW_DATA:
    Wire.write(new_data);
    new_data = false;
    break;
  case BALANCE_CMDBALANCE_GET_DATA_RAW:
    WIRE_SEND_FLOAT(raw_value);
    break;
  case BALANCE_CMDBALANCE_GET_DATA:
    WIRE_SEND_FLOAT(filtered_value);
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

void setup()
{
#ifdef SERIAL_DEBUG
  Serial.begin(115200);
  Serial.println("Serial debug enabled");
#endif
  //initialize balance
  balance.begin(BALANCE_PIN_DATA, BALANCE_PIN_CLOCK, BALANCE_GAIN);
  //initialize filter
  butterworth.calculateCoefficients(cutoff_frequency / samplingrate);
  //start i2c communication
  Wire.begin(BALANCE_BOARD_ADDRESS);
  Wire.onReceive(recieved);
  Wire.onRequest(request);
}

void loop()
{
  if (balance.is_ready())
  {
    raw_value = balance.read() / devider;
    filtered_value = butterworth.filter(raw_value);
    new_data = true;
#ifdef SERIAL_DEBUG
    Serial.print(raw_value);
    Serial.print(",");
    Serial.println(filtered_value);
#endif
  }
}