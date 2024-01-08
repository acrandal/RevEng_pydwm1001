import os
import sys
import pytest
from unittest import mock
from serial import Serial

# Add module directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import modules under test
from dwm1001 import ParsingError, UartDwm1001, ReservedGPIOPinError

valid_gpio_pins = [2, 8, 9, 10, 12, 13, 14, 15, 23, 27]
invalid_gpio_pins = [0, 1, 3, 4, 5, 6, 7, 11, 16, 17, 18, 19, 20, 21, 22, 24, 25, 26, 28, 29, 30, 31]
example_gpio_get_str_2_LOW = "gpio2: 0"
example_gpio_get_str_2_HIGH = "gpio2: 1"
example_gpio_get_str_14_LOW = "gpio14: 0"
example_gpio_get_str_14_HIGH = "gpio14: 1"

mock_serial = mock.Mock(Serial)
mock_serial.isOpen = lambda: True

# ************************* Begin Tests ************************* #
def test_valid_gpio_pin_numbers():
    node = UartDwm1001(mock_serial)
    for pin in valid_gpio_pins:
        assert node.is_valid_gpio_pin(pin) == True

def test_invalid_gpio_pin_numbers():
    node = UartDwm1001(mock_serial)
    for pin in invalid_gpio_pins:
        assert node.is_valid_gpio_pin(pin) == False

def test_parse_gpio_pin_state_str_2_LOW():
    node = UartDwm1001(mock_serial)
    assert node.parse_gpio_pin_state_str(example_gpio_get_str_2_LOW) == False

def test_parse_gpio_pin_state_str_2_HIGH():
    node = UartDwm1001(mock_serial)
    assert node.parse_gpio_pin_state_str(example_gpio_get_str_2_HIGH) == True

def test_parse_gpio_pin_state_str_14_LOW():
    node = UartDwm1001(mock_serial)
    assert node.parse_gpio_pin_state_str(example_gpio_get_str_14_LOW) == False

def test_parse_gpio_pin_state_str_14_HIGH():
    node = UartDwm1001(mock_serial)
    assert node.parse_gpio_pin_state_str(example_gpio_get_str_14_HIGH) == True

def test_parse_gpio_pin_state_str_invalid():
    node = UartDwm1001(mock_serial)
    with pytest.raises(ParsingError):
        node.parse_gpio_pin_state_str("invalid string")

def test_exception_raised_on_invalid_gpio_pin_number_high():
    node = UartDwm1001(mock_serial)
    with pytest.raises(ReservedGPIOPinError):
        node.set_gpio_pin_high(1)

def test_exception_raised_on_invalid_gpio_pin_number_low():
    node = UartDwm1001(mock_serial)
    with pytest.raises(ReservedGPIOPinError):
        node.set_gpio_pin_low(3)

if __name__ == "__main__":
    pytest.main([__file__])
