"""ABB Robot Controller"""

from __future__ import annotations

import atexit
import math

from armctl.templates import Commands, Properties
from armctl.templates import SocketController as Communication
from armctl.utils import CommandCheck as cc
from pathlib import Path

# Command Format: "CALL <FUNCTION_NAME> <ARG1> ... <ARGN> \n"

class ABB(Communication, Commands, Properties):
    def __init__(self, ip: str = "192.168.125.1", port: int = 11002):
        super().__init__(ip=ip, port=port)

        # Define Properties
        self.JOINT_RANGES: list[tuple[float, float]] = [
            (-math.pi, math.pi) for _ in range(6)
        ]
        self.MAX_JOINT_VELOCITY: float | None = None
        self.MAX_JOINT_ACCELERATION: float | None = None

        raise NotImplementedError("ABB controller is not yet implemented.")

    def connect(self):
        try:
            super().connect()  # Call first to ensure base connection logic is executed
            # Additional connection logic can be added here if needed
        except Exception as e:
            self.disconnect()  # Ensure disconnection on failure
            raise ConnectionError(
            f"Connection failed: {e}. Make sure the robot controller is reachable at "
            f"{self.ip}:{self.port} and the ABB server is properly configured (see "
            f"{Path(__file__).parent / 'abb_rapid_server.txt'})."
            ) from e

    @atexit.register
    def disconnect(self):
        super().disconnect()

    def sleep(self, seconds: float) -> None:
        """Sleep for the specified number of seconds."""
        cc.sleep(seconds)
        self.send_command(f"CALL SLEEP {seconds} \n")

    def move_joints(self, pos: list[float]) -> None:
        """Move robot joints to specified positions"""
        cc.move_joints(pos)
        self.send_command(f"CALL MOVE_JOINTS {' '.join(map(str, pos))} \n")

    def get_joint_positions(self) -> list[float]:
        """Get current joint positions."""
        cc.get_joint_positions()

        response = self.send_command("CALL GET_JOINT_POS \n")
        
        # Format: J j1 j2 j3 j4 j5 j6
        return list(map(float, response.strip().split()[1:7]))

    def move_cartesian(self, pose: list[float]) -> None:
        """Move robot to specified cartesian pose [x, y, z, rx, ry, rz]."""
        cc.move_cartesian(pose)

        response = self.send_command(f"CALL MOVE_CART {' '.join(map(str, pose))} \n")

        if "OK" not in response:
            raise RuntimeError(f"Failed to move to cartesian pose: {response}")

    def get_cartesian_position(self) -> list[float]:
        """Get current cartesian position."""
        cc.get_cartesian_position()
        response = self.send_command("CALL GET_CART_POS \n")

        # Format: C x y z qx qy qz qw
        return list(map(float, response.strip().split()[1:7]))

    def stop_motion(self) -> None:
        """Stop all robot motion immediately."""
        cc.stop_motion()

        response = self.send_command("CALL STOP_MOTION \n")
        if "OK" not in response:
            raise RuntimeError(f"Failed to stop motion: {response}")
        
    def get_robot_state(self) -> dict | str:
        """Get current robot state information."""
        cc.get_robot_state()
        cmd = "CALL GET_STATE \n"
        response = self.send_command(cmd)

        # Format: STATE <state_info>
        # Error Format: STATE ERROR <error_info>
        state_info = response.strip().split(' ', 1)[1]
        return state_info