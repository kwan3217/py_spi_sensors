"""
Use the sensor drivers to read the BME680 and LSM9DS1 sensors
"""

from spidev import SpiDev
from chip_select import ChipSelect
from bme680 import BME680
from lsm9ds1 import LSM9DS1_AG


def main():
    cs= ChipSelect()
    cs.begin()
    spi = SpiDev()
    spi.open(0, 0)
    # Allowed SPI from table at https://www.takaitra.com/spi-device-raspberry-pi/
    allowed_spi_spd = [125_000_000,
                       62_500_000,
                       31_200_000,
                       15_600_000,
                       7_800_000,
                       3_900_000,
                       1_953_000,
                       976_000,
                       488_000,
                       244_000,
                       122_000,
                       61_000,
                       30_500,
                       15_200,
                       7_629]

    spi.max_speed_hz = 3_900_000
    spi.mode = 0b00
    cs.set_addr(2)
    bme = BME680(spi)
    print(f'Chip ID (should be 0x61): 0x{bme.whoami():02x}')
    bme.begin()
    ag = LSM9DS1_AG(spi)
    cs.set_addr(0)
    print(f'Chip ID (should be 0x68): 0x{ag.whoami():02x}')
    ag.begin()
    while True:
        cs.set_addr(2)
        print(bme.wait_ready())
        rP, P, dP, rT, T, dT, rh, h, dh = bme.query()
        print(
            f'P: raw {rP:6d}, cal {P:.1f}  Pa, d {dP:.4e}Pa    T: raw {rT:6d}, cal {T:.4f}degC, d {dT:.4e}degC    h: raw {rh:6d}, cal {h:.3f}    %, d {dh:.4e}%')
        cs.set_addr(0)
        status_g,T,gx,gy,gz,ax,ay,az = ag.query()
        print(f'status_g: 0b{status_g:08b} T: {T:6d} gx: {gx:6d} gy: {gy:6d} gz: {gz:6d} ax: {ax:6d} ay: {ay:6d} az: {az:6d}')

if __name__=="__main__":
    main()