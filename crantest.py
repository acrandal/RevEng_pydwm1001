import logging

import dwm1001
from serial import Serial
import pexpect_serial
from pexpect import exceptions
from time import sleep


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    print("Testing things brutally")
    ser = Serial("/dev/ttyACM0", baudrate=115200, timeout=5)

    dwm1001 = dwm1001.UartDwm1001(ser)
    dwm1001.connect()

    #sleep(5)
    for i in range(2):
        print(dwm1001.get_uptime_ms())
     #   sleep(1)
    # print(dwm1001.get_command_output("ut"))

    #print(dwm1001.pexpect_handle.before)

    #dwm1001.get_uptime_ms()

    print(dwm1001.get_system_info())
    print("---------------------------")
    print(dwm1001.get_position())

    print(dwm1001.get_accelerometer_data())

    print(dwm1001.get_node_mode_str())
    print(dwm1001.get_node_mode())
    print(dwm1001.is_in_tag_mode())
    print(dwm1001.is_in_anchor_mode())
    print(dwm1001.is_in_anchor_initiator_mode())

    #dwm1001.disconnect()
    ser.close()


    print("Done.")