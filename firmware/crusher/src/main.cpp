#include <Arduino.h>
#include "Wire.h"
#include "Shared.h"
#include "WireProtocol.h"

#define SERIAL_DEBUG
#define PIN_PWM 6
#define PIN_LED 13
#define PIN_COVER_SWITCH 3

#define CRUSHING_MAX_TIME 30000

byte i2c_command = 0xFF;

byte error;
bool crushing;
unsigned long crushing_start_time;

void startCrushing()
{
  if (crushing)
    return;
  error = CRUSHER_ERROR_NO_ERROR;
  crushing = true;
  crushing_start_time = millis();
  analogWrite(PIN_PWM, 255);
}

void stopChrushing()
{
  crushing = false;
  digitalWrite(PIN_PWM, LOW);
}

void handleSetters(int parameters_count)
{
#ifdef SERIAL_DEBUG
  Serial.print("SET: ");
  Serial.println(i2c_command);
#endif
  switch (i2c_command)
  {
  case CRUSHER_CMD_START_CRUSHING:
    startCrushing();
    break;
  case CRUSHER_CMD_STOP_CRUSHING:
    stopChrushing();
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
    Wire.write(CRUSHER_BOARD_ADDRESS);
    break;
  case CRUSHER_CMD_GET_ERROR:
    Wire.write(error);
#ifdef SERIAL_DEBUG
    Serial.print("Error requested, returned: ");
    Serial.println(error);
#endif
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

void setup()
{
  Serial.begin(115200);
#ifdef SERIAL_DEBUG
  Serial.begin(115200);
#endif
  pinMode(PIN_PWM, OUTPUT);
  pinMode(PIN_COVER_SWITCH, INPUT);
  initWire();
#ifdef SERIAL_DEBUG
  Serial.println("Crusher board initialised");
#endif
  digitalWrite(PIN_PWM, LOW);
}

void loop()
{
  if (Serial.available())
  {
    String input = Serial.readString();
    String command = input.substring(0, 1);
    command.toLowerCase();
    String parameter;

    if (input.length() > 2)
    {
      parameter = input.substring(2);
    }

    if (command == "p")
    {
      Serial.print("PWM->");
      Serial.println(parameter.toInt());
      analogWrite(PIN_PWM, parameter.toInt());
    }
  }
  if (crushing)
  {
    //timeout
    if (millis() - crushing_start_time > CRUSHING_MAX_TIME)
    {
      error = CRUSHER_ERROR_TIMEOUT;
      stopChrushing();
#ifdef SERIAL_DEBUG
      Serial.println("Error: timeout");
#endif
    }
    if (!digitalRead(PIN_COVER_SWITCH))
    {
      error = CRUSHER_ERROR_COVER_OPEN;
      stopChrushing();
#ifdef SERIAL_DEBUG
      Serial.println("Error: cover open");
#endif
    }
  }
}