#!/usr/bin/python

import spidev

from bits import extract_uint16_le, extract_int16_le


class SPI_sensor:
    """
    Superclass for SPI sensors using the common de-facto SPI protocol:
    * Transaction defined by lowering/raising ~CS
    * First byte sent to the sensor in a transaction represents
      the read/~write command (bit 7) and the register (0x00-0x7F)
      to access
    * Subsequent bytes are sensor access. SPI is full duplex, but
      this protocol is half-duplex. To write, just send the data
      to go to the sensor, which will send back garbage. Many
      sensors have a register auto-increment so sending multiple
      bytes will do what you think. To read, send garbage to the sensor
      and it will send back the data from the register. Again, the
      register auto-increment may be in place. When all bytes are sent,
      the transaction is over and ~CS can be raised.

    Register auto-increment is a property of the sensor, not this protocol.
    """
    def __init__(self,spi:spidev.SpiDev):
        """

        :param spi: Reference to SPI device to use. Set the speed
                    etc outside of this module.

        """
        self.spi=spi
    def read_reg(self,reg_addr:int,count:int=1)->[bytes,int]:
        result = self.spi.xfer([reg_addr | 0x80] + [0] * (count))[1:]
        if count == 1:
            return result[0]
        else:
            return result
    def write_reg(self,reg_addr:int,values:[bytes,int])->None:
        if type(values)==int:
            values=bytes([values])
        self.spi.xfer(bytes([reg_addr & 0x7f])+values)
    def read_uint16(self,reg_addr:int)->int:
        result=self.read_reg(reg_addr,2)
        return extract_uint16_le(result)
    def read_int16(self,reg_addr:int)->int:
        return extract_int16_le(self.read_reg(reg_addr,2))
    def read_int8(self,reg_addr:int)->int:
        result=self.read_reg(reg_addr)
        if result>0x80:
            result-=0x1_00
        return result

