#!/usr/bin/env python3

# Standard library imports
from pathlib import Path
import sys
from typing import NoReturn
from time import sleep
import logging

# Third party imports
from serial import Serial

# Allows us to find dwm1001 library without installing it
sys.path.append(str(Path(__file__).resolve().parents[1]))
import dwm1001

SERIAL_PORT_PATH = "/dev/ttyACM0"


def main() -> NoReturn:
    logging.basicConfig(level=logging.INFO)  # Set to DEBUG for more info
    # logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for more info

    serial_handle = Serial(SERIAL_PORT_PATH, baudrate=115200, timeout=5)

    node = dwm1001.UartDwm1001(serial_handle)
    node.connect()

    print("Connected, printing acceleration, press Ctrl+C to stop")

    try:
        while True:
            print(node.get_accelerometer_data())
            sleep(0.25)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt - stopping")

    node.disconnect()


if __name__ == "__main__":
    main()
