from __future__ import annotations

import time

from armctl.templates import Commands, Properties
from armctl.templates import SocketController as SCT
from armctl.utils import CommandCheck as cc
from armctl.utils import units as uu

## Notes
# - Command Format: CMD(arg)
# - Command units are degrees & mm.


class ElephantRobotics(SCT, Commands, Properties):
    def __init__(self, ip: str, port: int):
        super().__init__(ip, port)
        self.JOINT_RANGES = uu.joints2rad(
            [
                (-180.00, 180.00),
                (-270.00, 90.00),
                (-150.00, 150.00),
                (-260.00, 80.00),
                (-168.00, 168.00),
                (-174.00, 174.00),
            ]
        )
        self.MAX_JOINT_VELOCITY = uu.deg2rad(2000)
        self.MAX_JOINT_ACCELERATION = None

    def connect(self):
        super().connect()  # Socket Connection

        assert (
            self.send_command("power_on()") == "power_on:[ok]"
        )  # Power on the robot
        assert (
            self.send_command("state_on()") == "state_on:[ok]"
        )  # Enable the system

    def disconnect(self):
        self.stop_motion()  # Stop any ongoing motion
        # assert self.send_command("state_off()") == "state_off:[ok]"  # Shut down the system, but the robot is still powered on
        # assert self.send_command("power_off()") == "power_off:[ok]"  # Power off the robot
        super().disconnect()  # Socket disconnection

    def _waitforfinish(self):
        while True:
            if (
                self.send_command("wait_command_done()", timeout=60)
                == "wait_command_done:0"
            ):
                break
            time.sleep(0.25)

    def sleep(self, seconds):
        cc.sleep(seconds)
        self.send_command(f"wait({seconds})")
        time.sleep(seconds)

    def move_joints(
        self, pos: list[float], speed: int = uu.deg2rad(500)
    ) -> None:
        """
        Move the robot to the specified joint positions.

        Parameters
        ----------
        pos : list of float
            Joint positions in radians [j1, j2, j3, j4, j5, j6].
        speed : int, optional
            Speed of the movement, range `0` ~ `math.radians(2000)` (default: `math.radians(500)`).
        """

        cc.move_joints(self, pos, speed)

        pos_deg = uu.joints2deg(pos)
        speed_deg = uu.rad2deg(speed)

        command = f"set_angles({','.join(map(str, pos_deg))},{speed_deg})"
        response = self.send_command(command)

        assert response == f"{command}:[ok]", (
            f"Failed to move joints: {response}"
        )

        while any(
            abs(a - b) > 3 for a, b in zip(self.get_joint_positions(), pos)
        ):
            time.sleep(1)

    def move_cartesian(
        self,
        pose: tuple[float, float, float, float, float, float],
        speed: int = uu.deg2rad(500),
    ) -> None:
        """
        Move the robot to the specified Cartesian coordinates.

        Parameters
        ----------
        pose : tuple of float
            Cartesian coordinates in the format `[x, y, z, rx, ry, rz]`.
        speed : int, optional
            Speed of the movement, range `0` ~ `math.radians(2000)` (default: `math.radians(500)`).
        """

        cc.move_cartesian(self, pose)

        pose_deg = uu.pose2deg(pose)
        speed_deg = uu.rad2deg(speed)

        command = f"set_coords({','.join(map(str, pose_deg))},{speed_deg})"

        assert self.send_command(command) == "set_coords:[ok]"

        while not all(
            abs(a - b) <= 1 for a, b in zip(self.get_cartesian_position(), pose)
        ):
            time.sleep(1)

    def get_joint_positions(self):
        response = self.send_command("get_angles()")
        if response == "[-1.0, -2.0, -3.0, -4.0, -1.0, -1.0]":
            raise ValueError("Invalid joint positions response from robot")
        joint_positions = list(
            map(
                float,
                response[response.index("[") + 1 : response.index("]")].split(
                    ","
                ),
            )
        )  # From string list to float list
        return [round(x, 2) for x in joint_positions]

    def get_cartesian_position(self):
        response = self.send_command("get_coords()")  # [x, y, z, rx, ry, rz]
        if response == "[-1.0, -2.0, -3.0, -4.0, -1.0, -1.0]":
            raise ValueError("Invalid cartesian position response from robot")
        cartesian_position = list(
            map(
                float,
                response[response.index("[") + 1 : response.index("]")].split(
                    ","
                ),
            )
        )  # From string list to float list
        return [round(x, 2) for x in cartesian_position]

    def stop_motion(self):
        command = "task_stop"
        response = self.send_command(f"{command}()")

        if not response.startswith(f"{command}:"):
            raise SystemError(f"Unexpected response: {response}")

        result = response.split(":", 1)[1]

        if result != "[ok]":
            raise SystemError(result)
        return True

    def get_robot_state(self):
        command = "check_running"
        response = self.send_command(f"{command}()")

        if not response.startswith(f"{command}:"):
            raise SystemError(f"Unexpected response format: {response}")

        status = response.partition(":")[2]  # Get everything after the colon

        if status == "1":
            return True
        elif status == "0":
            return False
        else:
            raise ValueError(f"Unknown robot state: {status}")
