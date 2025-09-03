from __future__ import annotations

import ast
import math
import time
from typing import Any

from armctl.templates import Commands, Properties
from armctl.templates import SocketController as SCT
from armctl.utils import CommandCheck as cc
from armctl.utils import units as uu

### Notes ###
# Command Format: dictionaries/json strings.
# Output Units: degrees & meters.

# Source: https://www.inrobots.shop/products/jaka-zu-5-cobot


class Jaka(SCT, Commands, Properties):
    JOINT_RANGES = uu.joints2rad(
        [
            (-180, 180),
            (-85, 265),
            (-175, 175),
            (-85, 265),
            (-300, 300),
            (-180, 180),
        ]
    )
    MAX_JOINT_VELOCITY = uu.deg2rad(180)  # rad/s
    MAX_JOINT_ACCELERATION = uu.deg2rad(720)  # rad/s^2

    def __init__(self, ip: str, port: int | tuple[int, int] = (10_001, 10_000)):
        super().__init__(ip, port)

    def _response_handler(self, response: str) -> Any:
        try:
            return ast.literal_eval(response)
        except (ValueError, SyntaxError) as e:
            raise RuntimeError(f"Failed to parse response: {response}") from e

    def _send_and_check(self, cmd_dict: dict[str, Any]) -> dict[str, Any]:
        resp = self._response_handler(self.send_command(str(cmd_dict)))
        if not (
            isinstance(resp, dict)
            and resp.get("errorCode") == "0"
            and resp.get("cmdName") == cmd_dict["cmdName"]
        ):
            raise RuntimeError(
                f"Failed to execute {cmd_dict['cmdName']}: {resp}. {resp.get('errorMsg')}"
            )
        return resp

    def connect(self) -> None:
        super().connect()
        self._send_and_check({"cmdName": "power_on"})
        self._send_and_check({"cmdName": "emergency_stop_status"})
        self._send_and_check({"cmdName": "enable_robot"})
        self._send_and_check(
            {
                "cmdName": "set_installation_angle",
                "angleX": 0,  # Robot rotation angle in the X direction, range: [0, 180] degrees.
                "angleZ": 0,  # Robot rotation angle in the Z direction, range: [0, 360) degrees.
            }
        )

    def disconnect(self) -> None:
        self._send_and_check({"cmdName": "disable_robot"})
        # self._send_and_check({"cmdName": "shutdown"})  # NOT RECOMMENDED: Shuts down the Robot TCP Server
        super().disconnect()

    def sleep(self, seconds: float) -> None:
        cc.sleep(seconds)
        time.sleep(seconds)

    def move_joints(
        self, pos: list[float], speed: float = 0.25, acceleration: float = 0.1
    ) -> None:
        """
        Move the robot to the specified joint positions.
        Parameters
        ----------
        pos : list of float
            Target joint positions in radians [j1, j2, j3, j4, j5, j6]
        speed : float
            Joint velocity in radians/sec
        acceleration : float
            Joint acceleration in radians/sec²
        """
        cc.move_joints(self, pos, speed, acceleration)

        cmd = {
            "cmdName": "joint_move",
            "relFlag": 0,  # 0 for absolute motion, 1 for relative motion.
            "jointPosition": uu.joints2deg(pos),
            "speed": uu.rad2deg(speed),
            "accel": uu.rad2deg(acceleration),
        }
        self._send_and_check(cmd)

    def move_cartesian(
        self, pose: list[float], speed: float = 0.25, acceleration: float = 0.0
    ) -> None:
        """
        Move the robot to the specified cartesian position.
        Parameters
        ----------
        pose : list of float
            Cartesian position and orientation [x, y, z, rx, ry, rz] in meters and radians.
        speed : float, optional
            Velocity of the movement in radians/sec
        acceleration : float, optional
            Acceleration of the movement in radians/sec²
        """
        cc.move_cartesian(self, pose)

        cmd = {
            "cmdName": "end_move",
            "end_position": uu.pose2deg(pose),
            "speed": uu.rad2deg(speed),
            "accel": uu.rad2deg(acceleration),
        }
        self._send_and_check(cmd)

    def get_joint_positions(self) -> list[float]:
        """
        Get the current joint positions of the robot.
        Returns
        -------
        list of float
            Joint positions in radians [j1, j2, j3, j4, j5, j6].
        """
        cc.get_joint_positions()
        cmd = {"cmdName": "get_joint_pos"}
        response = self._send_and_check(cmd)
        return [math.radians(angle) for angle in response["joint_pos"]]

    def get_cartesian_position(self) -> list[float]:
        """
        Retrieves the current Cartesian position of the robot's tool center point (TCP).
        Returns
        -------
        list of float
            Cartesian position [X, Y, Z, Rx, Ry, Rz], where X, Y, Z are in meters and Rx, Ry, Rz are in radians.
        """
        cc.get_cartesian_position()
        cmd = {"cmdName": "get_tcp_pos"}
        response = self._send_and_check(cmd)
        return self.to_radians_cartesian(response["tcp_pos"])

    def stop_motion(self) -> None:
        cc.stop_motion()
        self._send_and_check({"cmdName": "stop_program"})

    def get_robot_state(self) -> dict[str, Any]:
        """
        Get the current state of the robot.

        Returns
        -------
        dict
            A dictionary containing the robot's state information.
            - `enable`: Whether the robot is enabled. True means enabled, False means not enabled.
            - `power`: Whether the robot is powered on. 1 means powered on, 0 means not powered on.
            - `errorCode`: The corresponding error code.
            - `errcode`: The error code returned by the controller.
            - `errorMsg`: The corresponding error message.
            - `msg`: The error message returned by the controller.
        """
        cc.get_robot_state()
        return self._send_and_check({"cmdName": "get_robot_state"})
