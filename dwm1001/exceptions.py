# Local module defined exceptions
class ParsingError(Exception):
    """! Exception raised when parsing fails for shell command output."""

    pass


class ReservedGPIOPinError(Exception):
    """! Exception raised when trying to use a reserved GPIO pin."""

    pass
