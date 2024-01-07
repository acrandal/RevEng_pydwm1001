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
    pass


class ShellCommand(Enum):
    # Commands for the DWM1001 shell interface
    ENTER = "\r"
    DOUBLE_ENTER = "\r\r"
    RESET = "reset"
    GET_SYSTEM_INFO = "si"  # System info
    GET_UPTIME = "ut"  # Uptime
    GET_POSITION = "apg"  # Get position
    GET_ACCELEROMETER = "av"  # Get accelerometer data
    GET_MODE = "nmg"  # Get node mode: tag, anchor


class NodeMode(Enum):
    # Node Modes
    TAG = "tag"
    ANCHOR = "anchor"
    ANCHOR_INITIATOR = "anchor initiator"


@dataclass
class TagPosition:
    # Coordinates are in meters
    x_m: float
    y_m: float
    z_m: float
    quality: int

    def is_almost_equal(self, other: "TagPosition", rel_tol_m=0.01) -> bool:
        return (
            math.isclose(self.x_m, other.x_m, rel_tol=rel_tol_m)
            and math.isclose(self.y_m, other.y_m, rel_tol=rel_tol_m)
            and math.isclose(self.z_m, other.z_m, rel_tol=rel_tol_m)
        )

    def __eq__(self, other: "TagPosition") -> bool:
        return self.x_m == other.x_m and self.y_m == other.y_m and self.z_m == other.z_m

    @staticmethod
    def from_string(apg_line: str) -> "TagPosition":
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
    x: int
    y: int
    z: int


class UartDwm1001:
    # These delay periods were experimentally determined
    RESET_DELAY_PERIOD = 0.1
    SHELL_STARTUP_DELAY_PERIOD = 1.0
    SHELL_TIMEOUT_PERIOD_SEC = 3.0

    SHELL_PROMPT = "dwm> "
    BINARY_MODE_RESPONSE = "@\x01\x01"

    def __init__(self, serial_handle: Serial) -> None:
        self.log = logging.getLogger(__class__.__name__)
        self.serial_handle = serial_handle
        self.pexpect_handle = pexpect_serial.SerialSpawn(
            self.serial_handle, timeout=self.SHELL_TIMEOUT_PERIOD_SEC
        )

    def connect(self) -> None:
        if not self.is_in_shell_mode():
            self.log.debug("Not in shell mode, initializing shell.")
            try:
                self.enter_shell_mode()
            except pexpect.exceptions.TIMEOUT:
                self.log.warn("Connect failed.")
                raise pexpect.exceptions.TIMEOUT
        else:
            self.log.debug("Already in shell mode.")
        serial_port_path = self.serial_handle.name
        self.log.info(f"Connected to DWM1001 on: {serial_port_path}")
        self.clear_pexpect_buffer()

    def clear_pexpect_buffer(self) -> None:
        self.pexpect_handle.before = ""  # Clear buffer

    def disconnect(self) -> None:
        self.log.debug("Disconnecting from DWM1001.")
        self.exit_shell_mode()
        self.pexpect_handle.close()

    def get_uptime_ms(self) -> int:
        uptime_str = self.get_command_output(ShellCommand.GET_UPTIME.value)
        return self.parse_uptime_str(uptime_str)

    def parse_uptime_str(self, uptime_str: str) -> int:
        _, right = uptime_str.split(" (")
        uptime_ms_str, _ = right.split(" ms")
        uptime_ms = int(uptime_ms_str)
        return uptime_ms

    def get_system_info(self) -> str:
        system_info_str = self.get_command_output(ShellCommand.GET_SYSTEM_INFO.value)
        return system_info_str

    def get_command_output(self, command: ShellCommand) -> str:
        try:
            self.pexpect_handle.sendline(command)
            self.pexpect_handle.expect(self.SHELL_PROMPT)
            command_output = self.pexpect_handle.before.decode().strip()
        except pexpect.exceptions.TIMEOUT:
            self.log.warning(f"Timeout on command: {command}")
            raise pexpect.exceptions.TIMEOUT
        return command_output

    def reset(self) -> None:
        self.pexpect_handle.sendline(ShellCommand.RESET.value)
        time.sleep(self.RESET_DELAY_PERIOD)

    def is_in_shell_mode(self) -> bool:
        self.pexpect_handle.send("a" + ShellCommand.ENTER.value)
        try:
            result_index = self.pexpect_handle.expect(
                [self.BINARY_MODE_RESPONSE, self.SHELL_PROMPT], timeout=1
            )
            if result_index == 0:
                return False
            elif result_index == 1:
                return True
        except pexpect.exceptions.TIMEOUT:
            self.log.warning("Timeout while checking is in shell mode.")
            return False

    def enter_shell_mode(self) -> None:
        if self.is_in_shell_mode():  # Protect if already in shell mode
            self.log.debug("Already in shell mode.")
            return

        self.log.debug("Entering shell mode.")
        self.pexpect_handle.send(ShellCommand.DOUBLE_ENTER.value)
        try:
            self.pexpect_handle.expect(self.SHELL_PROMPT)  # Wait for shell prompt
        except pexpect.exceptions.TIMEOUT:
            self.log.warning("Timeout while entering shell mode.")
            raise pexpect.exceptions.TIMEOUT
        self.log.debug("Entered shell mode.")

    def exit_shell_mode(self) -> None:
        # If you quit shell mode (with `quit` command) without stopping
        # a running command, the command will automatically continue
        # when re-entering shell mode. This can be confusing, so we
        # reset the device instead to ensure previously-running commands
        # terminate.
        self.reset()

    def get_position(self) -> TagPosition:
        location_str = self.get_command_output(ShellCommand.GET_POSITION.value)
        location = TagPosition.from_string(location_str)
        return location

    def get_ble_address(self) -> str:
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
            x=int(match.group("x")), y=int(match.group("y")), z=int(match.group("z"))
        )

    def get_node_mode_str(self) -> str:
        node_mode_str = self.get_command_output(ShellCommand.GET_MODE.value)
        return node_mode_str

    def is_in_tag_mode(self) -> bool:
        node_mode_str = self.get_node_mode_str()
        return self.parse_node_mode_str(node_mode_str) == NodeMode.TAG

    def is_in_anchor_mode(self) -> bool:
        node_mode_str = self.get_node_mode_str()
        return self.parse_node_mode_str(node_mode_str) == NodeMode.ANCHOR

    def is_in_anchor_initiator_mode(self) -> bool:
        node_mode_str = self.get_node_mode_str()
        return self.parse_node_mode_str(node_mode_str) == NodeMode.ANCHOR_INITIATOR

    def get_node_mode(self) -> NodeMode:
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
