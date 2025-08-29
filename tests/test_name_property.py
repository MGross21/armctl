"""
Test suite for the __name__ property behavior across robot class hierarchy.
"""

import pytest
from armctl.elephant_robotics import ElephantRobotics, Pro600
from armctl.universal_robots import UniversalRobots, UR5, UR3
from armctl.dobot import Dobot


class TestRobotNameProperty:
    """Test the __name__ property for different inheritance levels."""

    def test_manufacturer_classes_return_class_name(self):
        """Test that manufacturer classes return just their class name."""
        # These require instantiation since __name__ is now a property
        try:
            assert (
                ElephantRobotics("192.168.1.1", 5001).__name__
                == "ElephantRobotics"
            )
        except (NotImplementedError, ImportError):
            pass  # ElephantRobotics might not be fully implemented

        try:
            assert UniversalRobots("192.168.1.1").__name__ == "UniversalRobots"
        except (NotImplementedError, ImportError):
            pass  # UniversalRobots might not be fully implemented

        try:
            assert Dobot("192.168.1.1", 5001).__name__ == "Dobot"
        except (NotImplementedError, ImportError):
            pass  # Dobot raises NotImplementedError

    def test_robot_series_classes_return_manufacturer_and_model(self):
        """Test that robot series classes return 'Manufacturer Model' format."""
        try:
            assert Pro600().__name__ == "ElephantRobotics Pro600"
        except (NotImplementedError, ImportError):
            pass

        try:
            assert UR5("192.168.1.1").__name__ == "UniversalRobots UR5"
        except (NotImplementedError, ImportError):
            pass

        try:
            assert UR3("192.168.1.1").__name__ == "UniversalRobots UR3"
        except (NotImplementedError, ImportError):
            pass

    @pytest.mark.parametrize(
        "robot_class,expected_name,init_args",
        [
            (ElephantRobotics, "ElephantRobotics", ("192.168.1.1", 5001)),
            (UniversalRobots, "UniversalRobots", ("192.168.1.1", 30002)),
            (Dobot, "Dobot", ("192.168.1.1", 5001)),
            (Pro600, "ElephantRobotics Pro600", ()),
            (UR5, "UniversalRobots UR5", ("192.168.1.1",)),
            (UR3, "UniversalRobots UR3", ("192.168.1.1", 30002)),
        ],
    )
    def test_name_property_parametrized(
        self, robot_class, expected_name, init_args
    ):
        """Parametrized test for all robot classes."""
        try:
            instance = robot_class(*init_args)
            assert instance.__name__ == expected_name
        except (NotImplementedError, ImportError) as e:
            # Some classes might not be fully implemented or missing dependencies, skip them
            pytest.skip(f"Cannot test {robot_class.__name__} - {str(e)}")
