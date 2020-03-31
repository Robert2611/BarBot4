#include <Arduino.h>
#include "Wire.h"
#include "Shared.h"
#include "WireProtocol.h"

#define PIN_EN 3
#define PIN_R_PWM 5
#define PIN_L_PWM 6
#define PIN_LED 13

#define CRUSHING_MAX_TIME 5000

byte i2c_command = 0xFF;

byte error;
bool crushing;
unsigned long crushing_start_time;

void handleSetters(int parameters_count)
{
#ifdef SERIAL_DEBUG
  Serial.print("SET");
  Serial.println(i2c_command);
#endif
  switch (i2c_command)
  {
  case CRUSHER_CMD_START_CRUSHING:
    break;
  case CRUSHER_CMD_STOP_CRUSHING:
    break;
  }
}

void handleGetters()
{
#ifdef SERIAL_DEBUG
  Serial.print("GET");
  Serial.println(i2c_command);
#endif
  switch (i2c_command)
  {

  case CRUSHER_CMD_GET_ERROR:
    Wire.write(error);
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

void initWire()
{
  //start i2c communication
  Wire.begin(CRUSHER_BOARD_ADDRESS);
  //disable pullups for i2c
  digitalWrite(SCL, LOW);
  digitalWrite(SDA, LOW);
  Wire.onReceive(recieved);
  Wire.onRequest(handleGetters);
  WireProtocol::blinkAddress(CRUSHER_BOARD_ADDRESS, PIN_LED);
}

void startCrushing()
{
  if (crushing)
    return;
  error = CRUSHER_ERROR_NO_ERROR;
  crushing = true;
  crushing_start_time = millis();
  analogWrite(PIN_EN, 255);
}

void stopChrushing()
{
  digitalWrite(PIN_EN, LOW);
}

void setup()
{
#ifdef SERIAL_DEBUG
  Serial.begin(115200);
#endif
  pinMode(PIN_EN, OUTPUT);
  pinMode(PIN_R_PWM, OUTPUT);
  pinMode(PIN_L_PWM, OUTPUT);
  initWire();
#ifdef SERIAL_DEBUG
  Serial.println("Crusher board initialised");
#endif
  digitalWrite(PIN_EN, LOW);
  digitalWrite(PIN_R_PWM, LOW);
  digitalWrite(PIN_L_PWM, HIGH);
}

void loop()
{
  //timeout
  if (crushing && millis() - crushing_start_time > CRUSHING_MAX_TIME)
  {
    error = CRUSHER_ERROR_TIMEOUT;
    crushing = false;
  }
}