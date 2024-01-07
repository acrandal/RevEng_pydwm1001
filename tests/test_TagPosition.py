import os
import sys
import pytest

# Add module directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import modules under test
from dwm1001 import TagPosition, ParsingError


# ************************* Begin Tests ************************* #
def test_construction():
    position = TagPosition(1.23, 4.56, 7.89, 42)

    assert position.x_m == 1.23
    assert position.y_m == 4.56
    assert position.z_m == 7.89
    assert position.quality == 42


def test_from_string_zeros():
    apg_line = "x:0 y:0 z:0 qf:0"
    position = TagPosition.from_string(apg_line)

    assert position.x_m == 0
    assert position.y_m == 0
    assert position.z_m == 0
    assert position.quality == 0


def test_from_string_advanced():
    apg_line = "x:10 y:78888 z:-334 qf:57"
    position = TagPosition.from_string(apg_line)

    assert position.x_m == 0.010
    assert position.y_m == 78.888
    assert position.z_m == -0.334
    assert position.quality == 57


def test_from_string_invalid():
    apg_line = "invalid line garbage"
    with pytest.raises(ParsingError):
        TagPosition.from_string(apg_line)


def test_exact_equality():
    position1 = TagPosition(1.23, 4.56, 7.89, 42)
    position2 = TagPosition(1.23, 4.56, 7.89, 42)

    assert position1 == position2


def test_almost_equality_equal():
    position1 = TagPosition(1.23, 4.56, 7.89, 42)
    position2 = TagPosition(1.2301, 4.5601, 7.8901, 42)

    assert position1.is_almost_equal(position2)


def test_almost_equality_not_equal():
    position1 = TagPosition(1.23, 4.56, 7.89, 42)
    position2 = TagPosition(1.251, 4.561, 7.891, 42)

    assert not position1.is_almost_equal(position2)


if __name__ == "__main__":
    pytest.main([__file__])
