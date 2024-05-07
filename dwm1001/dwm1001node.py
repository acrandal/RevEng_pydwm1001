#
#   Qovro UWB Positioning System
#   DecaWave DWM1001 Module
#   Wrapper and API for serial interface
#

# Standard library imports
from dataclasses import dataclass
from enum import Enum
import time
import logging
import re

# Third party imports
from serial import Serial
import pexpect_serial
import pexpect

# DWM1001 module imports
from .exceptions import ParsingError, ReservedGPIOPinError
from .tag_position import TagPosition
from .accelerometer_data import AccelerometerData
from .anchor_node_data import AnchorNodeData
from .node_mode import NodeMode
from .shell_command import ShellCommand


class DWM1001Node:
    """! Represents the communication interface with DWM1001 using UART.

    This class provides methods to interact with DWM1001 through UART, send commands, and receive responses.

    @param serial_handle (Serial): An already open serial handle to the DWM1001 device.

    @exception pexpect.exceptions.TIMEOUT: If a timeout occurs while waiting for a response from the DWM1001.

    Example usage:
      - dwm1001 = UartDwm1001(serial_handle)
      - dwm1001.connect()
      - tag_position = dwm1001.get_position()
      - dwm1001.disconnect()
    """

    # These delay periods were experimentally determined
    __RESET_DELAY_PERIOD = 0.1

    __SHELL_PROMPT = "dwm> "
    __BINARY_MODE_RESPONSE = "@\x01\x01"

    __LED_GPIO_PIN = 14

    def __init__(self, serial_handle: Serial, shell_timeout_sec=3.0) -> None:
        """! Constructor for UartDwm1001 class.
        @param serial_handle (Serial): An already open Serial handle to the DWM1001 device."""
        self.__log = logging.getLogger(__class__.__name__)
        self.__serial_handle = serial_handle
        self.__pexpect_handle = pexpect_serial.SerialSpawn(
            self.__serial_handle, timeout=shell_timeout_sec
        self._node_state_handle = None
        )

    def connect(self) -> None:
        """! Connects to the DWM1001 device."""
        if not self.is_in_shell_mode():
            self.__log.debug("Not in shell mode, initializing shell.")
            try:
                self.enter_shell_mode()
            except pexpect.exceptions.TIMEOUT:
                self.__log.warning("Connect failed.")
                raise pexpect.exceptions.TIMEOUT("Shell mode response timeout.")
        else:
            self.__log.debug("Already in shell mode.")
        serial_port_path = self.__serial_handle.name
        self.__log.info(f"Connected to DWM1001 on: {serial_port_path}")
        self.__clear_pexpect_buffer()

    def __clear_pexpect_buffer(self) -> None:
        self.__pexpect_handle.before = ""  # Clear buffer

    def disconnect(self) -> None:
        """! Disconnects from the DWM1001 device and resets to binary (non-shell) interface."""
        self.__log.debug("Disconnecting from DWM1001.")
        self.exit_shell_mode()

    def get_uptime_ms(self) -> int:
        """! Gets the uptime of the DWM1001 in milliseconds."""
        uptime_str = self.get_command_output(ShellCommand.GET_UPTIME.value)
        return self._parse_uptime_str(uptime_str)

    def _parse_uptime_str(self, uptime_str: str) -> int:
        _, right = uptime_str.split(" (")
        uptime_ms_str, _ = right.split(" ms")
        uptime_ms = int(uptime_ms_str)
        return uptime_ms

    def get_system_info(self) -> str:
        """! Gets the system info of the DWM1001."""
        system_info_str = self.get_command_output(ShellCommand.GET_SYSTEM_INFO.value)
        return system_info_str

    def get_command_output(self, command: ShellCommand) -> str:
        """! Sends a shell command to the DWM1001 and returns the output.
        @param command (ShellCommand): The shell command to send.
        @return str: The output of the shell command."""
        try:
            self.__pexpect_handle.sendline(command)
            self.__pexpect_handle.expect(self.__SHELL_PROMPT)
            command_output = self.__pexpect_handle.before.decode().strip()
        except pexpect.exceptions.TIMEOUT:
            self.__log.warning(f"Timeout on command: {command}")
            raise pexpect.exceptions.TIMEOUT(f"Timeout on command: {command}")
        return command_output

    def reset(self) -> None:
        """! Resets (reboots) the DWM1001 device."""
        self.__pexpect_handle.sendline(ShellCommand.RESET.value)
        time.sleep(self.__RESET_DELAY_PERIOD)

    def is_in_shell_mode(self) -> bool:
        """! Checks if the DWM1001 is in shell interface mode."""
        self.__pexpect_handle.send("a" + ShellCommand.ENTER.value)
        try:
            result_index = self.__pexpect_handle.expect(
                [self.__BINARY_MODE_RESPONSE, self.__SHELL_PROMPT], timeout=1
            )
            if result_index == 0:
                return False
            elif result_index == 1:
                return True
        except pexpect.exceptions.TIMEOUT:
            self.__log.warning("Timeout while checking is in shell mode.")
            return False

    def enter_shell_mode(self) -> None:
        """! Enters the shell interface mode."""
        if self.is_in_shell_mode():  # Protect if already in shell mode
            self.__log.debug("Already in shell mode.")
            return

        self.__log.debug("Entering shell mode.")
        self.__pexpect_handle.send(ShellCommand.DOUBLE_ENTER.value)
        try:
            self.__pexpect_handle.expect(self.__SHELL_PROMPT)  # Wait for shell prompt
        except pexpect.exceptions.TIMEOUT:
            self.__log.warning("Timeout while entering shell mode.")
            raise pexpect.exceptions.TIMEOUT("Timeout while entering shell mode.")
        self.__log.debug("Entered shell mode.")

    def exit_shell_mode(self) -> None:
        """! Exits the shell interface mode.

        It also resets the device to ensure that no commands are running on reconnect.

        """
        # If you quit shell mode (with `quit` command) without stopping
        # a running command, the command will automatically continue
        # when re-entering shell mode. This can be confusing, so we
        # reset the device instead to ensure previously-running commands
        # terminate.
        self.reset()

    def get_position(self) -> TagPosition:
        """! Gets the position of the tag from the DWM1001.
        @return TagPosition: The position of the tag.
        """
        location_str = self.get_command_output(ShellCommand.GET_POSITION.value)
        location = TagPosition.from_string(location_str)
        return location

    def get_ble_address(self) -> str:
        """! Gets the Bluetooth Low Energy (BLE) address of the DWM1001.
        @return str: The BLE hardware/MAC address of the DWM1001.
        """
        system_info_str = self.get_system_info()
        return self._parse_ble_address(system_info_str)

    def _parse_ble_address(self, system_info_str: str) -> str:
        # Example line: [036167.350 INF] ble: addr=E0:E5:D3:0A:19:BE
        # Example line: [036967.750 INF] ble: addr=E0:D5:F3:FA:19:C1
        pattern = r"ble: addr=(?P<ble_address>[0-9A-F:]+)"
        match = re.search(pattern, system_info_str)
        if match is None:
            raise ParsingError("Could not parse BLE address.")
        return match.group("ble_address")

    def get_network_id(self) -> str:
        """! Gets the network ID (the hex name) the DWM1001 is associated with.
        @return str: The network ID of the DWM1001."""
        system_info_str = self.get_system_info()
        return self._parse_network_id(system_info_str)

    def _parse_network_id(self, system_info_str: str) -> str:
        # Example line: [036167.320 INF] uwb0: panid=xC7D4 addr=xDECA59CDFA608830
        pattern = r"panid=(?P<network_id>x[0-9A-F]+) addr="
        match = re.search(pattern, system_info_str)
        if match is None:
            raise ParsingError("Could not parse network ID.")
        return match.group("network_id")

    def get_accelerometer_data(self) -> AccelerometerData:
        """! Gets a sample of the accelerometer data from the DWM1001.
        @return AccelerometerData: The accelerometer data with x,y,z values.
        """
        accelerometer_str = self.get_command_output(
            ShellCommand.GET_ACCELEROMETER.value
        )
        return self._parse_accelerometer_str(accelerometer_str)

    def _parse_accelerometer_str(self, accelerometer_str: str) -> AccelerometerData:
        """! Parses the output of the accelerometer command to get the x,y,z values.
        @param accelerometer_str (str): The output of the 'accelerometer' command.
        @return AccelerometerData: The accelerometer data with x,y,z values."""
        # Example line: acc: x = -256, y = 1424, z = 8032
        pattern = r"acc: x = (?P<x>-?\d+), y = (?P<y>-?\d+), z = (?P<z>-?\d+)"
        match = re.search(pattern, accelerometer_str)
        if match is None:
            raise ParsingError("Could not parse accelerometer data.")
        return AccelerometerData(
            x_raw=int(match.group("x")),
            y_raw=int(match.group("y")),
            z_raw=int(match.group("z")),
        )

    def get_node_mode_str(self) -> str:
        """! Gets the node mode of the DWM1001.
        @return str: The shell node mode string.

        - Example tag in active mode:     "mode: tn (act,twr,np,le)"
        - Example tag in passive mode:    "mode: tn (pasv,twr,lp,le)"
        - Example tag with UWB radio off: "mode: tn (off,twr,np,le)"
        - Example anchor:                 "mode: an (act,-,-)"
        - Example anchor in initiating:   "mode: ani (act,-,-)"
        """
        node_mode_str = self.get_command_output(ShellCommand.GET_MODE.value)
        return node_mode_str

    def is_in_tag_mode(self) -> bool:
        """! Checks if the DWM1001 node is in tag mode.
        @return bool: True if the node is in tag mode, False otherwise."""
        node_mode_str = self.get_node_mode_str()
        return self._parse_node_mode_str(node_mode_str) == NodeMode.TAG

    def is_in_anchor_mode(self) -> bool:
        """! Checks if the DWM1001 node is in anchor mode.
        @return bool: True if the node is in anchor mode, False otherwise."""
        node_mode_str = self.get_node_mode_str()
        return self._parse_node_mode_str(node_mode_str) == NodeMode.ANCHOR

    def is_in_anchor_initiator_mode(self) -> bool:
        """! Checks if the DWM1001 node is in anchor initiator mode.
        @return bool: True if the node is in anchor initiator mode, False otherwise."""
        node_mode_str = self.get_node_mode_str()
        return self._parse_node_mode_str(node_mode_str) == NodeMode.ANCHOR_INITIATOR

    def get_node_mode(self) -> NodeMode:
        """! Gets the node mode of the DWM1001.
        @return NodeMode: The node mode of the DWM1001."""
        node_mode_str = self.get_node_mode_str()
        return self._parse_node_mode_str(node_mode_str)

    def _parse_node_mode_str(self, node_mode_str: str) -> NodeMode:
        # Example: mode: tn (act,twr,np,le)
        # Example: mode: tn (pasv,twr,lp,le)
        # Example: mode: tn (off,twr,np,le)
        # Example: mode: an (act,-,-)
        # Example: mode: ani (act,-,-)
        if "mode: tn (" in node_mode_str:
            return NodeMode.TAG
        elif "mode: an (" in node_mode_str:
            return NodeMode.ANCHOR
        elif "mode: ani (" in node_mode_str:
            return NodeMode.ANCHOR_INITIATOR

    def get_gpio_pin_state(self, pin: int) -> bool:
        """! Gets the state of a GPIO pin on the DWM1001.
        @param pin (int): The GPIO pin number (0-31).
        @return bool: True if the pin is high, False if the pin is low.

        Valid pin numbers are: [2, 8, 9, 10, 12, 13, 14, 15, 23, 27]
        """
        pin_state_str = self.get_command_output(f"{ShellCommand.GPIO_GET.value} {pin}")
        return self._parse_gpio_pin_state_str(pin_state_str)

    def get_gpio_pin_state(self, pin: int) -> bool:
        """! Gets the state of a GPIO pin on the DWM1001.
        @param pin (int): The GPIO pin number (0-31).
        @return bool: True if the pin is high, False if the pin is low.

        Valid pin numbers are: [2, 8, 9, 10, 12, 13, 14, 15, 23, 27]
        """
        pin_state_str = self.get_command_output(f"{ShellCommand.GPIO_GET.value} {pin}")
        if "reserved" in pin_state_str:
            raise ReservedGPIOPinError(f"GPIO pin {pin} is reserved by the DWM1001.")
        return self._parse_gpio_pin_state_str(pin_state_str)

    def _parse_gpio_pin_state_str(self, pin_state_str: str) -> bool:
        """! Parses the output of the GPIO_GET command to get the state of a GPIO pin.
        @param pin_state_str (str): The output of the GPIO_GET command.
        @return bool: True if the pin is high, False if the pin is low."""
        # Example: gpio2: 0
        # Example: gpio2: 1
        # Example: gpio14: 0
        # Example: gpio14: 1
        pattern = r"gpio\d+: (?P<state>\d)"
        match = re.search(pattern, pin_state_str)
        if match is None:
            raise ParsingError("Could not parse GPIO pin state.")
        return bool(int(match.group("state")))

    def set_gpio_pin_high(self, pin: int) -> None:
        """! Sets a GPIO pin on the DWM1001 to HIGH.
        @param pin (int): The GPIO pin number (0-31)."""
        result_str = self.get_command_output(f"{ShellCommand.GPIO_SET.value} {pin}")
        if "reserved" in result_str:
            raise ReservedGPIOPinError(f"GPIO pin {pin} is reserved by the DWM1001.")

    def set_gpio_pin_low(self, pin: int) -> None:
        """! Sets a GPIO pin on the DWM1001 to LOW.
        @param pin (int): The GPIO pin number (0-31)."""
        result_str = self.get_command_output(f"{ShellCommand.GPIO_CLEAR.value} {pin}")
        if "reserved" in result_str:
            raise ReservedGPIOPinError(f"GPIO pin {pin} is reserved by the DWM1001.")

    def set_led_on(self) -> None:
        """! Sets the User LED (D12) on the DWM1001 to ON (high).
        NOTE: LED is active low"""
        self.set_gpio_pin_low(self.__LED_GPIO_PIN)

    def set_led_off(self) -> None:
        """! Sets the User LED (D12) on the DWM1001 to OFF (low).
        NOTE: LED is active low"""
        self.set_gpio_pin_high(self.__LED_GPIO_PIN)

    def is_valid_gpio_pin(self, pin: int) -> bool:
        """! Checks if a GPIO pin is reserved by the DWM1001.
        @param pin (int): The GPIO pin number (0-31).
        @return bool: True if the pin is valid, False otherwise.

        Valid pin numbers are: [2, 8, 9, 10, 12, 13, 14, 15, 23, 27]
        """
        return pin in [2, 8, 9, 10, 12, 13, 14, 15, 23, 27]

    def get_list_of_anchors(self) -> list:
        """! Gets a list of anchors currently seen by the DWM1001.
        @return list[AnchorNodeData]: A list of AnchorNodeData instances.
        """
        anchor_list_str = self.get_command_output(ShellCommand.GET_ANCHOR_LIST.value)
        return self._parse_anchor_list_str(anchor_list_str)

    def _parse_anchor_list_str(self, anchor_list_str: str) -> list:
        """! Parses the output of the "List Anchors" command to get a list of anchors.
        @param anchor_list_str (str): The output of the 'list anchors' command.
        @return list[AnchorNodeData]: A list of AnchorNodeData instances.
        """
        lines = anchor_list_str.splitlines()
        anchor_list = []
        for line in lines:
            if " seat=" in line:
                anchor_list.append(AnchorNodeData.from_string(line))
        return anchor_list

    def get_anchors_seen_count(self) -> int:
        """! Gets the number of anchors currently seen by the DWM1001.
        @return int: The number of anchors seen.
        """
        # Example: [005899.170 INF] AN: cnt=4 seq=x09
        # Example: [005899.170 INF] AN: cnt=2 seq=x03
        anchor_list_str = self.get_command_output(ShellCommand.GET_ANCHOR_LIST.value)
        return self._parse_anchors_seen_count_str(anchor_list_str)

    def _parse_anchors_seen_count_str(self, anchor_list_str: str) -> int:
        """! Parses the output of the "List Anchors" command to get the number of anchors seen.
        @param anchor_list_str (str): The output of the 'list anchors' command.
        @return int: The number of anchors seen.
        """
        # Example: [005899.170 INF] AN: cnt=4 seq=x09
        # Example: [005899.170 INF] AN: cnt=2 seq=x03
        pattern = r"AN: cnt=(?P<cnt>\d+) seq="
        match = re.search(pattern, anchor_list_str)
        if match is None:
            raise ParsingError("Could not parse anchor list.")
        return int(match.group("cnt"))
