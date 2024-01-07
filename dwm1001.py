# Standard library imports
from dataclasses import dataclass
from enum import Enum
import math
import time
from typing import Tuple
import logging

# Third party imports
from serial import Serial
import pexpect_serial
import pexpect


class TagId(str):
    pass


class TagName(str):
    pass


@dataclass
class TagPosition:
    x_m: float
    y_m: float
    z_m: float
    quality: int

    def is_almost_equal(self, other: "TagPosition") -> bool:
        return (
            math.isclose(self.x_m, other.x_m)
            and math.isclose(self.y_m, other.y_m)
            and math.isclose(self.z_m, other.z_m)
        )
    
    def __eq__(self, other: "TagPosition") -> bool:
        return (
            self.x_m == other.x_m
            and self.y_m == other.y_m
            and self.z_m == other.z_m
        )


@dataclass
class SystemInfo:
    uwb_address: str
    label: str

    @staticmethod
    def from_string(data: str) -> "SystemInfo":
        data_lines = data.splitlines()

        uwb_address_line = data_lines[1].strip()
        address_text_start = uwb_address_line.find("addr=")
        address_string = "0" + uwb_address_line[address_text_start + len("addr=") :]

        label_line = data_lines[5].strip()
        label_text_start = label_line.find("label=")
        label_string = label_line[label_text_start + len("label=") :]

        return SystemInfo(uwb_address=address_string, label=label_string)


class ShellCommand(Enum):
    ENTER = '\r'
    DOUBLE_ENTER = '\r\r'
    RESET = 'reset'
    SI = "si"  # System info
    GET_UPTIME = "ut"  # Uptime


class ParsingError(Exception):
    pass


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
        self.pexpect_handle = pexpect_serial.SerialSpawn(self.serial_handle, timeout=self.SHELL_TIMEOUT_PERIOD_SEC)

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
        self.pexpect_handle.before = ""     # Clear buffer

    def disconnect(self) -> None:
        self.log.debug("Disconnecting from DWM1001.")
        self.exit_shell_mode()
        self.pexpect_handle.close()

    def get_uptime_ms(self) -> int:
        uptime_ms = 0
        uptime_str = self.get_command_output(ShellCommand.GET_UPTIME.value)
        _, right = uptime_str.split(" (")
        uptime_ms_str, _ = right.split(" ms")
        uptime_ms = int(uptime_ms_str)
        return uptime_ms
    
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
            result_index = self.pexpect_handle.expect([self.BINARY_MODE_RESPONSE, self.SHELL_PROMPT], timeout=1)
            if result_index == 0:
                return False
            elif result_index == 1:
                return True
        except pexpect.exceptions.TIMEOUT:
            self.log.warning('Timeout while checking is in shell mode.')
            return False

    def enter_shell_mode(self) -> None:
        if self.is_in_shell_mode(): # Protect if already in shell mode
            self.log.debug("Already in shell mode.")
            return

        self.log.debug("Entering shell mode.")
        self.pexpect_handle.send(ShellCommand.DOUBLE_ENTER.value)
        try:
            self.pexpect_handle.expect(self.SHELL_PROMPT) # Wait for shell prompt
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

