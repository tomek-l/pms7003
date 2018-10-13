"""A minimalistic python interface for PMS7003 sensor"""
import serial
from collections import OrderedDict

class PmsSensorExcpetion(Exception):
    """
    Implies a problem with sensor communication that is unlikely to re-occur (e.g. serial connection glitch)
    Prevents from returning corrupt measurements
    """
    pass

START_SEQ = bytes([0x42, 0x4d])
FRAME_BYTES = 30

VALUES_MEANING = {
    1 :'PM1.0CF1',
    2 : 'PM2.5CF1',
    3 : 'PM10CF1',
    4 : 'PM1.0',
    5 : 'PM2.5',
    6 : 'PM10',
    7 : 'n0.3',
    8 : 'n0.5',
    9 : 'n1.0',
    10 : 'n5.0',
    11 : 'n10',
    }

NO_VALUES = len(VALUES_MEANING)


class Pms7003Sensor:

    def __init__(self, serial_device):
        #values according to product data manual
        self._serial = serial.Serial(port=serial_device, baudrate=9600, bytesize=serial.EIGHTBITS,
                                     parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=2)

    def _get_frame(self):
        """
        :return: a frame as a list of integer values of bytes
        """
        with self._serial as s:
            s.read_until(START_SEQ)
            frame = list(s.read(FRAME_BYTES))
            if len(frame) == FRAME_BYTES:
                return frame
            else:
                raise PmsSensorExcpetion

    def _parse_frame(self, f):
        """
        iterates every second index and glues the H and L bytes together
        :return: raw parsed integer values
        """
        vls = [f[i]<<8 | f[i+1] for i in range(0, len(f), 2)]
        return vls

    def _valid_frame(self, frame, vls):
        _checksum = vls[-1]
        return _checksum == sum(frame[:-2]) + sum(START_SEQ)

    def read(self):
        """
        :return: a dict with measurements or raises Pms7003Exception in case of a problem with connection
        """
        frame = self._get_frame()
        values = self._parse_frame(frame)
        #frame_len = values[0] (you could read the frame length from here)

        if self._valid_frame(frame, values):
            #return {VALUES_MEANING[i]: values[i] for i in range(1, NO_VALUES)} (regular dict)
            return OrderedDict((VALUES_MEANING[i], values[i]) for i in range(1, NO_VALUES))
        else:
            raise PmsSensorExcpetion
        