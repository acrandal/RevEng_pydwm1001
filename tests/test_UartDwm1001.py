
import os
import sys
import pytest
import serial
from unittest import mock

# Add module directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import modules under test
from dwm1001 import UartDwm1001, AccelerometerData, NodeMode


# ************************* Mock Serial ************************* #
# No one seems to know how to do this properly for pexpect_serial.
# It's a huge mess of mocking and patching, but nothing seems to work.
# This is the best I could come up with where I can still test the parsing, if not the serial communication.

mock_serial = mock.Mock(serial.Serial)
mock_serial.isOpen = lambda: True


# ** System Info example output ** #
system_info_str = """
[036167.230 INF] cfg:
[036167.230 INF] >fw2=x00044000
[036167.230 INF]  board=DWM1001_A2
[036167.230 INF]  cfg_ver=x00010700
[036167.240 INF]  fw_ver=x01010501
[036167.240 INF]  hw_ver=xDECA002A
[036167.240 INF]  opt=x1BC1A040
[036167.250 INF]  fw_size[0]=x0001F000
[036167.250 INF]  fw_size[1]=x00022000
[036167.250 INF]  fw_size[2]=x0003C000
[036167.260 INF]  fw_csum[0]=x9445F89E
[036167.260 INF]  fw_csum[1]=x37A439E0
[036167.260 INF]  fw_csum[2]=xF83EE8A1
[036167.270 INF] opt: ACC TWR LE SEC BPC UWB0 BLE I2C SPI UART 
[036167.270 INF] mcu: temp=26.5 hfclk=xtal:on lfclk=rc:on
[036167.280 INF] uptime: 10:02:47.280 0 days (36167280 ms)
[036167.280 INF] mem: free=1184 alloc=9808 tot=10992
[036167.290 INF] uwb: ch5 prf64 plen128 pac8 txcode9 rxcode9 sfd0 baud6800 phrext sfdto129 smart1
[036167.300 INF] uwb: tx_pwr=xC5/x2B4B6B8B 125:250:500:norm[ms]=20:17:14:11[dB] pgcnt=771 temp=18
[036167.310 INF] uwb0: lna=0 xtaltrim=25 tx_delay=16472 rx_delay=16472
[036167.310 INF] uwb0: ID dev=xDECA0130 part=xC4408830 lot=x013A6102
[036167.320 INF] uwb0: panid=xC7D4 addr=xDECA59CDFA608830
[036167.330 INF] mode: tn (act,twr,np,le)
[036167.330 INF] uwbmac: disconnected
[036167.330 INF] tn: upd_per=100000 upd_per_stat=10000000 us
[036167.340 INF] tn: cnt=0 rtc:hrclk:devt dri=0.000000000:0.000000000:0.000000000 dri_av=0.000000000:0.000000000
[036167.350 INF] ble: addr=E0:E5:D3:0A:19:BE
"""

# ************************* Begin Tests ************************* #
def test_dwm1001_get_uptime_ms():
    expected_uptime_ms = 2673760
    uptime_return_str = (
        "ut\r\n[002673.760 INF] uptime: 00:44:33.760 0 days (2673760 ms)\r\ndwm> "
    )

    dwm1001 = UartDwm1001(mock_serial)

    actual_uptime_ms = dwm1001._parse_uptime_str(uptime_return_str)
    assert actual_uptime_ms == expected_uptime_ms


def test_dwm1001_get_uptime_ms_small():
    expected_uptime_ms = 2670
    uptime_return_str = (
        "ut\r\n[002673.760 INF] uptime: 00:44:33.760 0 days (2670 ms)\r\ndwm> "
    )

    dwm1001 = UartDwm1001(mock_serial)

    actual_uptime_ms = dwm1001._parse_uptime_str(uptime_return_str)
    assert actual_uptime_ms == expected_uptime_ms


def test_parse_get_ble_address():
    expected_ble_address = "E0:E5:D3:0A:19:BE"
    ble_address_return_str = f"si\r\n{system_info_str}\r\ndwm> "

    dwm1001 = UartDwm1001(mock_serial)

    actual_ble_address = dwm1001._parse_ble_address(ble_address_return_str)
    assert actual_ble_address == expected_ble_address


def test_parse_network_id():
    expected_network_id = "xC7D4"
    network_id_return_str = f"si\r\n{system_info_str}\r\ndwm> "

    dwm1001 = UartDwm1001(mock_serial)

    actual_network_id = dwm1001._parse_network_id(network_id_return_str)
    assert actual_network_id == expected_network_id


def test_parse_accelerometer_str():
    expected_accelerometer_data = AccelerometerData(x_raw=-256, y_raw=1424, z_raw=8032)
    accelerometer_return_str = "av\r\nacc: x = -256, y = 1424, z = 8032\r\ndwm> "

    dwm1001 = UartDwm1001(mock_serial)

    actual_accelerometer_data = dwm1001._parse_accelerometer_str(
        accelerometer_return_str
    )
    assert actual_accelerometer_data == expected_accelerometer_data


def test_parse_accelerometer_str_highvals():
    expected_accelerometer_data = AccelerometerData(x_raw=11264, y_raw=-7216, z_raw=-9040)
    accelerometer_return_str = "av\r\nacc: x = 11264, y = -7216, z = -9040\r\ndwm> "

    dwm1001 = UartDwm1001(mock_serial)

    actual_accelerometer_data = dwm1001._parse_accelerometer_str(
        accelerometer_return_str
    )
    assert actual_accelerometer_data == expected_accelerometer_data


def test_parse_node_mode_tag_active():
    expected_node_mode = NodeMode.TAG
    node_mode_return_str = "nmg\r\nmode: tn (act,twr,np,le)\r\ndwm> "

    dwm1001 = UartDwm1001(mock_serial)

    actual_node_mode = dwm1001._parse_node_mode_str(node_mode_return_str)
    assert actual_node_mode == expected_node_mode


def test_parse_node_mode_tag_passive():
    expected_node_mode = NodeMode.TAG
    node_mode_return_str = "nmg\r\nmode: tn (pasv,twr,np,le)\r\ndwm> "

    dwm1001 = UartDwm1001(mock_serial)

    actual_node_mode = dwm1001._parse_node_mode_str(node_mode_return_str)
    assert actual_node_mode == expected_node_mode


def test_parse_node_mode_tag_off():
    expected_node_mode = NodeMode.TAG
    node_mode_return_str = "nmg\r\nmode: tn (off,twr,np,le)\r\ndwm> "

    dwm1001 = UartDwm1001(mock_serial)

    actual_node_mode = dwm1001._parse_node_mode_str(node_mode_return_str)
    assert actual_node_mode == expected_node_mode


if __name__ == "__main__":
    pytest.main([__file__])
