import os
import sys
import pytest
from unittest import mock
from serial import Serial

# Add module directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import modules under test
from dwm1001 import ParsingError, UartDwm1001, AnchorNodeData, TagPosition

mock_serial = mock.Mock(Serial)
mock_serial.isOpen = lambda: True

anchor_data_0 = "[003976.620 INF]   0) id=000000000000C920 seat=0 idl=0 seens=40 lqi=0 fl=5001 map=00000000 pos=0.38:0.84:2.15"
anchor_data_1 = "[003976.630 INF]   1) id=0000000000008389 seat=3 idl=0 seens=116 lqi=0 fl=5001 map=00000002 pos=114.96:2.50:-1.78"
anchor_data_2 = "[003976.640 INF]   2) id=0000000000000E0B seat=14 idl=0 seens=2103 lqi=0 fl=5001 map=00000002 pos=-0.0:-8000.63:-1.13"

list_anchors_str = """[005899.170 INF] AN: cnt=4 seq=x09
[005899.170 INF]   0) id=000000000000C920 seat=0 idl=0 seens=75 lqi=0 fl=5001 map=00000000 pos=0.38:0.84:2.15
[005899.180 INF]   1) id=0000000000008389 seat=3 idl=0 seens=42 lqi=0 fl=5001 map=00000001 pos=4.96:2.50:1.78
[005899.190 INF]   2) id=0000000000000E0B seat=4 idl=0 seens=32 lqi=0 fl=5001 map=00000001 pos=0.64:8.63:1.13
[005899.200 INF]   3) id=0000000000004505 seat=1 idl=0 seens=196 lqi=0 fl=5001 map=00000001 pos=5.14:9.03:1.35
[005899.210 INF]"""

list_anchors_str_0 = """[005899.170 INF] AN: cnt=0 seq=x09"""
list_anchors_str_4 = """[005899.170 INF] AN: cnt=4 seq=xA9"""
list_anchors_str_13 = """[005899.170 INF] AN: cnt=13 seq=x06"""

# ************************* Begin Tests ************************* #
def test_anchor_node_constructor_0():
    anchor_node = AnchorNodeData.from_string(anchor_data_0)
    assert anchor_node.id == "000000000000C920"
    assert anchor_node.seat == 0
    assert anchor_node.seens == 40
    assert anchor_node.position == TagPosition(0.38, 0.84, 2.15, 0)

def test_anchor_node_constructor_1():
    anchor_node = AnchorNodeData.from_string(anchor_data_1)
    assert anchor_node.id == "0000000000008389"
    assert anchor_node.seat == 3
    assert anchor_node.seens == 116
    assert anchor_node.position == TagPosition(114.96,2.50,-1.78,0)

def test_anchor_node_constructor_2():
    anchor_node = AnchorNodeData.from_string(anchor_data_2)
    assert anchor_node.id == "0000000000000E0B"
    assert anchor_node.seat == 14
    assert anchor_node.seens == 2103
    assert anchor_node.position == TagPosition(-0.0,-8000.63,-1.13,0)

def test_list_anchors_command():
    dwm1001node = UartDwm1001(mock_serial)
    anchor_list = dwm1001node._parse_anchor_list_str(list_anchors_str)

    assert len(anchor_list) == 4
    assert anchor_list[0].id == "000000000000C920"
    assert anchor_list[0].seat == 0
    assert anchor_list[1].id == "0000000000008389"
    assert anchor_list[1].seens == 42
    assert anchor_list[2].id == "0000000000000E0B"
    assert anchor_list[3].id == "0000000000004505"

def test_list_anchors_command_0():
    dwm1001node = UartDwm1001(mock_serial)
    anchor_list = dwm1001node._parse_anchor_list_str(list_anchors_str_0)

    assert len(anchor_list) == 0

def test_get_seen_anchor_count_0():
    expected_anchor_count = 0
    dwm1001node = UartDwm1001(mock_serial)
    anchor_count = dwm1001node._parse_anchors_seen_count_str(list_anchors_str_0)

    assert anchor_count == expected_anchor_count

def test_get_seen_anchor_count_4():
    expected_anchor_count = 4
    dwm1001node = UartDwm1001(mock_serial)
    anchor_count = dwm1001node._parse_anchors_seen_count_str(list_anchors_str_4)

    assert anchor_count == expected_anchor_count

def test_get_seen_anchor_count_13():
    expected_anchor_count = 13
    dwm1001node = UartDwm1001(mock_serial)
    anchor_count = dwm1001node._parse_anchors_seen_count_str(list_anchors_str_13)

    assert anchor_count == expected_anchor_count

def test_construct_invalid_string_1():
    invalid_string = "Invalid String Input"
    with pytest.raises(ParsingError):
        AnchorNodeData.from_string(invalid_string)

def test_invalid_anchor_count_parse():
    invalid_string = "Invalid String Input"
    dwm1001node = UartDwm1001(mock_serial)
    with pytest.raises(ParsingError):
        dwm1001node._parse_anchors_seen_count_str(invalid_string)
