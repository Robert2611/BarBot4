#include <Arduino.h>
#include "Wire.h"
#include "Shared.h"
#include "WireProtocol.h"
#include "Servo.h"

#define SERIAL_DEBUG
#define PIN_SERVO 9
#define PIN_LED 13

#define SERVO_CLOSED 115
#define SERVO_OPEN 0

#define DISPENSING_MAX_TIME 30000

byte i2c_command = 0xFF;

byte error;
bool dispensing;
unsigned long dispense_start_time;

Servo servo;

void startDispensing()
{
  if (dispensing)
    return;
  error = SUGAR_ERROR_NO_ERROR;
  dispensing = true;
  dispense_start_time = millis();
  servo.write(SERVO_OPEN);
}

void stopDispensing()
{
  dispensing = false;
  servo.write(SERVO_CLOSED);
}

void handleSetters(int parameters_count)
{
#ifdef SERIAL_DEBUG
  Serial.print("SET: ");
  Serial.println(i2c_command);
#endif
  switch (i2c_command)
  {
  case SUGAR_CMD_START_DISPENSING:
    startDispensing();
    break;
  case SUGAR_CMD_STOP_DISPENSING:
    stopDispensing();
    break;
  }
}

void handleGetters()
{
#ifdef SERIAL_DEBUG
  Serial.print("GET: ");
  Serial.println(i2c_command);
#endif
  switch (i2c_command)
  {
  case WIREPROTOCOL_CMD_PING:
    Wire.write(SUGAR_BOARD_ADDRESS);
    break;
  case SUGAR_CMD_GET_ERROR:
    Wire.write(error);
#ifdef SERIAL_DEBUG
    Serial.print("Error requested, returned: ");
    Serial.println(error);
#endif
    break;

  // no command byte set or unknown command
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
  // continue only if command byte was set
  if (count < 1)
    return;
  // save the command byte
  i2c_command = Wire.read();
  // handle messages that are only setters
  handleSetters(count - 1);
}

void initWire()
{
  // start i2c communication
  Wire.begin(SUGAR_BOARD_ADDRESS);
  // disable pullups for i2c
  digitalWrite(SCL, LOW);
  digitalWrite(SDA, LOW);
  Wire.onReceive(recieved);
  Wire.onRequest(handleGetters);
  WireProtocol::blinkAddress(SUGAR_BOARD_ADDRESS, PIN_LED);
}

void setup()
{
  Serial.begin(115200);
#ifdef SERIAL_DEBUG
  Serial.begin(115200);
#endif
  initWire();
#ifdef SERIAL_DEBUG
  Serial.println("Sugar board initialised");
#endif
  servo.attach(PIN_SERVO);
  servo.write(SERVO_CLOSED);
}

void loop()
{
#ifdef SERIAL_DEBUG
  if (Serial.available())
  {
    String input = Serial.readString();
    if (dispensing)
      stopDispensing();
    else
      startDispensing();
  }
#endif
  if (dispensing)
  {
    // timeout
    if (millis() - dispense_start_time > DISPENSING_MAX_TIME)
    {
      error = SUGAR_ERROR_TIMEOUT;
      stopDispensing();
#ifdef SERIAL_DEBUG
      Serial.println("Error: timeout");
#endif
    }
  }
}