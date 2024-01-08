# Introduction

This is a Python library for interfacing with the Qorvo (previously Decawave) DWM1001.

## Hardware Components

Hardware needed is the DWM1001 product line from Qorvo:
- https://www.qorvo.com/products/p/DWM1001-DEV
- https://www.qorvo.com/products/p/DWM1001C

The primary testing is done with the DWM1001-DEV platform through the serial interfaces, both RS232 and USB to serial chip interface.

The DWM1001 system overview documentation is available here: https://www.qorvo.com/products/d/da007974 

## Software Components

This is a Python3 wrapper/driver for the DWM1001 serial interface.
It is designed to provide a subset of the full interface, with a focus on reading location data more than configuring the boards.
To configure the devices, the Android app is likely the better choice.

To use the serial interface, the commands in pydwm1001 are being executed in the shell interface, which is a subset of the more complete firmware interface available over the serial interface.
The Qorvo supplied C library uses the firmware interface as documented here: https://www.qorvo.com/products/d/da007975 

This library should work on Linux, OSX, and Windows.
Additionally, it should work on Raspberry Pi, Orange Pi, NanoPI, and other similar SOC boards via the serial interface on pins 6, 8, and 10 of the Raspberry Pi GPIO header.

### Contributors and Library History

- Adam Morrissett \<morrissettal2@vcu.edu>
- Aaron S. Crandall \<crandall@gonzaga.edu>

