from dataclasses import dataclass


@dataclass
class AccelerometerData:
    """! Represents the accelerometer data from the DWM1001-DEV module.

    Attributes:
    - x_raw (int): X-axis acceleration.
    - y_raw (int): Y-axis acceleration.
    - z_raw (int): Z-axis acceleration.

    ---

    Measurements come from a ST LIS2DH12TR accelerometer:
    - Documentation: https://www.st.com/resource/en/datasheet/lis2dh12.pdf
    - The LIS2DH12TR can be accessed via TWI/I2C on address 0x33.

    - These values are on a 2g full scale range (by default).
    - To get the acceleration in gravities, divide by 2^6.
    - To get m/s^2, convert to gravities and then multiply by 0.004.

    """

    x_raw: int
    y_raw: int
    z_raw: int
