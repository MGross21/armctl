"""
Dobot M1 Pro controller — TCP/IP text protocol.

Response format: "ErrorID,{val1,...,valN},MessageName(params);"

J3 is a prismatic (Z-axis) joint; GetAngle()/JointMoveJ() values are in mm.
The public API represents J3 in radians (1 rad = 1 mm) for consistency.

Source
------
https://download.dobot.cc/2024/04/TCP_IP%20Remote%20Control%20Interface%20Guide%20%284axis%29_20240419_en.pdf
"""

from __future__ import annotations

import math

from armctl.templates import SocketController as SOC
from armctl.utils import CommandCheck as cc
from armctl.utils import units as uu

from .dobot import Codes, Dobot


class DobotM1Pro(SOC, Dobot):
    """Dobot M1 Pro 4-DOF SCARA."""

    # Approximate joint limits (degrees -> radians).
    # J3 is prismatic; value treated as mm mapped 1:1 to radians.
    JOINT_RANGES = uu.joints2rad(
        [
            (-145.0, 145.0),  # J1: base swing
            (-145.0, 145.0),  # J2: forearm swing
            (-200.0, 0.0),  # J3: Z-axis travel (mm -> rad)
            (-360.0, 360.0),  # J4: end-effector rotation
        ]
    )
    MAX_JOINT_VELOCITY: float = uu.deg2rad(180.0)
    MAX_JOINT_ACCELERATION: float = uu.deg2rad(720.0)

    def __init__(self, ip: str, port: int = 29_999):
        super().__init__(ip, port)

    def _send(self, s: str) -> tuple[int, str, str]:
        """
        Send command string and parse the response.

        Returns
        -------
        tuple of (int, str, str)
            error_code, values_str, message.
            values_str is the content inside {}, empty string if no values.
        """
        raw = self.send_command(f"{s}\n").strip().rstrip(";")
        comma1 = raw.index(",")
        code = int(raw[:comma1])
        brace_open = raw.index("{", comma1)
        brace_close = raw.index("}", brace_open)
        values_str = raw[brace_open + 1 : brace_close]
        message = raw[brace_close + 2 :]
        return code, values_str, message

    def _send_and_check(
        self, cmd: str, motion: bool = False
    ) -> list[float] | None:
        """
        Send command; raises RuntimeError on non-zero error code.

        Parameters
        ----------
        cmd : str
            Command string without trailing newline.
        motion : bool
            Blocks until motion completes via Sync().

        Returns
        -------
        list of float or None
            Parsed return values. None if response has no values.
        """
        code, values_str, _ = self._send(cmd)
        if code != 0:
            raise RuntimeError(f"Error {code}: {Codes.get_cmd_message(code)}")
        result = (
            [float(v) for v in values_str.split(",")] if values_str else None
        )
        if motion:
            self._send("Sync()")
        return result

    def connect(self) -> None:
        """Open socket, enable robot, clear errors, and reset the queue."""
        super().connect()
        self._send_and_check(
            "EnableRobot({},{},{},{})".format(0.0, 0.0, 0.0, 0.0)
        )
        self._send_and_check("ClearError()")
        self._send_and_check("Continue()")
        self._send_and_check("ResetRobot()")

    def disconnect(self) -> None:
        """Close socket."""
        super().disconnect()

    def sleep(self, seconds: float) -> None:
        """
        Timed pause queued on the controller.

        Parameters
        ----------
        seconds : float
            Duration in seconds; sent as milliseconds via Wait().
        """
        cc.sleep(seconds)
        self._send_and_check(f"Wait({int(seconds * 1000)})")

    def move_joints(
        self,
        pos: list[float],
        speed: float = uu.deg2rad(30.0),
        acceleration: float = uu.deg2rad(50.0),
    ) -> None:
        """
        Joint-interpolated move to joint positions.

        Parameters
        ----------
        pos : list of float
            [J1, J2, J3, J4] in radians.
        speed : float
            Joint speed in rad/s.
        acceleration : float
            Joint acceleration in rad/s².
        """
        cc.move_joints(self, pos, speed, acceleration)
        pos_deg = uu.joints2deg(pos)
        self._send_and_check(
            "JointMoveJ({})".format(",".join(map(str, pos_deg))),
            motion=True,
        )

    def move_cartesian(self, pose: list[float]) -> None:
        """
        Joint-interpolated move to Cartesian pose.

        Parameters
        ----------
        pose : list of float
            [x, y, z, r] — x/y/z in meters, r in radians.
        """
        cc.move_cartesian(self, pose)
        x_mm = pose[0] * 1000.0
        y_mm = pose[1] * 1000.0
        z_mm = pose[2] * 1000.0
        r_deg = math.degrees(pose[3])
        self._send_and_check(
            f"MoveJ({x_mm},{y_mm},{z_mm},{r_deg})", motion=True
        )

    def get_joint_positions(self) -> list[float]:
        """
        Current joint angles.

        Returns
        -------
        list of float
            [J1, J2, J3, J4] in radians.
        """
        cc.get_joint_positions()
        result = self._send_and_check("GetAngle()")
        return [math.radians(j) for j in result]

    def get_cartesian_position(self) -> list[float]:
        """
        Current Cartesian pose.

        Returns
        -------
        list of float
            [x, y, z, r] — x/y/z in meters, r in radians.
        """
        cc.get_cartesian_position()
        result = self._send_and_check("GetPose()")
        return [
            result[0] / 1000.0,
            result[1] / 1000.0,
            result[2] / 1000.0,
            math.radians(result[3]),
        ]

    def stop_motion(self) -> None:
        """Stop all motion and clear the queue."""
        cc.stop_motion()
        self._send_and_check("StopRobot()")

    def get_robot_state(self) -> str:
        """
        Current robot mode.

        Returns
        -------
        str
            Robot mode string (see Codes.STATE).
        """
        cc.get_robot_state()
        code, _, _ = self._send("RobotMode()")
        return Codes.get_state_message(code)
