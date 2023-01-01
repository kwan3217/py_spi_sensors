import time

from spidev import SpiDev

from spi_sensor import SPI_sensor


class BME680(SPI_sensor):
    chip_id = 0xD0;
    reset = 0xE0;
    ctrl_hum = 0x72;
    ctrl_meas = 0x74;
    config = 0x75;
    ctrl_gas_1 = 0x71;
    meas_status_0 = 0x1d;
    pres_msb = 0x1f;

    def __init__(self,spi:SpiDev):
        super().__init__(spi)
        self.page=0
    def set_page(self,new_page:int,force:bool=False):
        """
        Explicitly set SPI register page
        :param new_page: Register page to use
        """
        # Register page is bit 4 in register 0x73/0xF3 (IE same slot in both pages).
        # It seems backwards, but page 0 is registers 0x80-0xFF, and page 1 is 0x00-0x7F
        if force or self.page!=new_page:
            self.spi.xfer(bytes([0x73 & 0x7f]) + bytes((new_page<<4,)))
            self.page=new_page
    def read_reg(self,reg_addr:int,count:int=1)->bytes:
        self.set_page(1 if reg_addr<0x80 else 0)
        return super().read_reg(reg_addr,count)
    def write_reg(self,reg_addr:int,values:[bytes,int])->None:
        self.set_page(1 if reg_addr<0x80 else 0)
        super().write_reg(reg_addr,values)
    def begin(self,osrs_t:int=5, osrs_p:int=5, osrs_h:int=5, osrs_g:int=0):
        """

        :param osrs_t: T oversample -- set to 0 to disable T readout,
                                       or set oversampling to 2**(osrs_t-1). Default is highest oversampling.
        :param osrs_p: P oversample -- set to 0 to disable P readout,
                                       or set oversampling to 2**(osrs_p-1). Default is highest oversampling.
        :param osrs_h:
        :param osrs_g:
        """
        # Make sure we are on a known register page
        self.osrs_t=osrs_t
        self.osrs_p=osrs_p
        self.osrs_h=osrs_h
        self.osrs_g=osrs_g
        if self.osrs_g>0:
            raise NotImplementedError("Gas sensor not implemented")
        self.set_page(0,force=True) #Change to page 0

        # Reset, and allow 10ms to wake up. Reset will also put us on page 0.
        self.write_reg(0xE0,0xb6)
        time.sleep(0.01)

        # Set oversampling for T, P, H. T and P in same register, H in a different register
        self.write_reg(self.ctrl_hum,  (     0 & 0x01) << 6 | ##Disable spi 3wire interrupt
                                       (osrs_h & 0x07) << 0)  ##Set humidity oversample
        print(f"readback of ctrl_hum 0x{self.ctrl_hum:02x}: 0b{self.read_reg(self.ctrl_hum):08b}")

        self.write_reg(self.ctrl_meas, (osrs_t & 0x07)<<5 |  # Temperature oversample
                                       (osrs_p & 0x07)<<2 |  # Pressure oversample
                                       (0      & 0x03)<<0 )  # Sleep mode for now
        print(f"readback of ctrl_meas 0x{self.ctrl_meas:02x}: 0b{self.read_reg(self.ctrl_meas):08b}")

        # Disable IIR for temperature
        self.write_reg(self.config,    (0      & 0x07)<<2 |  # Disable IIR by setting coefficient to 0
                                       (0      & 0x01)<<0 )  # Disable SPI 3wire interface
        print(f"readback of config 0x{self.config:02x}: 0b{self.read_reg(self.config):08b}")

        # Disable gas measurement
        self.write_reg(self.ctrl_gas_1,(0      & 0x01)<<4 )     # Disable run_gas measurement
        print(f"readback of ctrl_gas_1 0x{self.ctrl_gas_1:02x}: 0b{self.read_reg(self.ctrl_gas_1):08b}")

        # Read cal coefficients
        self.par_t1=self.read_uint16(0xe9)
        self.par_t2=self.read_int16(0x8a)
        self.par_t3=self.read_int8(0x8c)
        print(f"par_t1: {self.par_t1}")
        print(f"par_t2: {self.par_t2}")
        print(f"par_t3: {self.par_t3}")

        self.par_p1 = self.read_uint16(0x8e)
        self.par_p2 = self.read_int16(0x90)
        self.par_p3 = self.read_int8(0x92)
        self.par_p4 = self.read_int16(0x94)
        self.par_p5 = self.read_int16(0x96)
        self.par_p6 = self.read_int8(0x99)
        self.par_p7 = self.read_int8(0x98)
        self.par_p8 = self.read_int16(0x9c)
        self.par_p9 = self.read_int16(0x9e)
        self.par_p10 = self.read_reg(0xa0)
        print(f"par_p1: {self.par_p1}")
        print(f"par_p2: {self.par_p2}")
        print(f"par_p3: {self.par_p3}")
        print(f"par_p4: {self.par_p4}")
        print(f"par_p5: {self.par_p5}")
        print(f"par_p6: {self.par_p6}")
        print(f"par_p7: {self.par_p7}")
        print(f"par_p8: {self.par_p8}")
        print(f"par_p9: {self.par_p9}")
        print(f"par_p10: {self.par_p10}")
        buf=self.read_reg(0xe1, 3);
        print(f"buf: {buf[0]:02x}{buf[1]:02x}{buf[2]:02x}");
        self.par_h1 = ((buf[1] & 0x0F) >> 0) | (buf[2] << 4);
        self.par_h2 = ((buf[1] & 0xF0) >> 4) | (buf[0] << 4);
        self.par_h3 = self.read_int8(0xe4);
        self.par_h4 = self.read_int8(0xe5);
        self.par_h5 = self.read_int8(0xe6);
        self.par_h6 = self.read_reg(0xe7);
        self.par_h7 = self.read_int8(0xe8);
        print(f"par_h1: {self.par_h1}")
        print(f"par_h2: {self.par_h2}")
        print(f"par_h3: {self.par_h3}")
        print(f"par_h4: {self.par_h4}")
        print(f"par_h5: {self.par_h5}")
        print(f"par_h6: {self.par_h6}")
        print(f"par_h7: {self.par_h7}")

        # Do a priming read -- this will eventually set the data-ready bit.
        self.kickoff()
    def whoami(self)->int:
        return self.read_reg(self.chip_id)
    def kickoff(self):
        self.write_reg(self.ctrl_meas,(self.osrs_t & 0x07)<<5 |  # Write back existing oversample
                                      (self.osrs_p & 0x07)<<2 |
                                      (1           & 0x03)<<0)   # Force a measurement to start
    def wait_ready(self,delay=0.01)->int:
        """

        :param delay: Delay in seconds between checking for ready
        :return: Number of times around the loop
        """
        time.sleep(delay)
        ready=self.read_reg(self.meas_status_0)
        result=0
        while not bool((ready >> 7) & 0x01):
            time.sleep(delay)
            result+=1
            ready = self.read_reg(self.meas_status_0)
        return result
    def calibrate_T(self,rT:int):
        """

        :param rT:
        :return:
        """
        var1 = (((float(rT) / 16384.0) - (float(self.par_t1) / 1024.0)) * (float(self.par_t2)))

        # calculate var2 data
        var2 = ((((float(rT) / 131072.0) - (float(self.par_t1) / 8192.0)) *
                 ((float(rT) / 131072.0) - (float(self.par_t1) / 8192.0))) * (float(self.par_t3) * 16.0))

        # t_fine value, used as temperature for other measurements
        t_fine = (var1 + var2)

        # compensated temperature data
        T = ((t_fine) / 5120.0)
        return T,t_fine
    def calibrate_P(self,rP:int,t_fine:float):
        # Pressure calibration from same file, float calc_pressure()
        var1 = ((float(t_fine) / 2.0) - 64000.0)
        var2 = var1 * var1 * ((float(self.par_p6)) / (131072.0))
        var2 = var2 + (var1 * (float(self.par_p5)) * 2.0)
        var2 = (var2 / 4.0) + ((float(self.par_p4)) * 65536.0)
        var1 = ((((float(self.par_p3) * var1 * var1) / 16384.0) + (float(self.par_p2) * var1)) / 524288.0)
        var1 = ((1.0 + (var1 / 32768.0)) * (float(self.par_p1)))
        P = (1048576.0 - (float(rP)))

        # Avoid exception caused by division by zero */
        if int(var1) != 0:
            P = (((P - (var2 / 4096.0)) * 6250.0) / var1)
            var1 = ((float(self.par_p9)) * P * P) / 2147483648.0;
            var2 = P * ((float(self.par_p8)) / 32768.0);
            var3 = ((P / 256.0) * (P / 256.0) * (P / 256.0) * (self.par_p10 / 131072.0));
            P = (P + (var1 + var2 + var3 + (float(self.par_p7) * 128.0)) / 16.0);
        else:
            P = 0
        return P
    def calibrate_h(self,rh:int,T:float):
        var1 = (float(float(rh)) -
                ((float(self.par_h1) * 16.0) + ((float(self.par_h3) / 2.0) * T)))
        var2 = var1 * (((float(self.par_h2) / 262144.0) *
                        (1.0 + ((float(self.par_h4) / 16384.0) * T) +
                         ((float(self.par_h5) / 1048576.0) * T * T))))
        var3 = float(self.par_h6) / 16384.0
        var4 = float(self.par_h7) / 2097152.0
        h = var2 + ((var3 + (var4 * T)) * var2 * var2)
        if (h > 100.0):
            h = 100.0
        elif (h < 0.0):
            h = 0.0
        return h

    def query(self,rekick:bool=True,cal:bool=True):
        """
        :param rekick: Kick off a new measurement as soon as this one is done
        :return: Raw t, p, and h
        """
        pres_msb,pres_lsb,pres_xlsb,temp_msb,temp_lsb,temp_xlsb,hum_msb,hum_lsb=self.read_reg(self.pres_msb,8)

        if rekick:
            self.kickoff()
        rP=(pres_msb<<12 | pres_lsb<<4 | pres_xlsb>>4)
        rT=(temp_msb<<12|temp_lsb<<4|temp_xlsb>>4)
        rh=(hum_msb<<8|hum_lsb)
        if not cal:
            return rP,None,1,rT,None,1,rh,None,1
        else:
            # Code from https://github.com/BoschSensortec/BME68x-Sensor-API/blob/master/bme68x.c::float calc_temperature()
            # which is just a transcription of the datasheet, copied here to avoid transcription errors.
            # BME680 and BME688 use the same registers and formulas, but the calibration coefficients are documented
            # only in the BME688 datasheet, pp23-
            # calculate var1 data
            T,t_fine=self.calibrate_T(rT)
            dT=self.calibrate_T(rT+1)[0]-T

            P=self.calibrate_P(rP,t_fine)
            dP=self.calibrate_P(rP+1,t_fine)-P

            # Humidity, ibid, floaf calc_humidity()
            h=self.calibrate_h(rh,T)
            dh=self.calibrate_h(rh+1,T)-h
            return rP,P,dP,rT,T,dT,rh,h,dh

def main():
    """
    This depends on ~CE0 being connected directly to ~CS on sensor
    """
    spi = SpiDev()
    spi.open(0, 0)

    spi.max_speed_hz = 3_900_000
    spi.mode = 0b00

    bme = BME680(spi)
    bme.begin()
    print(f'Chip ID (should be 0x61): 0x{bme.whoami():02x}')
    while True:
        print(bme.wait_ready())
        rP, P, dP, rT, T, dT, rh, h, dh = bme.query()
        print(
            f'P: raw {rP:6d}, cal {P:.1f}  Pa, d {dP:.4e}Pa    T: raw {rT:6d}, cal {T:.4f}degC, d {dT:.4e}degC    h: raw {rh:6d}, cal {h:.3f}    %, d {dh:.4e}%')

if __name__=="__main__":
    main()