import pytest

from armctl.dobot import Dobot
from armctl.elephant_robotics import ElephantRobotics, Pro600
from armctl.fanuc import Fanuc
from armctl.jaka import Jaka
from armctl.templates import (
    Commands,
    PLCController,
    Properties,
    SerialController,
    SocketController,
)
from armctl.universal_robots import UR3, UR5, UR10, UR16, UniversalRobots, UR5e
from armctl.vention import Vention
from armctl.zaber import Zaber

ROBOTS = [
    Dobot,
    ElephantRobotics,
    Pro600,
    Jaka,
    UR3,
    UR5,
    UR5e,
    UR10,
    UR16,
    UniversalRobots,
    Vention,
    Fanuc,
]
CONTROLLERS = (SerialController, SocketController, PLCController)


INCOMPLETE = pytest.mark.xfail(reason="Fanuc driver does not implement sleep", strict=True)


@pytest.mark.parametrize(
    "robot",
    [pytest.param(r, marks=INCOMPLETE) if r is Fanuc else r for r in [*ROBOTS, Zaber]],
    ids=lambda r: r.__name__,
)
def test_implements_commands_and_properties(robot):
    assert issubclass(robot, Commands)
    assert issubclass(robot, Properties)
    assert not getattr(robot, "__abstractmethods__", None)


@pytest.mark.parametrize("robot", ROBOTS, ids=lambda r: r.__name__)
def test_uses_a_controller(robot):
    assert issubclass(robot, CONTROLLERS)
