"""
armctl
=======

This module provides a unified interface for controlling robotic arms from multiple manufacturers.

Supported Manufacturers and Robot Series:
- Dobot

- Elephant Robotics:
    - myCobot Pro600 (Ethernet)

- Universal Robotics:
    - UR5 (Ethernet)
    - UR5e (Ethernet)

    Grippers:
    - OnRobot (Ethernet)

- Fanuc

- Vention
"""

from .dobot import Dobot
from .elephant_robotics import ElephantRobotics, Pro600
from .universal_robotics import UniversalRobotics, UR5, UR5e, OnRobot
from .fanuc import Fanuc
from .vention import Vention

__all__ = [
    "Dobot",

    "ElephantRobotics",
    "Pro600",

    "UniversalRobotics",
    "UR5",
    "UR5e",
    "OnRobot",

    "Fanuc",

    "Vention",
]