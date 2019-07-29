#include <Arduino.h>
#include "Wire.h"
#include "Shared.h"
#include "WireProtocol.h"

#define PIN_EN 2
#define PIN_MOTOR_1 3
#define PIN_MOTOR_2 4
#define PIN_ENDSTOP_TOP 5
#define PIN_ENDSTOP_BOTTOM 6
#define PIN_MIXER_EN 7
#define PIN_MIXER 8

byte movingDirection;
byte targetPosition;

byte i2c_command = 0xFF;

byte getPosition()
{
  bool top = !digitalRead(PIN_ENDSTOP_TOP) && !digitalRead(PIN_ENDSTOP_TOP);
  bool bottom = !digitalRead(PIN_ENDSTOP_BOTTOM) && !digitalRead(PIN_ENDSTOP_BOTTOM);
  if (top && !bottom)
    return MIXER_POSITION_TOP;
  else if (bottom && !top)
    return MIXER_POSITION_BOTTOM;
  else
    return MIXER_POSITION_UNDEFINED;
}

void setMixer(bool mix)
{
  digitalWrite(PIN_MIXER, HIGH);
  digitalWrite(PIN_MIXER_EN, mix ? HIGH : LOW);
}

void handleSetters(int parameters_count)
{
  switch (i2c_command)
  {
  case MIXER_CMD_SET_TARGET_POS:
    if (parameters_count != 1)
      break;
    byte data;
    data = Wire.read();
    targetPosition = data;
    break;
  case MIXER_CMD_MIX_ON:
    setMixer(true);
    break;
  case MIXER_CMD_MIX_OFF:
    setMixer(false);
    break;
  }
}

void handleGetters()
{
  switch (i2c_command)
  {
  case MIXER_CMD_GET_POS:
    Wire.write(getPosition());
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
  pinMode(PIN_EN, OUTPUT);
  pinMode(PIN_MOTOR_1, OUTPUT);
  pinMode(PIN_MOTOR_2, OUTPUT);
  pinMode(PIN_ENDSTOP_TOP, INPUT_PULLUP);
  pinMode(PIN_ENDSTOP_BOTTOM, INPUT_PULLUP);
  pinMode(PIN_MIXER_EN, OUTPUT);
  pinMode(PIN_MIXER, OUTPUT);

  //start i2c communication
  Wire.begin(MIXER_BOARD_ADDRESS);
  //disable pullups for i2c
  digitalWrite(SCL, LOW);
  digitalWrite(SDA, LOW);
  Wire.onReceive(recieved);
  Wire.onRequest(handleGetters);

  //disable the driver
  digitalWrite(PIN_EN, LOW);
  digitalWrite(PIN_MIXER_EN, LOW);
}

void loop()
{
  //do we need to move up or down?
  if (((targetPosition == MIXER_POSITION_TOP) || (targetPosition == MIXER_POSITION_BOTTOM)) && (getPosition() != targetPosition))
  {
    digitalWrite(PIN_MOTOR_1, (targetPosition == MIXER_POSITION_TOP) ? HIGH : LOW);
    digitalWrite(PIN_MOTOR_2, (targetPosition == MIXER_POSITION_TOP) ? LOW : HIGH);
    digitalWrite(PIN_EN, HIGH);
  }
  else
  {
    //disable output
    digitalWrite(PIN_EN, LOW);
  }
}