import os
import sys
import pytest
from unittest import mock
from serial import Serial
from mock_serial import MockSerial
import logging

logging.basicConfig(
  stream=sys.stdout,
  level=logging.DEBUG,
  format="%(levelname)s - %(message)s"
)

# Add module directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import modules under test
from dwm1001.dwm1001 import DWM1001Node, AnchorNodeData, TagPosition, ParsingError
from dwm1001.shell_command import ShellCommand

# ************************* Mock Serial ************************* #
#mock_serial = mock.Mock(Serial)
#mock_serial.isOpen = lambda: True

# ********************* DWM1001 Node in shell mode ********************* #
device_already_in_shell_mode = MockSerial()
device_already_in_shell_mode.open()
device_already_in_shell_mode.stub(
        name='is_in_shell_mode_check',
        receive_bytes=b'a' + ShellCommand.ENTER.value.encode(),
        send_bytes=b'dwm> ',
    )

device_already_in_shell_mode.stub(
        name='reset_command',
        receive_bytes=ShellCommand.RESET.value.encode() + b'\n',
        send_bytes=b'',
    )

# ********************* DWM1001 Node in binary mode ********************* #
device_in_binary_mode = MockSerial()
device_in_binary_mode.open()
device_in_binary_mode.stub(
        name='is_in_binary_mode_check',
        receive_bytes=b'a' + ShellCommand.ENTER.value.encode(),
        send_bytes=b'@\x01\x01',
    )

device_in_binary_mode.stub(
        name='enter_shell_mode',
        receive_bytes=ShellCommand.DOUBLE_ENTER.value.encode(),
        send_bytes=b'dwm> ',
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

def test_enter_shell_mode():
    serial = Serial(device_already_in_shell_mode.port)
    dwm1001node = DWM1001Node(serial)
    dwm1001node.connect()
    assert dwm1001node.is_in_shell_mode() == True

def test_reset():
    serial = Serial(device_already_in_shell_mode.port)
    dwm1001node = DWM1001Node(serial)
    dwm1001node.connect()
    dwm1001node.reset()
    assert dwm1001node.is_in_shell_mode() == True


if __name__ == "__main__":
    pytest.main(["-s", __file__])