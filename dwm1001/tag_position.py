from dataclasses import dataclass
import math
import re

# Module imports
from dwm1001.exceptions import ParsingError


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

        - Example apg position line: x:0 y:0 z:0 qf:0
        - Example apg position line: x:10 y:78888 z:-334 qf:57
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

    def get_as_tuple(self) -> tuple:
        """! Gets the position as a tuple of floats.
        @return tuple[float, float, float]: The position as a tuple of floats.
        """
        return (self.x_m, self.y_m, self.z_m)

    def get_as_list(self) -> list:
        """! Gets the position as a list of floats.
        @return list[float]: The position as a list of floats.

        NOTE: Very useful for creating a numpy array for 3D operations.
        """
        return [self.x_m, self.y_m, self.z_m]
