"""Universal Robots series robot implementations."""

from __future__ import annotations

import math

from .universal_robots import UniversalRobots as UR


class UR3(UR):
    """Universal Robots UR3 robot controller."""

    def __init__(self, ip: str, port: int = 30_002):
        super().__init__(ip, port)
        self.HOME_POSITION = [
            math.pi / 2,
            -math.pi / 2,
            math.pi / 2,
            -math.pi / 2,
            -math.pi / 2,
            0,
        ]

    def home(self, speed: float = 0.1) -> None:
        """Move robot to home position."""
        self.move_joints(self.HOME_POSITION, speed=speed)


class UR5(UR):
    """Universal Robots UR5 robot controller."""

    def __init__(self, ip: str, port: int = 30_002):
        super().__init__(ip, port)
        self.HOME_POSITION = [
            math.pi / 2,
            -math.pi / 2,
            math.pi / 2,
            -math.pi / 2,
            -math.pi / 2,
            0,
        ]

    def home(self, speed: float = 0.1) -> None:
        """Move robot to home position."""
        self.move_joints(self.HOME_POSITION, speed=speed)


class UR5e(UR):
    """Universal Robots UR5e robot controller."""

    def __init__(self, ip: str, port: int = 30_002):
        super().__init__(ip, port)
        self.HOME_POSITION = [
            math.pi / 2,
            -math.pi / 2,
            math.pi / 2,
            -math.pi / 2,
            -math.pi / 2,
            0,
        ]

    def home(self, speed: float = 0.1) -> None:
        """Move robot to home position."""
        self.move_joints(self.HOME_POSITION, speed=speed)


class UR10(UR):
    """Universal Robots UR10 robot controller."""

    def __init__(self, ip: str, port: int = 30_002):
        super().__init__(ip, port)
        self.HOME_POSITION = [
            math.pi / 2,
            -math.pi / 2,
            math.pi / 2,
            -math.pi / 2,
            -math.pi / 2,
            0,
        ]

    def home(self, speed: float = 0.1) -> None:
        """Move robot to home position."""
        self.move_joints(self.HOME_POSITION, speed=speed)


class UR16(UR):
    """Universal Robots UR16 robot controller."""

    def __init__(self, ip: str, port: int = 30_002):
        super().__init__(ip, port)
        self.HOME_POSITION = [
            math.pi / 2,
            -math.pi / 2,
            math.pi / 2,
            -math.pi / 2,
            -math.pi / 2,
            0,
        ]

    def home(self, speed: float = 0.1) -> None:
        """Move robot to home position."""
        self.move_joints(self.HOME_POSITION, speed=speed)
