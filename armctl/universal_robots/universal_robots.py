from __future__ import annotations

import math

from armctl.templates import Commands, Properties
from armctl.templates import SocketController as SCT
from armctl.templates.logger import logger
from armctl.utils import CommandCheck as cc

### Notes ###
# Command Format: CMD(args)\n
# Output Units: radians, meters


class UniversalRobots(SCT, Commands, Properties):
    def _check_rtde(self):
        try:
            from .protocols.rtde import RTDE
        except ImportError:
            import os
            import shutil
            import sys
            from subprocess import run

            logger.warning(
                "RTDE Python Client Library not found. Attempting installation..."
            )

            # Determine installer
            if shutil.which("uv") and os.environ.get("VIRTUAL_ENV"):
                install_cmd = [
                    "uv",
                    "add",
                    "--quiet",
                    "urrtde@git+https://github.com/UniversalRobots/RTDE_Python_Client_Library.git@main",
                ]
            elif shutil.which("poetry") and os.environ.get("POETRY_ACTIVE"):
                install_cmd = [
                    "poetry",
                    "add",
                    "git+https://github.com/UniversalRobots/RTDE_Python_Client_Library.git@main",
                ]
            else:
                install_cmd = [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--quiet",
                    "git+https://github.com/UniversalRobots/RTDE_Python_Client_Library.git@main",
                ]

            try:
                run(install_cmd, check=True)
            except Exception as e:
                logger.error(
                    f"Failed to install RTDE Python Client Library: {e}"
                )
                raise ImportError(
                    "Could not install RTDE Python Client Library."
                ) from e

            # Try import again

    def __init__(self, ip: str, port: int | tuple[int, int] = 30_002):
        self._check_rtde()
        super().__init__(ip, port)
        self.JOINT_RANGES = [
            (-2 * math.pi, 2 * math.pi),
            (-2 * math.pi, 2 * math.pi),
            (-2 * math.pi, 2 * math.pi),
            (-2 * math.pi, 2 * math.pi),
            (-2 * math.pi, 2 * math.pi),
            (-2 * math.pi, 2 * math.pi),
        ]
        # Source: https://forum.universal-robots.com/t/maximum-axis-speed-acceleration/13338/2
        self.MAX_JOINT_VELOCITY = 2.0  # rad/s
        # Source: https://forum.universal-robots.com/t/maximum-axis-speed-acceleration/13338/4
        self.MAX_JOINT_ACCELERATION = 10.0  # rad/s^2

    def connect(self):
        super().connect()
        from .protocols.rtde import RTDE

        self.rtde = RTDE(self.ip)  # Initialize RTDE connection

    def disconnect(self):
        self.rtde.c.disconnect()  # Disconnect RTDE connection
        super().disconnect()

    def sleep(self, seconds):
        cc.sleep(seconds)
        self.send_command(f"sleep({seconds})\n")

    def move_joints(
        self,
        pos: list[float],
        speed: float = 0.1,
        acceleration: float = 0.05,
        t: float = 0.0,
        radius: float = 0.0,
    ) -> None:
        """
        MoveJ
        --------
        Move the robot to the specified joint positions.

        Parameters
        ----------
        pos : list of float
            Joint positions in radians [j1, j2, j3, j4, j5, j6].
        speed : float, optional
            Speed of the movement in rad/s.
        acceleration : float, optional
            Acceleration of the movement in rad/s^2.
        t : float, optional
            The time in seconds to make the move. If specified, the command will ignore the speed and acceleration values.
        radius : float, optional
            Blend radius in meters.
        """
        cc.move_joints(self, pos, speed, acceleration)

        command = f"movej([{','.join(map(str, pos))}], a={acceleration}, v={speed}, t={t}, r={radius})\n"
        self.send_command(
            command, timeout=t + 10, suppress_output=True, raw_response=False
        )

        # while not all(round(a, 2) == round(b, 2) for a, b in zip(self.get_joint_positions(), joint_positions)):
        #     _sleep(2)

    def move_cartesian(
        self,
        pose: list[float],
        move_type: str = "movel",
        speed: float = 0.1,
        acceleration: float = 0.1,
        time: float = 0.0,
        radius: float = 0.0,
    ) -> None:
        """
        Move the robot to the specified Cartesian position.

        Parameters
        ----------
        pose : list of float
            Cartesian position and orientation [x, y, z, rx, ry, rz] in meters and radians.
        move_type : str, optional
            Type of movement: "movel" for linear Cartesian pathing, "movep" for circular Cartesian pathing, or "movej" for flexible real-time path tracking.
        speed : float, optional
            Velocity of the movement in m/s.
        acceleration : float, optional
            Acceleration of the movement in m/s^2.
        time : float, optional
            The time in seconds to make the move. If specified, the command will ignore the speed and acceleration values.
        radius : float, optional
            Blend radius in meters.
        """
        if move_type not in {"movel", "movep", "movej"}:
            raise ValueError(
                "Unsupported move type. Use 'movel', 'movep', or 'movej'."
            )

        cc.move_cartesian(self, pose)

        # Construct the command based on the move type
        base_command = f"{move_type}(p[{','.join(map(str, pose))}], a={acceleration}, v={speed}"
        if move_type in {"movel", "movej"}:
            command = f"{base_command}, t={time}, r={radius})\n"
        else:  # move_type == "movep"
            command = f"{base_command}, r={radius})\n"

        self.send_command(command, suppress_output=True)

        # while not all(round(a, 2) == round(b, 2) for a, b in zip(self.get_cartesian_position(), pose)):
        #     _sleep(2)

    def get_joint_positions(self) -> list[float]:
        """
        Get the current joint positions of the robot.

        Returns
        -------
        list of float
            Joint positions in radians [j1, j2, j3, j4, j5, j6].
        """
        angles = self.rtde.joint_angles()
        logger.receive(f"Received response: {angles}")
        return angles

    def get_cartesian_position(self) -> list[float]:
        """
        Retrieves the current Cartesian position of the robot's tool center point (TCP).

        This method sends a command to the robot to obtain the actual TCP pose and
        processes the response to return the Cartesian position.

        Returns:
            list: A list representing the Cartesian position of the TCP in the format
                  [X, Y, Z, Rx, Ry, Rz], where X, Y, Z are the position coordinates in meters,
                  and Rx, Ry, Rz are the rotation vector components in radians.
        """
        pose = self.rtde.tcp_pose()
        logger.receive(f"Received response: {pose}")
        return pose

    def stop_motion(self) -> None:
        deceleration = 2.0  # rad/s^2
        self.send_command(f"stopj({deceleration})\n", suppress_output=True)

    def get_robot_state(self) -> dict[str, bool]:
        status = self.rtde.robot_status()

        key_out = [
            "Power On",
            "Program Running",
            "Emergency Stopped",
            "Stopped Due to Safety",
        ]
        logger.receive(
            "Received response: "
            + ", ".join(f"{k}: {status[k]}" for k in key_out)
            + " ..."
        )
        return status
