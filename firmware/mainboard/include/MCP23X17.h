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

#ifndef MCP23X17_H_
#define MCP23X17_H_

#include <SPI.h>
#include <Wire.h>

class MCP23X17
{
public:
    MCP23X17(uint8_t cs_pin, SPIClass *spi);
    MCP23X17(uint8_t cs_pin, SPIClass *spi, uint8_t adress);

    MCP23X17(TwoWire *i2c);
    MCP23X17(TwoWire *i2c, uint8_t adress);

    void begin();

    uint8_t readRegister(uint8_t addr);
    void writeRegister(uint8_t addr, uint8_t value);

private:
    uint8_t _mode;
    uint8_t _cs_pin;
    uint8_t _address;
    SPIClass *_spi;
    TwoWire *_i2c;

    uint16_t readWord(uint8_t addr);
    void writeWord(uint8_t addr, uint16_t value);

    uint8_t bitForPin(uint8_t pin);
    uint8_t regForPin(uint8_t pin, uint8_t portAaddr, uint8_t portBaddr);

    void transferSpiAddress(bool write);

    /**
   * Utility private method to update a register associated with a pin (whether port A/B)
   * reads its value, updates the particular bit, and writes its value.
   */
    void updateRegisterBit(uint8_t p, uint8_t pValue, uint8_t portAaddr, uint8_t portBaddr);
};

#define MCP23X17_ADDRESS 0x40

#define MCP23X17_MODE_SPI 0
#define MCP23X17_MODE_WIRE 1

// registers
#define MCP23X17_IODIRA 0x00
#define MCP23X17_IPOLA 0x02
#define MCP23X17_GPINTENA 0x04
#define MCP23X17_DEFVALA 0x06
#define MCP23X17_INTCONA 0x08
#define MCP23X17_IOCONA 0x0A
#define MCP23X17_GPPUA 0x0C
#define MCP23X17_INTFA 0x0E
#define MCP23X17_INTCAPA 0x10
#define MCP23X17_GPIOA 0x12
#define MCP23X17_OLATA 0x14

#define MCP23X17_IODIRB 0x01
#define MCP23X17_IPOLB 0x03
#define MCP23X17_GPINTENB 0x05
#define MCP23X17_DEFVALB 0x07
#define MCP23X17_INTCONB 0x09
#define MCP23X17_IOCONB 0x0B
#define MCP23X17_GPPUB 0x0D
#define MCP23X17_INTFB 0x0F
#define MCP23X17_INTCAPB 0x11
#define MCP23X17_GPIOB 0x13
#define MCP23X17_OLATB 0x15

#define MCP23X17_INT_ERR 255

#endif