"""
Bit manipulation
"""


def extract_uint16_le(buf:bytes,i0:int=0):
    return buf[i0+1] << 8 | buf[i0+0]


def extract_uint16_be(buf:bytes,i0:int=0):
    return buf[i0+0] << 8 | buf[i0+1]


def extract_int16_le(buf:bytes,i0:int=0):
    result=extract_uint16_le(buf,i0=i0)
    if result >= 0x8000:
        result -= 0x1_0000
    return result


def extract_int8(buf:bytes,i0:int=0):
    if buf[i0]>0x80:
        return buf[i0]-0x1_00
    return buf[i0]

