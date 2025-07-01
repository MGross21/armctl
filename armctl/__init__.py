"""
armctl
======

A unified interface for controlling robotic arms from multiple manufacturers.

Supported Manufacturers and Robots:
- Elephant Robotics: myCobot Pro600 (Ethernet)
- Universal Robotics: UR5, UR5e (Ethernet)
    - Grippers: OnRobot (Ethernet)
- Vention (Ethernet)
- Jaka Robotics: Jaka (Ethernet)
"""

# from .dobot import Dobot
from .elephant_robotics import ElephantRobotics, Pro600
from .universal_robotics import UniversalRobotics, UR5, UR5e, OnRobot
# from .fanuc import Fanuc
from .vention import Vention
from .jaka import Jaka
from .diy_robot import DIYRobot

__all__ = [
    "ElephantRobotics",
    "Pro600",

    "UniversalRobotics",
    "UR5",
    "UR5e",
    "OnRobot",

    "Vention",
    "Jaka",
    "DIYRobot",
]