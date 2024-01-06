import logging

import dwm1001
from serial import Serial


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    print("Testing things brutally")
    ser = Serial("/dev/ttyACM0", baudrate=115200, timeout=5)

    dwm = dwm1001.UartDwm1001(ser)
    dwm.connect()
    print("Connected")
    uptime_ms = dwm.get_uptime_ms()
    print(f"Uptime: {uptime_ms} ms")

    uptime_ms = dwm.get_uptime_ms()
    print(f"Uptime: {uptime_ms} ms")
    uptime_ms = dwm.get_uptime_ms()
    print(f"Uptime: {uptime_ms} ms")
    uptime_ms = dwm.get_uptime_ms()
    print(f"Uptime: {uptime_ms} ms")
    uptime_ms = dwm.get_uptime_ms()
    print(f"Uptime: {uptime_ms} ms")

    print("Done.")