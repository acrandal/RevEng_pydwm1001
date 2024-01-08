#
#   Qovro UWB Positioning System
#   DecaWave DWM1001 Module
#   Wrapper and API for serial interface
#

# Standard library imports
from dataclasses import dataclass
from enum import Enum
import math
import time
import logging
import re

# Third party imports
from serial import Serial
import pexpect_serial
import pexpect

# Local module defined exceptions
class ParsingError(Exception):
    """! Exception raised when parsing fails for shell command output."""
    pass


class ShellCommand(Enum):
    """! Commands for the DWM1001 shell interface. """
    ENTER = "\r"
    DOUBLE_ENTER = "\r\r"
    RESET = "reset"
    GET_SYSTEM_INFO = "si"  # System info
    GET_UPTIME = "ut"  # Uptime
    GET_POSITION = "apg"  # Get position
    GET_ACCELEROMETER = "av"  # Get accelerometer data
    GET_MODE = "nmg"  # Get node mode: tag, anchor


class NodeMode(Enum):
    """! DWM1001 Node Modes """
    TAG = "tag"
    ANCHOR = "anchor"
    ANCHOR_INITIATOR = "anchor initiator"

@dataclass
class TagPosition:
    """! Represents the position of a tag in 3D space.

    Attributes:
    - x_m (float): X-coordinate in meters.
    - y_m (float): Y-coordinate in meters.
    - z_m (float): Z-coordinate in meters.
    - quality (int): Quality of the tag position.

    """

    x_m: float
    y_m: float
    z_m: float
    quality: int

    def is_almost_equal(self, other: "TagPosition", relative_tolerance_m=0.01) -> bool:
        """! Checks if two TagPosition instances are almost equal in coordinates.

        @param other (TagPosition): The other TagPosition instance to compare.
        @param rel_tol_m (float): Relative tolerance in meters. Defaults to 0.01 meters.

        @return bool: True if the instances are almost equal, False otherwise.
        """
        return (
            math.isclose(self.x_m, other.x_m, rel_tol=relative_tolerance_m)
            and math.isclose(self.y_m, other.y_m, rel_tol=relative_tolerance_m)
            and math.isclose(self.z_m, other.z_m, rel_tol=relative_tolerance_m)
        )

    def __eq__(self, other: "TagPosition") -> bool:
        """! Checks if two TagPosition instances are equal in the coordinate system.

        @param other (TagPosition): The other TagPosition instance to compare.

        @return bool: True if the instances are equal, False otherwise.
        """
        return self.x_m == other.x_m and self.y_m == other.y_m and self.z_m == other.z_m

    @staticmethod
    def from_string(apg_line: str) -> "TagPosition":
        """! Parses a string to create a TagPosition instance.

        @param apg_line (str): The input string containing tag position information.

        @return TagPosition: The TagPosition instance created from the string.

        @exception ParsingError: If the APG line cannot be parsed.

        Example apg position line: x:0 y:0 z:0 qf:0
        Example apg position line: x:10 y:78888 z:-334 qf:57
        """
        # Example line: x:0 y:0 z:0 qf:0
        # Example line: x:10 y:78888 z:-334 qf:57
        # Note: apg command returns values in mm, so we divide by 1000
        pattern = r"x:(?P<x>-?\d+) y:(?P<y>-?\d+) z:(?P<z>-?\d+) qf:(?P<qf>\d+)"
        match = re.search(pattern, apg_line)
        if match is None:
            raise ParsingError("Could not parse APG line.")
        position = TagPosition(
            x_m=float(match.group("x")) / 1000,
            y_m=float(match.group("y")) / 1000,
            z_m=float(match.group("z")) / 1000,
            quality=int(match.group("qf")),
        )

        return position


@dataclass
class AccelerometerData:
    """! Represents the accelerometer data from the DWM1001-DEV module.

    Attributes:
    - x_raw (int): X-axis acceleration.
    - y_raw (int): Y-axis acceleration.
    - z_raw (int): Z-axis acceleration.

    ---

    Measurements come from a ST LIS2DH12TR accelerometer:  
    Documentation: https://www.st.com/resource/en/datasheet/lis2dh12.pdf  
    The LIS2DH12TR can be accessed via TWI/I2C on address 0x33.

    - These values are on a 2g full scale range (by default).  
    - To get the acceleration in gravities, divide by 2^6.  
    - To get m/s^2, convert to gravities and then multiply by 0.004.  
    
    """
    x_raw: int
    y_raw: int
    z_raw: int


