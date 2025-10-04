from __future__ import annotations

import math

from armctl.templates import Commands, Properties
from armctl.templates import SocketController as Communication
from armctl.utils import CommandCheck as cc


# Command Format: CMD {...} \n
# Command Units: Radians and Meters


class Kuka(Communication, Commands, Properties):
    def __init__(self, ip: str, port: int):
        super().__init__(ip=ip, port=port)

        self.JOINT_RANGES: list[tuple[float, float]] = [
            (-math.pi, math.pi) for _ in range(6)
        ]
        self.MAX_JOINT_VELOCITY: float | None = None
        self.MAX_JOINT_ACCELERATION: float | None = None

    def connect(self):
        super().connect()

    def disconnect(self):
        super().disconnect()

    def sleep(self, seconds: float) -> None:
        """Sleep for the specified number of seconds."""
        cc.sleep(seconds)
        # Additional sleep logic can be added here if needed
        # Send sleep command to robot
        pass

    def move_joints(self, pos: list[float]) -> None:
        """Move robot joints to specified positions"""
        cc.move_joints(pos)

        # Example Command Format: "PTP {A1 0, A2 0, A3 0, A4 0, A5 0, A6 0}"
        command = (
            "PTP "
            + ", ".join(f"A{i + 1} {p}" for i, p in enumerate(pos))
            + "\n"
        )
        self.send_command(command)

        # Assert OK or DONE

    def get_joint_positions(self) -> list[float]:
        """Get current joint positions."""
        cc.get_joint_positions()
        response = self.send_command("GET_JOINT_POSITIONS\n")
        try:
            return [float(value) for value in response.strip().split(",")]
        except Exception as e:
            raise ValueError(
                f"Failed to parse joint positions: {response}"
            ) from e

    def move_cartesian(self, pose: list[float]) -> None:
        """Move robot to specified cartesian pose [x, y, z, rx, ry, rz]."""
        cc.move_cartesian(pose)
        # Example Command Format: "LIN {X 0, Y 0, Z 0, A 0, B 0, C 0}"
        axes = ["X", "Y", "Z", "A", "B", "C"]
        command = f"LIN {', '.join(f'{axis} {value}' for axis, value in zip(axes, pose))}\n"
        self.send_command(command)

    def get_cartesian_position(self) -> list[float]:
        """Get current cartesian position."""
        cc.get_cartesian_position()
        response = self.send_command("GET_CARTESIAN_POSITION\n")
        try:
            return [float(value) for value in response.strip().split(",")]
        except Exception as e:
            raise ValueError(
                f"Failed to parse cartesian position: {response}"
            ) from e

    def stop_motion(self) -> None:
        """Stop all robot motion immediately."""
        cc.stop_motion()
        self.send_command("HALT\n")

    def get_robot_state(self) -> dict | str:
        """Get current robot state information."""
        cc.get_robot_state()
        response = self.send_command("GET_ROBOT_STATE\n")
        try:
            return eval(response)
        except Exception:
            return response