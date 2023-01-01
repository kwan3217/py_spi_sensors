import spidev

from lsm9ds1 import LSM9DS1_AG

def main():
    spi = spidev.SpiDev()
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

    ag = LSM9DS1_AG(spi)
    print(f'Chip ID (should be 0x68): 0x{ag.whoami():02x}')
    ag.begin()
    while True:
        status_g,T,gx,gy,gz,ax,ay,az = ag.query()
        print(f'status_g: 0b{status_g:08b} T: 0x{T:04x} gx: 0x{gx:04x} gy: 0x{gy:04x} gz: 0x{gz:04x} ax: 0x{ax:04x} ay: 0x{ay:04x} az: 0x{az:04x}')


if __name__=="__main__":
    main()