"""
armctl
======

A unified interface for controlling robotic arms from multiple manufacturers.

"""

# from .dobot import Dobot
from .elephant_robotics import ElephantRobotics, Pro600
from .jaka import Jaka
from .universal_robots import (
    UR3,
    UR5,
    UR10,
    UR16,
    OnRobot,
    UniversalRobots,
    UR5e,
)

# from .fanuc import Fanuc
from .vention import Vention

__all__ = [
    "ElephantRobotics",
    "Pro600",
    "UniversalRobots",
    "UR3",
    "UR5",
    "UR5e",
    "UR10",
    "UR16",
    # "OnRobot",
    "Vention",
    "Jaka",
]

__version__ = "0.3.4"


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


import os

if os.environ.get("ARMCTL_LOG", "").lower() in {"0", "false", "disable"}:
    Logger.disable()
