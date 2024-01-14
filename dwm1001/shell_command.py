from enum import Enum


class ShellCommand(Enum):
    """! Commands for the DWM1001 shell interface."""

    ENTER = "\r"
    DOUBLE_ENTER = "\r\r"
    RESET = "reset"
    GET_SYSTEM_INFO = "si"  # System info
    GET_UPTIME = "ut"  # Uptime
    GET_POSITION = "apg"  # Get position
    GET_ACCELEROMETER = "av"  # Get accelerometer data
    GET_MODE = "nmg"  # Get node mode: tag, anchor
    GET_ANCHOR_LIST = "la"  # Get list of currently seen anchors
    GPIO_CLEAR = "gc"  # Set GPIO pin LOW
    GPIO_SET = "gs"  # Set GPIO pin HIGH
    GPIO_GET = "gg"  # Get GPIO pin value
