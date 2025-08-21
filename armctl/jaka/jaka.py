import ast
import math
import time
from typing import Any, Dict, List, Union

from armctl.utils import Angle as au
from armctl.templates import Commands
from armctl.templates import Properties
from armctl.templates import SocketController as SCT

### Notes ###
# - Commands are sent as JSON strings.
# - Command units are degrees & meters.

# Source: https://www.inrobots.shop/products/jaka-zu-5-cobot


class Jaka(SCT, Commands, Properties):
    JOINT_RANGES = [
        (-math.pi, math.pi),
        (math.radians(-85), math.radians(265)),
        (math.radians(-175), math.radians(175)),
        (math.radians(-85), math.radians(265)),
        (math.radians(-300), math.radians(300)),
        (-math.pi, math.pi),
    ]
    DOF = len(JOINT_RANGES)
    MAX_JOINT_VELOCITY = math.radians(180)  # rad/s
    MAX_JOINT_ACCELERATION = math.radians(720)  # rad/s^2

    def __init__(
        self, ip: str, port: Union[int, tuple[int, int]] = (10_001, 10_000)
    ):
        super().__init__(ip, port)

    def _response_handler(self, response: str) -> Any:
        try:
            return ast.literal_eval(response)
        except (ValueError, SyntaxError) as e:
            raise RuntimeError(f"Failed to parse response: {response}") from e

    def _send_and_check(self, cmd_dict: Dict[str, Any]) -> Dict[str, Any]:
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
        if not isinstance(seconds, (int, float)):
            raise TypeError("Seconds must be a numeric value.")
        if seconds < 0:
            raise ValueError("Seconds must be a non-negative value.")
        time.sleep(seconds)

    def move_joints(
        self, pos: List[float], speed: float = 0.25, acceleration: float = 0.1
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
        if len(pos) != self.DOF:
            raise ValueError(f"Joint positions must have {self.DOF} elements")
        if not (0 < speed <= self.MAX_JOINT_VELOCITY):
            raise ValueError(
                f"Speed out of range: 0 ~ {self.MAX_JOINT_VELOCITY}"
            )
        if not (0 < acceleration <= self.MAX_JOINT_ACCELERATION):
            raise ValueError(
                f"Acceleration out of range: 0 ~ {self.MAX_JOINT_ACCELERATION}"
            )
        for idx, p in enumerate(pos):
            min_j, max_j = self.JOINT_RANGES[idx]
            if not (min_j <= p <= max_j):
                raise ValueError(
                    f"Joint {idx + 1} position {p} is out of range: {self.JOINT_RANGES[idx]}"
                )
        cmd = {
            "cmdName": "joint_move",
            "relFlag": 0,  # 0 for absolute motion, 1 for relative motion.
            "jointPosition": self.to_degrees_joint(pos),
            "speed": math.degrees(speed),
            "accel": math.degrees(acceleration),
        }
        self._send_and_check(cmd)

    def move_cartesian(
        self, pose: List[float], speed: float = 0.25, acceleration: float = 0.0
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
        if not (0 < speed <= self.MAX_JOINT_VELOCITY):
            raise ValueError(
                f"Speed out of range: 0 ~ {self.MAX_JOINT_VELOCITY}"
            )
        if not (0 <= acceleration <= self.MAX_JOINT_ACCELERATION):
            raise ValueError(
                f"Acceleration out of range: 0 ~ {self.MAX_JOINT_ACCELERATION}"
            )
        for p in pose[3:]:
            if not (0 <= p <= math.pi * 2):
                raise ValueError(
                    f"Orientation value {p} out of range: 0 ~ {math.pi * 2}"
                )
        cmd = {
            "cmdName": "end_move",
            "end_position": self.to_degrees_cartesian(pose),
            "speed": math.degrees(speed),
            "accel": math.degrees(acceleration),
        }
        self._send_and_check(cmd)

    def get_joint_positions(self) -> List[float]:
        """
        Get the current joint positions of the robot.
        Returns
        -------
        list of float
            Joint positions in radians [j1, j2, j3, j4, j5, j6].
        """
        cmd = {"cmdName": "get_joint_pos"}
        response = self._send_and_check(cmd)
        return [math.radians(angle) for angle in response["joint_pos"]]

    def get_cartesian_position(self) -> List[float]:
        """
        Retrieves the current Cartesian position of the robot's tool center point (TCP).
        Returns
        -------
        list of float
            Cartesian position [X, Y, Z, Rx, Ry, Rz], where X, Y, Z are in meters and Rx, Ry, Rz are in radians.
        """
        cmd = {"cmdName": "get_tcp_pos"}
        response = self._send_and_check(cmd)
        return self.to_radians_cartesian(response["tcp_pos"])

    def stop_motion(self) -> None:
        self._send_and_check({"cmdName": "stop_program"})

    def get_robot_state(self) -> Dict[str, Any]:
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
        return self._send_and_check({"cmdName": "get_robot_state"})
