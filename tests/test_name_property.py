import pytest

from armctl.dobot import Dobot
from armctl.elephant_robotics import ElephantRobotics, Pro600
from armctl.universal_robots import UR3, UR5, UniversalRobots


@pytest.mark.parametrize(
    "robot_class, init_args, expected",
    [
        (ElephantRobotics, ("192.168.1.1", 5001), "ElephantRobotics"),
        (UniversalRobots, ("192.168.1.1",), "UniversalRobots"),
        (Pro600, (), "ElephantRobotics Pro600"),
        (UR5, ("192.168.1.1",), "UniversalRobots UR5"),
        (UR3, ("192.168.1.1", 30002), "UniversalRobots UR3"),
    ],
)
def test_name_property(robot_class, init_args, expected):
    assert robot_class(*init_args).__name__ == expected


def test_dobot_not_supported():
    with pytest.raises(NotImplementedError):
        Dobot("192.168.1.1", 5001)
