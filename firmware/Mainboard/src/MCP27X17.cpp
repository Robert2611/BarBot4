/*************************************************** 
 This is a library for the MCP23X17 i2c port expander
 These displays use I2C to communicate, 2 pins are required to
 interface
 Adafruit invests time and resources providing this open source code,
 please support Adafruit and open-source hardware by purchasing
 products from Adafruit!
 Written by Limor Fried/Ladyada for Adafruit Industries.
 BSD license, all text above must be included in any redistribution
 ****************************************************/

#include "MCP23X17.h"
#include "Arduino.h"

/**
 * Bit number associated to a give Pin
 */
uint8_t MCP23X17::bitForPin(uint8_t pin)
{
	return pin % 8;
}

/**
 * Register address, port dependent, for a given PIN
 */
uint8_t MCP23X17::regForPin(uint8_t pin, uint8_t portAaddr, uint8_t portBaddr)
{
	return (pin < 8) ? portAaddr : portBaddr;
}

/**
 * Reads a given register
 */
uint8_t MCP23X17::readRegister(uint8_t regAddr)
{
	uint8_t value;
	if (_mode == MCP23X17_MODE_SPI)
	{
		::digitalWrite(_cs_pin, LOW);
		transferSpiAddress(true);
		SPI.transfer(regAddr);
		// Send any byte, the function will return the read value
		value = SPI.transfer(0x00);
		::digitalWrite(_cs_pin, HIGH);
	}
	else
	{
		// read the current GPINTEN
		Wire.beginTransmission(MCP23X17_ADDRESS | _address);
		Wire.write(regAddr);
		Wire.endTransmission();
		Wire.requestFrom(MCP23X17_ADDRESS | _address, 1);
		value = Wire.read();
	}
	return value;
}

/**
 * Writes a given register
 */
void MCP23X17::writeRegister(uint8_t regAddr, uint8_t regValue)
{
	if (_mode == MCP23X17_MODE_SPI)
	{
		::digitalWrite(_cs_pin, LOW);
		transferSpiAddress(true);
		SPI.transfer(regAddr);
		SPI.transfer(regValue);
		::digitalWrite(_cs_pin, HIGH);
	}
	else
	{
		Wire.beginTransmission(MCP23X17_ADDRESS | _address);
		Wire.write(regAddr);
		Wire.write(regValue);
		Wire.endTransmission();
	}
}

/**
 * Helper to update a single bit of an A/B register.
 * - Reads the current register value
 * - Writes the new register value
 */
void MCP23X17::updateRegisterBit(uint8_t pin, uint8_t pValue, uint8_t portAaddr, uint8_t portBaddr)
{
	uint8_t regValue;
	uint8_t regAddr = regForPin(pin, portAaddr, portBaddr);
	uint8_t bit = bitForPin(pin);
	regValue = readRegister(regAddr);

	// set the value for the particular bit
	bitWrite(regValue, bit, pValue);

	writeRegister(regAddr, regValue);
}

////////////////////////////////////////////////////////////////////////////////

/**
 * Initializes the MCP23X17 given its HW selected address, see datasheet for Address selection.
 */
void MCP23X17::beginSPI(uint8_t cs_pin)
{
	beginSPI(cs_pin, 0);
}

void MCP23X17::beginSPI(uint8_t cs_pin, uint8_t adress)
{
	//init the chip select
	_cs_pin = cs_pin;
	::pinMode(_cs_pin, OUTPUT);
	::digitalWrite(_cs_pin, HIGH);

	SPI.begin();

	_mode = MCP23X17_MODE_SPI;
	begin(adress);
}

void MCP23X17::beginWire()
{
	beginWire(0);
}

void MCP23X17::beginWire(uint8_t adress)
{
	Wire.begin();
	_mode = MCP23X17_MODE_WIRE;
	begin(adress);
}

void MCP23X17::begin(uint8_t adress)
{
	_address = constrain(adress, 0, 7);
	// set defaults!
	// all inputs on port A and B
	writeRegister(MCP23X17_IODIRA, 0xff);
	writeRegister(MCP23X17_IODIRB, 0xff);
}

/**
 * Sets the pin mode to either INPUT or OUTPUT
 */
void MCP23X17::pinMode(uint8_t p, uint8_t d)
{
	updateRegisterBit(p, (d == INPUT), MCP23X17_IODIRA, MCP23X17_IODIRB);
}

void MCP23X17::transferSpiAddress(bool write)
{
	SPI.transfer(((MCP23X17_ADDRESS | _address << 1)) | write);
}

/**
 * Reads all 16 pins (port A and B) into a single 16 bits variable.
 */
uint16_t MCP23X17::readWord(uint8_t regAddr)
{
	uint16_t res = 0;
	if (_mode == MCP23X17_MODE_SPI)
	{
		::digitalWrite(_cs_pin, LOW);
		transferSpiAddress(false);
		SPI.transfer(MCP23X17_GPIOA);
		res = SPI.transfer(0x00) << 8;
		res += SPI.transfer(0x00);
		::digitalWrite(_cs_pin, HIGH);
	}
	else
	{
		Wire.beginTransmission(MCP23X17_ADDRESS | _address);
		Wire.write(regAddr);
		Wire.endTransmission();
		Wire.requestFrom(MCP23X17_ADDRESS | _address, 2);
		res = Wire.read() << 8;
		res += Wire.read();
	}
	return res;
}

