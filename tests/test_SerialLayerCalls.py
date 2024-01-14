import os
import sys
import pexpect
import pytest
from unittest import mock
from serial import Serial
from mock_serial import MockSerial
import logging

logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, format="%(levelname)s - %(message)s"
)

shell_timeout_sec = 0.05

# Add module directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import modules under test
from dwm1001.dwm1001 import DWM1001Node, AnchorNodeData, TagPosition, ParsingError
from dwm1001.shell_command import ShellCommand

# ************************* Mock Serial ************************* #
# mock_serial = mock.Mock(Serial)
# mock_serial.isOpen = lambda: True

# ********************* DWM1001 In binary, but fails to shell mode *****#
device_in_binary_mode_no_shell = MockSerial()
device_in_binary_mode_no_shell.open()
device_in_binary_mode_no_shell.stub(
    name="is_in_binary_mode_check",
    receive_bytes=b"a" + ShellCommand.ENTER.value.encode(),
    send_bytes=b"@\x01\x01",
)


# ********************* DWM1001 Node in shell mode ********************* #
device_already_in_shell_mode = MockSerial()
device_already_in_shell_mode.open()
device_already_in_shell_mode.stub(
    name="is_in_shell_mode_check",
    receive_bytes=b"a" + ShellCommand.ENTER.value.encode(),
    send_bytes=b"dwm> ",
)

device_already_in_shell_mode.stub(
    name="reset_command",
    receive_bytes=ShellCommand.RESET.value.encode() + b"\n",
    send_bytes=b"",
)

device_already_in_shell_mode.stub(
    name="system_info_command",
    receive_bytes=ShellCommand.GET_SYSTEM_INFO.value.encode() + b"\n",
    send_bytes=b"System Info Response\r\ndwm> ",
)

# ********************* DWM1001 Node in binary mode ********************* #
device_in_binary_mode = MockSerial()
device_in_binary_mode.open()
device_in_binary_mode.stub(
    name="is_in_binary_mode_check",
    receive_bytes=b"a" + ShellCommand.ENTER.value.encode(),
    send_bytes=b"@\x01\x01",
)

device_in_binary_mode.stub(
    name="enter_shell_mode",
    receive_bytes=ShellCommand.DOUBLE_ENTER.value.encode(),
    send_bytes=b"dwm> ",
)

# *********************************************************************** #
# *********************** Test Cases ************************************ #
# *********************************************************************** #
def test_already_in_shell_mode():
    serial = Serial(device_already_in_shell_mode.port)
    dwm1001node = DWM1001Node(serial)
    assert dwm1001node.is_in_shell_mode() == True


def test_in_binary_mode():
    serial = Serial(device_in_binary_mode.port)
    dwm1001node = DWM1001Node(serial)
    assert dwm1001node.is_in_shell_mode() == False


def test_in_binary_mode_change_to_shell():
    serial = Serial(device_in_binary_mode.port)
    dwm1001node = DWM1001Node(serial)
    dwm1001node.connect()
    assert dwm1001node.is_in_shell_mode() == False


def test_enter_shell_mode():
    serial = Serial(device_already_in_shell_mode.port)
    dwm1001node = DWM1001Node(serial)
    dwm1001node.connect()
    assert dwm1001node.is_in_shell_mode() == True


def test_connect_shell_mode_timeout():
    serial = Serial(device_in_binary_mode_no_shell.port)
    dwm1001node = DWM1001Node(serial, shell_timeout_sec=shell_timeout_sec)
    with pytest.raises(pexpect.exceptions.TIMEOUT):
        dwm1001node.connect()

def test_reset():
    serial = Serial(device_already_in_shell_mode.port)
    dwm1001node = DWM1001Node(serial)
    dwm1001node.connect()
    dwm1001node.reset()
    assert dwm1001node.is_in_shell_mode() == True


def test_disconnect():
    serial = Serial(device_already_in_shell_mode.port)
    dwm1001node = DWM1001Node(serial)
    dwm1001node.disconnect()
    # Just checking that no error is raised - it calls reset

def test_get_uptime_ms():
    expected_uptime_ms = 2673760
    uptime_return_str = (
        "ut\r\n[002673.760 INF] uptime: 00:44:33.760 0 days (2673760 ms)\r\ndwm> "
    )

    device = MockSerial()
    device.open()
    device.stub(
        name="uptime_command",
        receive_bytes=ShellCommand.GET_UPTIME.value.encode() + b"\n",
        send_bytes=uptime_return_str.encode(),
    )

    serial = Serial(device.port)
    dwm1001node = DWM1001Node(serial)
    actual_uptime_ms = dwm1001node.get_uptime_ms()
    assert actual_uptime_ms == expected_uptime_ms


def test_get_system_info():
    serial = Serial(device_already_in_shell_mode.port)
    dwm1001node = DWM1001Node(serial)
    system_info_response = dwm1001node.get_system_info()
    assert system_info_response is not None

def test_get_command_output_timeout():
    device = MockSerial()
    device.open()
    serial = Serial(device.port)
    dwm1001node = DWM1001Node(serial, shell_timeout_sec=shell_timeout_sec)
    with pytest.raises(pexpect.exceptions.TIMEOUT):
        dwm1001node.get_command_output(ShellCommand.GET_UPTIME.value)

def test_is_in_shell_mode_timeout():
    device = MockSerial()
    device.open()
    serial = Serial(device.port)
    dwm1001node = DWM1001Node(serial, shell_timeout_sec=shell_timeout_sec)
    is_in_shell_mode_expected = False
    is_in_shell_mode_actual = dwm1001node.is_in_shell_mode()
    assert is_in_shell_mode_actual == is_in_shell_mode_expected

def test_already_in_shell_mode_when_trying_to_enter_shell_mode():
    serial = Serial(device_already_in_shell_mode.port)
    dwm1001node = DWM1001Node(serial, shell_timeout_sec=shell_timeout_sec)
    dwm1001node.enter_shell_mode()
    # Just checking that no error is raised - it should already be in shell mode




if __name__ == "__main__":
    pytest.main(["-s", __file__])
