#include <Arduino.h>
#include "Wire.h"
#include "Shared.h"
#include "WireProtocol.h"

#define PIN_EN A7            //ADC7
#define PIN_MOTOR_1 A0       //PC0
#define PIN_MOTOR_2 A1       //PC1
#define PIN_ENDSTOP_TOP 2    //PD2
#define PIN_ENDSTOP_BOTTOM 3 //PD3
#define PIN_MIXER_EN 1       //PD1
#define PIN_MIXER 0          //PD0
#define PIN_LED 4            //PD4
#define PIN_BUTTON 10        //PB2
//not used but still on the PCB
#define PIN_SERVO_1 5 //PD5
#define PIN_SREVO_2 6 //PD6

#define MIXING_MIN_TIME 500      // avoid very short...
#define MIXING_MAX_TIME 5000     // ... and very long mixes
#define MIXING_MOVE_TIMEOUT 3000 //no success if move takes too long
#define MIXING_DEFAULT_TIME 2000 //will be used if no time is set

byte i2c_command = 0xFF;

bool do_mixing;
bool error;
long mixing_time = 1000;

void startMixing(long _mixing_time)
{
  if (do_mixing)
    return;
  error = false;
  do_mixing = true;
  mixing_time = constrain(_mixing_time, MIXING_MIN_TIME, MIXING_MAX_TIME);
  digitalWrite(PIN_LED, HIGH);
}

void stopMixing(bool _error)
{
  error = _error;
  do_mixing = false;
  digitalWrite(PIN_LED, LOW);
}

void handleSetters(int parameters_count)
{
#ifdef SERIAL_DEBUG
  Serial.print("SET");
  Serial.println(i2c_command);
#endif
  switch (i2c_command)
  {
  case MIXER_CMD_START_MIXING:
    if (parameters_count == 0)
    {
      startMixing(MIXING_DEFAULT_TIME);
    }
    else if (parameters_count == 1)
    {
      byte time_in_seconds = Wire.read();
      startMixing((unsigned long)time_in_seconds * 1000);
    }
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
  case WIREPROTOCOL_CMD_PING:
    Wire.write(MIXER_BOARD_ADDRESS);
    break;
  case MIXER_CMD_GET_IS_MIXING:
    Wire.write(do_mixing);
    break;

  case MIXER_CMD_GET_SUCCESSFUL:
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
#ifdef SERIAL_DEBUG
  Serial.begin(115200);
#endif
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_EN, OUTPUT);
  pinMode(PIN_MOTOR_1, OUTPUT);
  pinMode(PIN_MOTOR_2, OUTPUT);
  pinMode(PIN_ENDSTOP_TOP, INPUT);
  pinMode(PIN_ENDSTOP_BOTTOM, INPUT);
  pinMode(PIN_MIXER_EN, OUTPUT);
  pinMode(PIN_MIXER, OUTPUT);
  pinMode(PIN_BUTTON, INPUT_PULLUP);
  //disable the driver
  digitalWrite(PIN_MOTOR_1, HIGH);
  digitalWrite(PIN_MOTOR_2, HIGH);
  digitalWrite(PIN_EN, HIGH);
  digitalWrite(PIN_MIXER_EN, LOW);
  initWire();
#ifdef SERIAL_DEBUG
  Serial.println("Mixer board initialised");
#endif
}

bool isAtTop()
{
  return !digitalRead(PIN_ENDSTOP_TOP) && !digitalRead(PIN_ENDSTOP_TOP);
}

bool isAtBottom()
{
  return !digitalRead(PIN_ENDSTOP_BOTTOM) && !digitalRead(PIN_ENDSTOP_BOTTOM);
}

void startMotor(bool up)
{
  digitalWrite(PIN_MOTOR_1, up ? HIGH : LOW);
  digitalWrite(PIN_MOTOR_2, up ? LOW : HIGH);
}

void stopMotor()
{
  digitalWrite(PIN_MOTOR_1, HIGH);
  digitalWrite(PIN_MOTOR_2, HIGH);
}

void toggleMixer(bool on)
{
  digitalWrite(PIN_MIXER, HIGH);
  digitalWrite(PIN_MIXER_EN, on ? HIGH : LOW);
}

void loop()
{
  //wait for i2c command or button press, stay in top position
  while (!do_mixing && digitalRead(PIN_BUTTON) == HIGH)
  {
    if (!isAtTop())
      startMotor(true);
    else
      stopMotor();
    delay(1);
  }
  if (!do_mixing)
    startMixing(MIXING_DEFAULT_TIME);

  //move down
  startMotor(false);
  unsigned long before_move = millis();
  while (!isAtBottom())
  {
    if (millis() > before_move + MIXING_MOVE_TIMEOUT)
    {
      //TIMEOUT,
      stopMixing(true);
      return;
    }
    delay(1);
  }

  stopMotor();

  //mix
  toggleMixer(true);
  delay(mixing_time);
  toggleMixer(false);

  //move up
  startMotor(true);

  before_move = millis();
  while (!isAtTop())
  {
    if (millis() > before_move + MIXING_MOVE_TIMEOUT)
    {
      //TIMEOUT,
      stopMixing(true);
      return;
    }
    delay(1);
  }

  stopMixing(false);
}