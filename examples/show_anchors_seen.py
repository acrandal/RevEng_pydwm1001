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

    print("Connected, Showing Current seen anchors list, press Ctrl+C to stop")

    try:
        while True:
            anchors_seen_count = node.get_anchors_seen_count()
            print(f"Anchors seen count: {anchors_seen_count}")
            anchors_seen_list = node.get_list_of_anchors()
            print(f"Anchors seen list: {anchors_seen_list}")
            sleep(5)
            print("-" * 79)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt - stopping")

    node.disconnect()


if __name__ == "__main__":
    main()