void MCP23X17::writeWord(uint8_t regAddr, uint16_t regValue)
{
	if (_mode == MCP23X17_MODE_SPI)
	{
		::digitalWrite(_cs_pin, LOW);
		transferSpiAddress(true);
		SPI.transfer(regAddr);
		SPI.transfer((byte)(regValue >> 8));
		SPI.transfer((byte)(regValue & 0xFF));
		::digitalWrite(_cs_pin, HIGH);
	}
	else
	{
		Wire.beginTransmission(MCP23X17_ADDRESS | _address);
		Wire.write(regAddr);
		Wire.write((byte)(regValue >> 8));
		Wire.write((byte)(regValue & 0xFF));
		Wire.endTransmission();
	}
}

uint16_t MCP23X17::readGPIOAB()
{
	return readWord(MCP23X17_GPIOA);
}

uint16_t MCP23X17::readGPIOBA()
{
	uint16_t ab = readGPIOAB();
	//swap bytes
	return ((ab & 0xFF) << 8) | (ab >> 8);
}

uint8_t MCP23X17::readGPIOA()
{
	return readRegister(MCP23X17_GPIOA);
}

uint8_t MCP23X17::readGPIOB()
{
	return readRegister(MCP23X17_GPIOB);
}

/**
 * Writes all the pins in one go. This method is very useful if you are implementing a multiplexed matrix and want to get a decent refresh rate.
 */
void MCP23X17::writeGPIOAB(uint16_t ab)
{
	writeWord(MCP23X17_GPIOA, ab);
}

void MCP23X17::writeGPIOBA(uint16_t ba)
{
	//swap bytes
	uint16_t ab = ((ba & 0xFF) << 8) | (ba >> 8);
	writeGPIOAB(ab);
}

void MCP23X17::digitalWrite(uint8_t pin, uint8_t d)
{
	uint8_t gpio;
	uint8_t bit = bitForPin(pin);

	// read the current GPIO output latches
	uint8_t regAddr = regForPin(pin, MCP23X17_OLATA, MCP23X17_OLATB);
	gpio = readRegister(regAddr);

	// set the pin and direction
	bitWrite(gpio, bit, d);

	// write the new GPIO
	regAddr = regForPin(pin, MCP23X17_GPIOA, MCP23X17_GPIOB);
	writeRegister(regAddr, gpio);
}

void MCP23X17::pullUp(uint8_t p, uint8_t d)
{
	updateRegisterBit(p, d, MCP23X17_GPPUA, MCP23X17_GPPUB);
}

uint8_t MCP23X17::digitalRead(uint8_t pin)
{
	uint8_t bit = bitForPin(pin);
	uint8_t regAddr = regForPin(pin, MCP23X17_GPIOA, MCP23X17_GPIOB);
	return (readRegister(regAddr) >> bit) & 0x1;
}

/**
 * Configures the interrupt system. both port A and B are assigned the same configuration.
 * Mirroring will OR both INTA and INTB pins.
 * Opendrain will set the INT pin to value or open drain.
 * polarity will set LOW or HIGH on interrupt.
 * Default values after Power On Reset are: (false, false, LOW)
 * If you are connecting the INTA/B pin to arduino 2/3, you should configure the interupt handling as FALLING with
 * the default configuration.
 */
void MCP23X17::setupInterrupts(uint8_t mirroring, uint8_t openDrain, uint8_t polarity)
{
	// configure the port A
	uint8_t ioconfValue = readRegister(MCP23X17_IOCONA);
	bitWrite(ioconfValue, 6, mirroring);
	bitWrite(ioconfValue, 2, openDrain);
	bitWrite(ioconfValue, 1, polarity);
	writeRegister(MCP23X17_IOCONA, ioconfValue);

	// Configure the port B
	ioconfValue = readRegister(MCP23X17_IOCONB);
	bitWrite(ioconfValue, 6, mirroring);
	bitWrite(ioconfValue, 2, openDrain);
	bitWrite(ioconfValue, 1, polarity);
	writeRegister(MCP23X17_IOCONB, ioconfValue);
}

/**
 * Set's up a pin for interrupt. uses arduino MODEs: CHANGE, FALLING, RISING.
 *
 * Note that the interrupt condition finishes when you read the information about the port / value
 * that caused the interrupt or you read the port itself. Check the datasheet can be confusing.
 *
 */
void MCP23X17::setupInterruptPin(uint8_t pin, uint8_t mode)
{

	// set the pin interrupt control (0 means change, 1 means compare against given value);
	updateRegisterBit(pin, (mode != CHANGE), MCP23X17_INTCONA, MCP23X17_INTCONB);
	// if the mode is not CHANGE, we need to set up a default value, different value triggers interrupt

	// In a RISING interrupt the default value is 0, interrupt is triggered when the pin goes to 1.
	// In a FALLING interrupt the default value is 1, interrupt is triggered when pin goes to 0.
	updateRegisterBit(pin, (mode == FALLING), MCP23X17_DEFVALA, MCP23X17_DEFVALB);

	// enable the pin for interrupt
	updateRegisterBit(pin, HIGH, MCP23X17_GPINTENA, MCP23X17_GPINTENB);
}

uint8_t MCP23X17::getLastInterruptPin()
{
	uint8_t intf;

	// try port A
	intf = readRegister(MCP23X17_INTFA);
	for (int i = 0; i < 8; i++)
		if (bitRead(intf, i))
			return i;

	// try port B
	intf = readRegister(MCP23X17_INTFB);
	for (int i = 0; i < 8; i++)
		if (bitRead(intf, i))
			return i + 8;

	return MCP23X17_INT_ERR;
}
uint8_t MCP23X17::getLastInterruptPinValue()
{
	uint8_t intPin = getLastInterruptPin();
	if (intPin != MCP23X17_INT_ERR)
	{
		uint8_t intcapreg = regForPin(intPin, MCP23X17_INTCAPA, MCP23X17_INTCAPB);
		uint8_t bit = bitForPin(intPin);
		return (readRegister(intcapreg) >> bit) & (0x01);
	}

	return MCP23X17_INT_ERR;
}