class UartDwm1001:
    # These delay periods were experimentally determined
    """! Represents the communication interface with DWM1001 using UART.

    This class provides methods to interact with DWM1001 through UART, send commands, and receive responses.

    @param serial_handle (Serial): An already open serial handle to the DWM1001 device.

    @exception pexpect.exceptions.TIMEOUT: If a timeout occurs while waiting for a response from the DWM1001.

    Example usage:  
      dwm1001 = UartDwm1001(serial_handle)  
      dwm1001.connect()  
      tag_position = dwm1001.get_position()  
      dwm1001.disconnect()  
    """

    __RESET_DELAY_PERIOD = 0.1
    __SHELL_TIMEOUT_PERIOD_SEC = 3.0

    __SHELL_PROMPT = "dwm> "
    __BINARY_MODE_RESPONSE = "@\x01\x01"

    def __init__(self, serial_handle: Serial) -> None:
        self.__log = logging.getLogger(__class__.__name__)
        self.__serial_handle = serial_handle
        self.__pexpect_handle = pexpect_serial.SerialSpawn(
            self.__serial_handle, timeout=self.__SHELL_TIMEOUT_PERIOD_SEC
        )

    def connect(self) -> None:
        """! Connects to the DWM1001 device. """
        if not self.is_in_shell_mode():
            self.__log.debug("Not in shell mode, initializing shell.")
            try:
                self.enter_shell_mode()
            except pexpect.exceptions.TIMEOUT:
                self.__log.warn("Connect failed.")
                raise pexpect.exceptions.TIMEOUT
        else:
            self.__log.debug("Already in shell mode.")
        serial_port_path = self.__serial_handle.name
        self.__log.info(f"Connected to DWM1001 on: {serial_port_path}")
        self.__clear_pexpect_buffer()

    def __clear_pexpect_buffer(self) -> None:
        self.__pexpect_handle.before = ""  # Clear buffer

    def disconnect(self) -> None:
        """! Disconnects from the DWM1001 device and resets to binary (non-shell) interface. """
        self.__log.debug("Disconnecting from DWM1001.")
        self.exit_shell_mode()
        self.__pexpect_handle.close()

    def get_uptime_ms(self) -> int:
        """! Gets the uptime of the DWM1001 in milliseconds. """
        uptime_str = self.get_command_output(ShellCommand.GET_UPTIME.value)
        return self.parse_uptime_str(uptime_str)

    def parse_uptime_str(self, uptime_str: str) -> int:
        _, right = uptime_str.split(" (")
        uptime_ms_str, _ = right.split(" ms")
        uptime_ms = int(uptime_ms_str)
        return uptime_ms

    def get_system_info(self) -> str:
        """! Gets the system info of the DWM1001. """
        system_info_str = self.get_command_output(ShellCommand.GET_SYSTEM_INFO.value)
        return system_info_str

    def get_command_output(self, command: ShellCommand) -> str:
        """! Sends a shell command to the DWM1001 and returns the output. """
        try:
            self.__pexpect_handle.sendline(command)
            self.__pexpect_handle.expect(self.__SHELL_PROMPT)
            command_output = self.__pexpect_handle.before.decode().strip()
        except pexpect.exceptions.TIMEOUT:
            self.__log.warning(f"Timeout on command: {command}")
            raise pexpect.exceptions.TIMEOUT
        return command_output

    def reset(self) -> None:
        """! Resets (reboots) the DWM1001 device. """
        self.__pexpect_handle.sendline(ShellCommand.RESET.value)
        time.sleep(self.__RESET_DELAY_PERIOD)

    def is_in_shell_mode(self) -> bool:
        """! Checks if the DWM1001 is in shell interface mode. """
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
        """! Enters the shell interface mode. """
        if self.is_in_shell_mode():  # Protect if already in shell mode
            self.__log.debug("Already in shell mode.")
            return

        self.__log.debug("Entering shell mode.")
        self.__pexpect_handle.send(ShellCommand.DOUBLE_ENTER.value)
        try:
            self.__pexpect_handle.expect(self.__SHELL_PROMPT)  # Wait for shell prompt
        except pexpect.exceptions.TIMEOUT:
            self.__log.warning("Timeout while entering shell mode.")
            raise pexpect.exceptions.TIMEOUT
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
        return self.parse_ble_address(system_info_str)

    def parse_ble_address(self, system_info_str: str) -> str:
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
        return self.parse_network_id(system_info_str)

    def parse_network_id(self, system_info_str: str) -> str:
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
        return self.parse_accelerometer_str(accelerometer_str)

    def parse_accelerometer_str(self, accelerometer_str: str) -> AccelerometerData:
        # Example line: acc: x = -256, y = 1424, z = 8032
        pattern = r"acc: x = (?P<x>-?\d+), y = (?P<y>-?\d+), z = (?P<z>-?\d+)"
        match = re.search(pattern, accelerometer_str)
        if match is None:
            raise ParsingError("Could not parse accelerometer data.")
        return AccelerometerData(
            x_raw=int(match.group("x")), y_raw=int(match.group("y")), z_raw=int(match.group("z"))
        )

    def get_node_mode_str(self) -> str:
        """! Gets the node mode of the DWM1001.
            @return str: The shell node mode string.

            Example tag in active mode:     "mode: tn (act,twr,np,le)"  
            Example tag in passive mode:    "mode: tn (pasv,twr,lp,le)"  
            Example tag with UWB radio off: "mode: tn (off,twr,np,le)"  
            Example anchor:                 "mode: an (act,-,-)"  
            Example anchor in initiating:   "mode: ani (act,-,-)"  
        """
        node_mode_str = self.get_command_output(ShellCommand.GET_MODE.value)
        return node_mode_str

    def is_in_tag_mode(self) -> bool:
        """! Checks if the DWM1001 node is in tag mode.
        @return bool: True if the node is in tag mode, False otherwise. """
        node_mode_str = self.get_node_mode_str()
        return self.parse_node_mode_str(node_mode_str) == NodeMode.TAG

    def is_in_anchor_mode(self) -> bool:
        """! Checks if the DWM1001 node is in anchor mode.
        @return bool: True if the node is in anchor mode, False otherwise. """
        node_mode_str = self.get_node_mode_str()
        return self.parse_node_mode_str(node_mode_str) == NodeMode.ANCHOR

    def is_in_anchor_initiator_mode(self) -> bool:
        """! Checks if the DWM1001 node is in anchor initiator mode.
        @return bool: True if the node is in anchor initiator mode, False otherwise. """
        node_mode_str = self.get_node_mode_str()
        return self.parse_node_mode_str(node_mode_str) == NodeMode.ANCHOR_INITIATOR

    def get_node_mode(self) -> NodeMode:
        """! Gets the node mode of the DWM1001.
        @return NodeMode: The node mode of the DWM1001. """
        node_mode_str = self.get_node_mode_str()
        return self.parse_node_mode_str(node_mode_str)

    def parse_node_mode_str(self, node_mode_str: str) -> NodeMode:
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
