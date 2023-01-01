"""
Use a 74x138 chip to control multiple SPI devices with a single chip enable line, plus
a few GPIO lines. Test target is [Nexperia 74LVC138APW](https://www.mouser.com/ProductDetail/771-74LVC138APW-T)
in a TSSOP16 package. See that page for ordering and datasheet details.

The Raspberry Pi 4B has a hardware SPI port with two dedicated chip select lines, ~CE0
and ~CE1. This is fine, until you need to control more than two devices. So, we use
a 3-to-8 decoder to repurpose three GPIO lines to control up to 8 SPI devices.

The 74x138 is the ideal decoder for this purpose -- it almost seems as if it was designed
for it. It has 8 output lines that are normally high, three input lines which controls
which of the 8 is low, and a set of enable lines that control if *any* of the lines are
low. We can program the enable port such that it only activates (lowers) one of the
output lines if the input enable is low, and then we can plug the Pi's ~CE0 into that
enable.

The flow is then as follows:
* Use this module to program the address of the device to enable
* Use the normal SpiDev driver to handle CE0
"""

import RPi.GPIO as GPIO

class ChipSelect:
    def __init__(self,pin0:int=15,pin1:int=13,pin2:int=11):
        self.pins=(pin0,pin1,pin2)
    def begin(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pins,GPIO.OUT,initial=GPIO.HIGH)
    def end(self):
        GPIO.cleanup()
    def set_addr(self,addr:int):
        out=(GPIO.HIGH if ((addr >> 0) & 0x01)==0x01 else GPIO.LOW,
                     GPIO.HIGH if ((addr >> 1) & 0x01)==0x01 else GPIO.LOW,
                     GPIO.HIGH if ((addr >> 2) & 0x01)==0x01 else GPIO.LOW,
                     )
        GPIO.output(self.pins,out)

def main():
    import time
    cs=ChipSelect()
    cs.begin()
    for i in range(8):
        cs.set_addr(i)
        time.sleep(1)


if __name__=="__main__":
    main()
