from armctl.dobot import Dobot
from armctl.elephant_robotics import ElephantRobotics, Pro600
from armctl.fanuc import Fanuc
from armctl.jaka import Jaka
from armctl.templates import Commands, Properties, PLCController, SerialController, SocketController
from armctl.universal_robots import UR3, UR5, UR5e, UR10, UR16, UniversalRobots
from armctl.vention import Vention

# All robot classes that should inherit from Commands and a controller
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

# Required base classes
REQUIRED_BASES = (Commands, Properties)
CONTROLLER_BASES = (SerialController, SocketController, PLCController)


def test_robot_subclass_inheritance():
    """Test that all robot classes inherit from Commands and at least one controller."""
    for robot in ROBOTS:
        # Check required base class inheritance
        for base in REQUIRED_BASES:
            assert issubclass(robot, base), (
            f"{robot.__name__} must inherit from {base.__name__}"
            )

        # Check controller inheritance
        has_controller = any(issubclass(robot, c) for c in CONTROLLER_BASES)
        assert has_controller, (
            f"{robot.__name__} must inherit from at least one controller: "
            f"{', '.join(c.__name__ for c in CONTROLLER_BASES)}"
        )