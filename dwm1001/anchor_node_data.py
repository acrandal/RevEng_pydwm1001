from dataclasses import dataclass
import re


# Module imports
from .exceptions import ParsingError
from .tag_position import TagPosition


@dataclass
class AnchorNodeData:
    """! Represents an anchor node in the system."""

    id: str
    seat: int
    seens: int
    position: TagPosition

    @staticmethod
    def from_string(anchor_line: str) -> "AnchorNodeData":
        """! Parses a string to create an AnchorData instance."""
        # Example: [003976.620 INF]   0) id=000000000000C920 seat=0 idl=0 seens=40 lqi=0 fl=5001 map=00000000 pos=0.38:0.84:2.15
        # Example: [003976.630 INF]   1) id=0000000000008389 seat=3 idl=0 seens=116 lqi=0 fl=5001 map=00000002 pos=4.96:2.50:1.78
        # Example: [003976.640 INF]   2) id=0000000000000E0B seat=4 idl=0 seens=103 lqi=0 fl=5001 map=00000002 pos=0.64:8.63:1.13
        # pos=0.64:8.63:1.13  # x:y:z
        pattern = r"id=(?P<id>[0-9A-F]+) seat=(?P<seat>\d+) idl=\d+ seens=(?P<seens>\d+) lqi=\d+ fl=\d+ map=\d+ pos=(?P<pos>[0-9.:-]+)"
        match = re.search(pattern, anchor_line)
        if match is None:
            raise ParsingError("Could not parse anchor line.")
        id = match.group("id")
        seat = int(match.group("seat"))
        seens = int(match.group("seens"))
        position_str = match.group("pos")
        x_str, y_str, z_str = position_str.split(":")
        position = TagPosition(float(x_str), float(y_str), float(z_str), 0)
        return AnchorNodeData(id, seat, seens, position)
