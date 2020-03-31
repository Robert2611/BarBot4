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

uint8_t MCP23X17::regForPin(uint8_t pin, uint8_t portAaddr, uint8_t portBaddr)
{
	return (pin < 8) ? portAaddr : portBaddr;
}

uint8_t MCP23X17::readRegister(uint8_t regAddr)
{
	uint8_t value;
	if (_mode == MCP23X17_MODE_SPI)
	{
		::digitalWrite(_cs_pin, LOW);
		transferSpiAddress(true);
		_spi->transfer(regAddr);
		// Send any byte, the function will return the read value
		value = _spi->transfer(0xFF);
		::digitalWrite(_cs_pin, HIGH);
	}
	else
	{
		// read the current GPINTEN
		_i2c->beginTransmission(MCP23X17_ADDRESS | _address);
		_i2c->write(regAddr);
		_i2c->endTransmission();
		_i2c->requestFrom(MCP23X17_ADDRESS | _address, 1);
		value = _i2c->read();
	}
	return value;
}

void MCP23X17::writeRegister(uint8_t regAddr, uint8_t regValue)
{
	if (_mode == MCP23X17_MODE_SPI)
	{
		::digitalWrite(_cs_pin, LOW);
		transferSpiAddress(false);
		_spi->transfer(regAddr);
		_spi->transfer(regValue);
		::digitalWrite(_cs_pin, HIGH);
	}
	else
	{
		_i2c->beginTransmission(MCP23X17_ADDRESS | _address);
		_i2c->write(regAddr);
		_i2c->write(regValue);
		_i2c->endTransmission();
	}
}

void MCP23X17::updateRegisterBit(uint8_t pin, uint8_t pValue, uint8_t portAaddr, uint8_t portBaddr)
{
	uint8_t regValue;
	uint8_t regAddr = regForPin(pin, portAaddr, portBaddr);
	regValue = readRegister(regAddr);

	// set the value for the particular bit
	bitWrite(regValue, pin % 8, pValue);

	writeRegister(regAddr, regValue);
}

uint16_t MCP23X17::readWord(uint8_t regAddr)
{
	uint16_t res = 0;
	if (_mode == MCP23X17_MODE_SPI)
	{
		::digitalWrite(_cs_pin, LOW);
		transferSpiAddress(true);
		_spi->transfer(MCP23X17_GPIOA);
		res = _spi->transfer(0x00) << 8;
		res += _spi->transfer(0x00);
		::digitalWrite(_cs_pin, HIGH);
	}
	else
	{
		_i2c->beginTransmission(MCP23X17_ADDRESS | _address);
		_i2c->write(regAddr);
		_i2c->endTransmission();
		_i2c->requestFrom(MCP23X17_ADDRESS | _address, 2);
		res = _i2c->read() << 8;
		res += _i2c->read();
	}
	return res;
}

void MCP23X17::writeWord(uint8_t regAddr, uint16_t regValue)
{
	if (_mode == MCP23X17_MODE_SPI)
	{
		::digitalWrite(_cs_pin, LOW);
		transferSpiAddress(false);
		_spi->transfer(regAddr);
		_spi->transfer((byte)(regValue >> 8));
		_spi->transfer((byte)(regValue & 0xFF));
		::digitalWrite(_cs_pin, HIGH);
	}
	else
	{
		_i2c->beginTransmission(MCP23X17_ADDRESS | _address);
		_i2c->write(regAddr);
		_i2c->write((byte)(regValue >> 8));
		_i2c->write((byte)(regValue & 0xFF));
		_i2c->endTransmission();
	}
}

MCP23X17::MCP23X17(uint8_t cs_pin, SPIClass *spi) : MCP23X17(cs_pin, spi, 0)
{
}

MCP23X17::MCP23X17(uint8_t cs_pin, SPIClass *spi, uint8_t adress)
{
	//init the chip select
	_cs_pin = cs_pin;
	_spi = spi;
	_address = constrain(adress, 0, 7);
	_mode = MCP23X17_MODE_SPI;
}

MCP23X17::MCP23X17(TwoWire *i2c) : MCP23X17(i2c, 0)
{
}

MCP23X17::MCP23X17(TwoWire *i2c, uint8_t adress)
{
	_i2c = i2c;
	_mode = MCP23X17_MODE_WIRE;
	_address = constrain(adress, 0, 7);
}

void MCP23X17::begin()
{
	if (_mode == MCP23X17_MODE_SPI)
	{
		::pinMode(_cs_pin, OUTPUT);
		::digitalWrite(_cs_pin, HIGH);
	}
}

void MCP23X17::transferSpiAddress(bool read)
{
	uint8_t read_write = read ? 1 : 0;
	_spi->transfer(((MCP23X17_ADDRESS | _address << 1)) | read_write);
}
