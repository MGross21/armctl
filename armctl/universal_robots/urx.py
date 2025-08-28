"""Universal Robots URX series robot implementations."""

import math
from dataclasses import dataclass

from .universal_robots import UniversalRobots as UR


@dataclass
class URX(UR):
    """Base class for Universal Robots URX series with common functionality."""

    HOME_POSITION: list[float] = (
        math.pi / 2,
        -math.pi / 2,
        math.pi / 2,
        -math.pi / 2,
        -math.pi / 2,
        0,
    )

    def home(self, speed: float = 0.1) -> None:
        """Move robot to home position."""
        self.move_joints(self.HOME_POSITION, speed=speed)


class UR3(URX):
    """Universal Robots UR3 robot controller."""

    def __init__(self, ip: str, port: int = 30_002):
        super().__init__(ip, port)


class UR5(URX):
    """Universal Robots UR5 robot controller."""

    def __init__(self, ip: str = "192.168.1.111", port: int = 30_002):
        super().__init__(ip, port)


class UR5e(URX):
    """Universal Robots UR5e robot controller."""

    def __init__(self, ip: str = "192.168.1.111", port: int = 30_002):
        super().__init__(ip, port)


class UR10(URX):
    """Universal Robots UR10 robot controller."""

    def __init__(self, ip: str, port: int = 30_002):
        super().__init__(ip, port)


class UR16(URX):
    """Universal Robots UR16 robot controller."""

    def __init__(self, ip: str, port: int = 30_002):
        super().__init__(ip, port)
