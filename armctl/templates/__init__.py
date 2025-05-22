"""
This module defines abstract base classes and custom logging levels for robot communication and control.

Classes
-------
Communication : ABC
    Abstract base class for communication protocols with a robot.
Commands : ABC
    Abstract base class for defining robot commands.
"""

from .socketcontroller import SocketController
from .serialcontroller import SerialController
from .commands import Commands