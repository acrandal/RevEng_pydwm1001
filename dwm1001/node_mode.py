from enum import Enum


class NodeMode(Enum):
    """! DWM1001 Node Modes"""

    TAG = "tag"
    ANCHOR = "anchor"
    ANCHOR_INITIATOR = "anchor initiator"
