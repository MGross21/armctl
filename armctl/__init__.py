"""
armctl
======

A unified interface for controlling robotic arms from multiple manufacturers.

Supported Manufacturers and Robots:
- Elephant Robotics: myCobot Pro600 (Ethernet)
- Universal Robotics: UR3, UR5, UR5e, UR10, UR16 (Ethernet)
    - Grippers: OnRobot (Ethernet)
- Vention (Ethernet)
- Jaka Robotics: Jaka (Ethernet)
"""

# from .dobot import Dobot
from .elephant_robotics import ElephantRobotics, Pro600
from .universal_robotics import UniversalRobotics, UR3, UR5, UR5e, UR10, UR16, OnRobot

# from .fanuc import Fanuc
from .vention import Vention
from .jaka import Jaka

__all__ = [
    "ElephantRobotics",
    "Pro600",
    "UniversalRobotics",
    "UR5",
    "UR5e",
    "OnRobot",
    "Vention",
    "Jaka",
    "Logger",
]


class Logger:
    """Global logger utility for armctl."""

    @staticmethod
    def disable():
        """Disables logging."""
        import logging

        # Disable all logging at and below the CRITICAL level
        logging.disable(logging.CRITICAL)

    @staticmethod
    def enable():
        """Enables logging."""
        import logging

        # Re-enable logging to its previous state
        logging.disable(logging.NOTSET)
