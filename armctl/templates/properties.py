from __future__ import annotations

from abc import ABC
from typing import ClassVar


class Properties(ABC):
    """Base class for robot properties."""

    JOINT_RANGES: ClassVar[list[tuple[float, float]]]
    """Joint position limits for each joint in radians."""

    MAX_JOINT_VELOCITY: ClassVar[float]
    """Max joint velocity in rad/s."""

    MAX_JOINT_ACCELERATION: ClassVar[float]
    """Max joint acceleration in rad/s^2."""

    @property
    def DOF(self) -> int:
        """Degrees of freedom derived from joint ranges."""
        return len(self.JOINT_RANGES)

    @property
    def __name__(self) -> str:
        """Name of the robot.

        Returns:
            - Manufacturer classes: "ManufacturerName"
            - Robot series classes: "ManufacturerName SeriesName"
        """
        # Use type(self) to avoid circular reference with __name__
        class_name = type(self).__name__
        bases = type(self).__bases__

        # Manufacturer class: Properties is 1 level deep
        if any(base.__name__ == "Properties" for base in bases):
            return class_name

        # Robot series class: Properties is 2 levels deep
        for base in bases:
            if any(
                getattr(grandbase, "__name__", "") == "Properties"
                for grandbase in getattr(base, "__bases__", [])
            ):
                return f"{base.__name__} {class_name}"

        return class_name
