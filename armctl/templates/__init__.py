"""
This module defines abstract base classes and custom logging levels for robot communication and control.

Classes
-------
Communication : ABC
    Abstract base class for communication protocols with a robot.
Commands : ABC
    Abstract base class for defining robot commands.
"""

from .socket_controller import SocketController
from .serial_controller import SerialController
from .plc_controller import PLCController
from .commands import Commands
