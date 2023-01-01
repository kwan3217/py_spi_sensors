"""
LSM9DS1 sensor. Since this has two independent SPI interfaces with two
~CS lines, treat it as two different sensors.
"""
from typing import Sequence

from bits import extract_int16_le, extract_uint16_le, extract_uint16_be
from spi_sensor import SPI_sensor

class LSM9DS1_AG(SPI_sensor):
    WHO_AM_I     =0x0F
    CTRL_REG1_G  =0x10
    CTRL_REG2_G  =0x11
    CTRL_REG3_G  =0x12
    OUT_TEMP_L   =0x15
    OUT_TEMP_H   =0x16
    STATUS_REG_G =0x17
    OUT_X_L_G    =0x18
    OUT_X_H_G    =0x19
    OUT_Y_L_G    =0x1A
    OUT_Y_H_G    =0x1B
    OUT_Z_L_G    =0x1C
    OUT_Z_H_G    =0x1D
    CTRL_REG4    =0x1E
    CTRL_REG5_XL =0x1F
    CTRL_REG6_XL =0x20
    CTRL_REG8    =0x22
    STATUS_REG_XL=0x27
    OUT_X_L_XL   =0x28
    OUT_X_H_XL   =0x29
    OUT_Y_L_XL   =0x2A
    OUT_Y_H_XL   =0x2B
    OUT_Z_L_XL   =0x2C
    OUT_Z_H_XL   =0x2D
    g=9.80665 # m/s**2 in 1g.
    odr_gs = (0, 14.9, 59.5, 119.0, 238.0, 476.0, 952.0, None)
    fs_gs=(245.0,500.0,None,2000.0)
    def select(self,val:[int,float],vals:Sequence[float])->int:
        if type(val)==int and val>=0 and val<len(vals):
            return val
        else:
            return vals.index(val)
    def __init__(self,spi:spidev.SpiDev):
        super().__init__(spi)
    def whoami(self)->int:
        return self.read_reg(self.WHO_AM_I)
    def begin(self,odr_g:[int,float]=119.0,fs_g:int=0,odr_a:int=3,fs_a:int=0):
        """

        :param odr_g:
        :param fs_g:
        :param odr_a:
        :param fs_a:
        :return:
        """
        odr_g=self.select(odr_g,self.odr_gs)
        self.odr_g=self.odr_gs[odr_g]
        fs_g=self.select(fs_g,self.fs_gs)
        self.fs_g=self.fs_gs[fs_g]
        self.write_reg(self.CTRL_REG1_G, ((odr_g & 0x07) << 5) | # Output data rate
                                         ((fs_g  & 0x03) << 3) | # Full-scale
                                         ((0     & 0x03) << 0))  # Bandwidth selection

        self.write_reg(self.CTRL_REG2_G, ((0     & 0x03) << 2) | # Interrupt filter selection (No HPF or LPF2)
                                         ((0     & 0x03) << 0))  # Output filter selection (No HPF or LPF2)

        self.write_reg(self.CTRL_REG3_G, ((0     & 0x01) << 7) | # Low-power mode (disabled)
                                         ((0     & 0x01) << 6) | # High-pass filter (disabled)
                                         ((0     & 0x0f) << 0))  # High-pass cutoff frequency (n/a)

        self.write_reg(self.CTRL_REG5_XL,((0     & 0x03) << 6) | # Decimation (no decimation)
                                         ((1     & 0x01) << 5) | # az enabled
                                         ((1     & 0x01) << 4) | # ay enabled
                                         ((1     & 0x01) << 3) | # ax enabled
                                         ((0     & 0x07) << 0))  # Reserved, must write 0

        self.write_reg(self.CTRL_REG4   ,((0     & 0x03) << 6) | # Reserved, must write 0
                                         ((1     & 0x01) << 5) | # gz enabled
                                         ((1     & 0x01) << 4) | # gy enabled
                                         ((1     & 0x01) << 3) | # gx enabled
                                         ((0     & 0x01) << 0))  # Reserved, must write 0

        self.write_reg(self.CTRL_REG6_XL,((odr_a & 0x07) << 5) | # Output data rate
                                         ((fs_a  & 0x03) << 3) | # Full-scale
                                         ((0     & 0x07) << 0))  # Bandwidth scale and selection

        self.write_reg(self.CTRL_REG8,   ((0     & 0x01) << 7) |  # Boot request
                                         ((1     & 0x01) << 6) |  # Block data update
                                         ((0     & 0x01) << 5) |  # Interrupt active high
                                         ((0     & 0x01) << 4) |  # Push-pull on INT pins
                                         ((0     & 0x01) << 3) |  # SPI mode 4 wire
                                         ((1     & 0x01) << 2) |  # Interface register address increment
                                         ((0     & 0x01) << 1) |  # Little endian select
                                         ((0     & 0x01) << 0))   # Software Reset

    def query(self,cal=False):
        """
        :param cal: If true, use nominal full-scale values to calibrate into SI units. False returns
                    raw DN values.
        :return: Tuple of (status, ax, ay, az, gx, gy, gz, T). If c
        """
        if cal:
            raise NotImplementedError("Calibration isn't yet implemented")
        status  =self.read_reg(self.STATUS_REG_G)
        out_temp=self.read_int16(self.OUT_TEMP_L)
        out_x_g =self.read_int16(self.OUT_X_L_G)
        out_y_g =self.read_int16(self.OUT_Y_L_G)
        out_z_g =self.read_int16(self.OUT_Z_L_G)
        out_x_xl=self.read_int16(self.OUT_X_L_XL)
        out_y_xl=self.read_int16(self.OUT_Y_L_XL)
        out_z_xl=self.read_int16(self.OUT_Z_L_XL)
        return status,out_temp,out_x_g,out_y_g,out_z_g,out_x_xl,out_y_xl,out_z_xl


def main():
    import spidev
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