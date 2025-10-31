"""Blank Robot Module

This module provides a template for creating a robot controller with various connection methods.

Usage:
1. Choose your communication method by uncommenting the appropriate import
2. Implement the required methods for your specific robot
3. Customize the connection parameters in __init__ if needed

Communication Methods:
- PLCController: For PLC-based communication
- SocketController: For TCP/UDP socket communication
- SerialController: For serial port communication
"""

# Universal Imports
from __future__ import annotations

import atexit
import math

from armctl.templates import Commands, Properties

# Choose one of the following Communication Methods
# Uncomment the one you need and comment out the others
from armctl.templates import SocketController as Communication
from armctl.utils import CommandCheck as cc

# from armctl.templates import PLCController as Communication
# from armctl.templates import SerialController as Communication


class BlankRobot(Communication, Commands, Properties):
    def __init__(self, **kwargs):
        # Initialize connection parameters from kwargs
        # The specific parameters depend on which communication method you choose:
        # For SerialController: port, baud
        # For SocketController/PLCController: ip, port
        super().__init__(**kwargs)

        # Define Properties
        self.JOINT_RANGES: list[tuple[float, float]] = [
            (-math.pi, math.pi) for _ in range(6)
        ]
        self.MAX_JOINT_VELOCITY: float | None = None
        self.MAX_JOINT_ACCELERATION: float | None = None

    def connect(self):
        super().connect()  # Call first to ensure base connection logic is executed
        # Additional connection logic can be added here if needed

    @atexit.register
    def disconnect(self):
        # Additional disconnection logic can be added here if needed
        super().disconnect()  # Call last to ensure base disconnection logic is executed

    def sleep(self, seconds: float) -> None:
        """Sleep for the specified number of seconds."""
        cc.sleep(seconds)
        # Additional sleep logic can be added here if needed
        # Send sleep command to robot
        pass

    def move_joints(self, pos: list[float]) -> None:
        """Move robot joints to specified positions (in radians or degrees)."""
        cc.move_joints(pos)
        # Additional move logic can be added here if needed
        # Send move command to robot
        pass

    def get_joint_positions(self) -> list[float]:
        """Get current joint positions."""
        cc.get_joint_positions()
        # Additional get logic can be added here if needed
        # Return the joint positions
        pass

    def move_cartesian(self, pose: list[float]) -> None:
        """Move robot to specified cartesian pose [x, y, z, rx, ry, rz]."""
        cc.move_cartesian(pose)
        # Additional move logic can be added here if needed
        # Send move command to robot
        pass

    def get_cartesian_position(self) -> list[float]:
        """Get current cartesian position."""
        cc.get_cartesian_position()
        # Additional get logic can be added here if needed
        # Return the cartesian position
        pass

    def stop_motion(self) -> None:
        """Stop all robot motion immediately."""
        cc.stop_motion()
        # Additional stop logic can be added here if needed
        # Send stop command to robot
        pass

    def get_robot_state(self) -> dict | str:
        """Get current robot state information."""
        cc.get_robot_state()
        # Additional get logic can be added here if needed
        # Return the robot state information
        pass
