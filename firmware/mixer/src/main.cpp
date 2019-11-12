#include <Arduino.h>
#include "Wire.h"
#include "Shared.h"
#include "WireProtocol.h"

#define PIN_EN A7
#define PIN_MOTOR_1 A0 //PC0
#define PIN_MOTOR_2 A1 //PC1
#define PIN_ENDSTOP_TOP 2
#define PIN_ENDSTOP_BOTTOM 3
#define PIN_MIXER_EN 1
#define PIN_MIXER 0
#define PIN_LED 4

byte movingDirection;
byte targetPosition;
byte oldPosition;

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

void initWire()
{
  //start i2c communication
  Wire.begin(MIXER_BOARD_ADDRESS);
  //disable pullups for i2c
  digitalWrite(SCL, LOW);
  digitalWrite(SDA, LOW);
  Wire.onReceive(recieved);
  Wire.onRequest(handleGetters);
  WireProtocol::blinkAddress(MIXER_BOARD_ADDRESS, PIN_LED);
}

void setup()
{
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_EN, OUTPUT);
  pinMode(PIN_MOTOR_1, OUTPUT);
  pinMode(PIN_MOTOR_2, OUTPUT);
  pinMode(PIN_ENDSTOP_TOP, INPUT);
  pinMode(PIN_ENDSTOP_BOTTOM, INPUT);
  pinMode(PIN_MIXER_EN, OUTPUT);
  pinMode(PIN_MIXER, OUTPUT);
  initWire();
  //disable the driver
  digitalWrite(PIN_MOTOR_1, HIGH);
  digitalWrite(PIN_MOTOR_2, HIGH);
  digitalWrite(PIN_EN, HIGH);
  digitalWrite(PIN_MIXER_EN, LOW);
  oldPosition = MIXER_POSITION_UNDEFINED;
}

void loop()
{
  //do we need to move up or down?
  if (((targetPosition == MIXER_POSITION_TOP) || (targetPosition == MIXER_POSITION_BOTTOM)) && (getPosition() != targetPosition))
  {
    digitalWrite(PIN_MOTOR_1, (targetPosition == MIXER_POSITION_TOP) ? HIGH : LOW);
    digitalWrite(PIN_MOTOR_2, (targetPosition == MIXER_POSITION_TOP) ? LOW : HIGH);
  }
  else
  {
    //target position reached
    //disable output
    digitalWrite(PIN_MOTOR_1, HIGH);
    digitalWrite(PIN_MOTOR_2, HIGH);
    delay(100);
    if (oldPosition != targetPosition)
    {
      oldPosition = targetPosition;
      //reset wire protocol after each stop of the motor
      TWCR = 0; // reset TwoWire Control Register to default, inactive state
      initWire();
    }
  }
}