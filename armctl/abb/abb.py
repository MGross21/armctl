"""ABB Robot Controller"""
from __future__ import annotations

import atexit
import math

from armctl.templates import Commands, Properties
from armctl.templates import SocketController as Communication
from armctl.utils import CommandCheck as cc


class ABB(Communication, Commands, Properties):
    def __init__(self, ip: str = "192.168.125.1", port: int = 80):
        super().__init__(ip=ip, port=port)

        # Define Properties
        self.JOINT_RANGES: list[tuple[float, float]] = [
            (-2 * math.pi, 2 * math.pi) for _ in range(6)
        ]
        self.MAX_JOINT_VELOCITY: float | None = None
        self.MAX_JOINT_ACCELERATION: float | None = None

    def connect(self):
        super().connect()  # Call first to ensure base connection logic is executed

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
