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
import dwm1001.dwm1001 as dwm1001

SERIAL_PORT_PATH = "/dev/ttyACM0"


def main() -> NoReturn:
    logging.basicConfig(level=logging.INFO)  # Set to DEBUG for more info
    # logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for more info

    serial_handle = Serial(SERIAL_PORT_PATH, baudrate=115200, timeout=5)

    node = dwm1001.UartDwm1001(serial_handle)
    node.connect()

    print("Connected - demoing of tag information")
    print(f"Node mode: {node.get_node_mode()}")
    print(f"Node uptime: {node.get_uptime_ms()} ms")
    print(f"Node position: {node.get_position()}")
    print(f"Node accelerometer data: {node.get_accelerometer_data()}")
    print(f"Node network id: {node.get_network_id()}")
    print(f"Node Bluetooth address: {node.get_ble_address()}")
    print("Demo complete - disconnecting")

    node.disconnect()


if __name__ == "__main__":
    main()
