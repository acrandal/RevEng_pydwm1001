import logging

import pexpect_serial
import pexpect

class DWM1001Node_State:
    def __init__(self, pexpect_handle: pexpect_serial.SerialSpawn):
        self.__log = logging.getLogger(__class__.__name__)
        self.__pexpect_handle = pexpect_handle


