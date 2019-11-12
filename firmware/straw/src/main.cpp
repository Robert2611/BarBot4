#include <Arduino.h>
#include "Wire.h"
#include "Shared.h"
#include "WireProtocol.h"
#include "Servo.h"

#define PIN_SERVO_STRAW 9
#define PIN_SERVO_SHUTTER 10
#define PIN_MOTOR 7
#define PIN_LED 13
#define PIN_BUTTON 5

#define STATE_IDLE 0
#define STATE_STARTED 1

#define SERVO_STRAW_TAKE 37
#define SERVO_STRAW_DISPENSE 132
#define SERVO_SHUTTER_OPEN 10
#define SERVO_SHUTTER_CLOSED 100

bool error = false;
bool dispensing = false;

Servo servo_straw;
Servo servo_shutter;

byte i2c_command = 0xFF;

void start_dispense()
{
  if (dispensing)
    return;
  error = false;
  dispensing = true;
}

void handleSetters(int parameters_count)
{
  switch (i2c_command)
  {
  case STRAW_CMD_DISPENSE:
    start_dispense();
    break;
  }
}

void handleGetters()
{
  switch (i2c_command)
  {
  case STRAW_CMD_GET_IS_DISPENSING:
    Wire.write(dispensing);
    break;

  case STRAW_CMD_GET_SUCCESSFUL:
    Wire.write(!error);
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
  Wire.begin(STRAW_BOARD_ADRESSS);
  //disable pullups for i2c
  digitalWrite(SCL, LOW);
  digitalWrite(SDA, LOW);
  Wire.onReceive(recieved);
  Wire.onRequest(handleGetters);
  WireProtocol::blinkAddress(STRAW_BOARD_ADRESSS, PIN_LED);
}

void setup()
{
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_BUTTON, INPUT_PULLUP);
  //initialize servos
  servo_shutter.attach(PIN_SERVO_SHUTTER);
  servo_shutter.write(SERVO_SHUTTER_CLOSED);
  servo_straw.attach(PIN_SERVO_STRAW);
  servo_straw.write(SERVO_STRAW_DISPENSE);
  //initialize motor
  pinMode(PIN_MOTOR, OUTPUT);
  digitalWrite(PIN_MOTOR, LOW);
  initWire();
}

void loop()
{
  //wait for i2c command or button press
  while (!dispensing && digitalRead(PIN_BUTTON) == HIGH)
  {
    delay(1);
  }
  dispensing = true;
  servo_straw.write(SERVO_STRAW_TAKE);
  delay(1000);
  servo_shutter.write(SERVO_SHUTTER_OPEN);
  delay(500);
  servo_shutter.write(SERVO_SHUTTER_CLOSED);
  delay(500);
  servo_straw.write(SERVO_STRAW_DISPENSE);
  delay(1000);
  digitalWrite(PIN_MOTOR, HIGH);
  delay(3000);
  digitalWrite(PIN_MOTOR, LOW);
  //TODO: error detection
  error = false;
  dispensing = false;
}