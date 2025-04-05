"""
This module provides an interface for controlling various robotic arms from different manufacturers.

Supported Manufacturers and Robot Series:
- Dobot:

- Elephant Robotics:
    - myCobot Pro600 (Ethernet)

- Universal Robotics:
    - UR5 (Ethernet)

- Fanuc:

- Vention:

"""

from .dobot import Dobot
from .elephant_robotics import ElephantRobotics, Pro600
from .universal_robotics import UniversalRobotics, UR5
from .fanuc import Fanuc
from .vention import Vention
from .manipulators import OnRobot