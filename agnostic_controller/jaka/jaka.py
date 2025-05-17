from agnostic_controller.templates import SocketController as SCT, Commands
from agnostic_controller.angle_utils import AngleUtils
import math
import ast
import time

### Notes ###
# - Commands are sent as JSON strings.
# - Command units are degrees & meters.

class Jaka(SCT, Commands, AngleUtils):
    def __init__(self, ip:str, port:int | tuple[int, int] = (10_001, 10_000)):
        super().__init__(ip, port)                                         
        self.JOINT_RANGES = [           # Source: https://www.inrobots.shop/products/jaka-zu-5-cobot
            (-math.pi, math.pi),
            (math.radians(-85), math.radians(265)),
            (math.radians(-175), math.radians(175)),
            (math.radians(-85), math.radians(265)),
            (math.radians(-300), math.radians(300)),
            (-math.pi, math.pi),
        ]
        self.DOF = len(self.JOINT_RANGES)
        self.MAX_JOINT_VELOCITY = math.radians(180) # rad/s
        self.MAX_JOINT_ACCELERATION = math.radians(720) # rad/s^2

    def _response_handler(self, response: str):
        try:
            return ast.literal_eval(response)
        except (ValueError, SyntaxError) as e:
            raise RuntimeError(f"Failed to parse response: {response}") from e

    def _send_and_check(self, cmd_dict):
        resp = self._response_handler(self.send_command(str(cmd_dict)))
        if not (isinstance(resp, dict) and resp.get("errorCode") == "0" and resp.get("cmdName") == cmd_dict["cmdName"]):
            raise RuntimeError(f"Failed to execute {cmd_dict['cmdName']}: {resp}. {resp.get('errorMsg')}")
        return resp
    
    def connect(self): 
        super().connect()
        self._send_and_check({"cmdName": "power_on"})
        self._send_and_check({"cmdName": "emergency_stop_status"})
        self._send_and_check({"cmdName": "enable_robot"})
        self._send_and_check({
            "cmdName": "set_installation_angle",
            "angleX": 0,    # Robot rotation angle in the X direction, range: [0, 180] degrees.
            "angleZ": 0,    # Robot rotation angle in the Z direction, range: [0, 360) degrees.
        })

    def disconnect(self):
        self._send_and_check({"cmdName": "disable_robot"})
        # self._send_and_check({"cmdName": "shutdown"})  # NOT RECOMMENDED: Shuts down the Robot TCP Server
        super().disconnect()

    def sleep(self, seconds: float):
        assert isinstance(seconds, (int, float)), "Seconds must be a numeric value."
        assert seconds >= 0, "Seconds must be a non-negative value."
        time.sleep(seconds)

    def move_joints(self,
                    joint_positions: list[float],
                    speed: float = 0.25,
                    acceleration: float = 0.1,
                    *args, **kwargs) -> None:
        """
        Move the robot to the specified joint positions.

        Parameters
        ----------
        joint_positions : list of float
            Target joint positions in radians [j1, j2, j3, j4, j5, j6]
        speed : float
            Joint velocity in radians/sec
        acceleration : float
            Joint acceleration in radians/sec²
        relFlag : int
            0 for absolute motion, 1 for relative motion. 
        """
        if len(joint_positions) != self.DOF:
            raise ValueError(f"Joint positions must have {self.DOF} elements")

        assert speed < self.MAX_JOINT_VELOCITY, f"Speed out of range: 0 ~ {self.MAX_JOINT_VELOCITY}"
        assert acceleration < self.MAX_JOINT_ACCELERATION, f"Acceleration out of range: 0 ~ {self.MAX_JOINT_ACCELERATION}"

        for idx, pos in enumerate(joint_positions):
            if not (self.JOINT_RANGES[idx][0] <= pos <= self.JOINT_RANGES[idx][1]):
                raise ValueError(f"Joint {idx + 1} position {pos} is out of range: {self.JOINT_RANGES[idx]}")
            
        cmd = {
            "cmdName": "joint_move",
            "relFlag": 0,       # 0 for absolute motion, 1 for relative motion.
            "jointPosition": self.to_degrees_joint(joint_positions),
            "speed": math.degrees(speed),
            "accel": math.degrees(acceleration),
        }

        response = self._response_handler(self.send_command(str(cmd)))
        if not (isinstance(response, dict) and response.get("errorCode") == "0" and response.get("cmdName") == "joint_move"):
            raise RuntimeError(f"Failed to move joints: {response}. {response.get('errorMsg')}")

    def move_cartesian(self, 
                       robot_pose: list[float], 
                       speed: float = 0.25,
                       acceleration: float = 0.0,
                       *args, **kwargs) -> None:
        """
        Move the robot to the specified cartesian position. (`movel` or `movep`)

        Parameters
        ----------
        robot_pose : list of float
            Cartesian position and orientation [x, y, z, rx, ry, rz] in meters and radians.
        speed : float, optional
            Velocity of the movement in radians/sec
        acceleration : float, optional
            Acceleration of the movement in radians/sec²
        """
        assert speed < self.MAX_JOINT_VELOCITY, f"Speed out of range: 0 ~ {self.MAX_JOINT_VELOCITY}"
        assert acceleration < self.MAX_JOINT_ACCELERATION, f"Acceleration out of range: 0 ~ {self.MAX_JOINT_ACCELERATION}"

        # Only check orientation part for radians
        for pos in robot_pose[3:]:
            if not (0 <= pos <= math.pi*2):
                raise ValueError(f"Orientation value {pos} out of range: 0 ~ {math.pi*2}")

        cmd = {
            "cmdName": "end_move",
            "end_position": self.to_degrees_cartesian(robot_pose),
            "speed": self.to_degrees_joint(speed),
            "accel": self.to_degrees_joint(acceleration),
        }

        response = self._response_handler(self.send_command(str(cmd)))
        if not (isinstance(response, dict) and response.get("errorCode") == "0" and response.get("cmdName") == "joint_move"):
            raise RuntimeError(f"Failed to move joints: {response}. {response.get('errorMsg')}")

    def get_joint_positions(self, *args, **kwargs) -> list[float]:
        """
        Get the current joint positions of the robot.

        Returns
        -------
        list of float
            Joint positions in radians [j1, j2, j3, j4, j5, j6].
        """
        cmd = {"cmdName": "get_joint_pos"}
        response = self._response_handler(self.send_command(str(cmd))) # Returned in Degrees

        if not (isinstance(response, dict) and response.get("errorCode") == "0" and response.get("cmdName") == cmd["cmdName"]):
            raise RuntimeError(f"Failed to get joint positions: {response}. {response.get('errorMsg')}")
        
        return [math.radians(angle) for angle in response["joint_pos"]]

    def get_cartesian_position(self, *args, **kwargs) -> list[float]:
        """
        Retrieves the current Cartesian position of the robot's tool center point (TCP).

        Returns
        -------
        list of float
            Cartesian position [X, Y, Z, Rx, Ry, Rz], where X, Y, Z are in meters and Rx, Ry, Rz are in radians.
        """
        cmd = {"cmdName": "get_tcp_pos"}
        response = self._response_handler(self.send_command(str(cmd)))

        if not (isinstance(response, dict) and response.get("errorCode") == "0" and response.get("cmdName") == cmd["cmdName"]):
            raise RuntimeError(f"Failed to get TCP position: {response}. {response.get('errorMsg')}")
        return self.to_radians_cartesian(response["tcp_pos"])

    def stop_motion(self) -> None:
        self.send_command(str({"cmdName": "stop_program"}))

    def get_robot_state(self) -> dict:
        """
        Get the current state of the robot.

        Returns
        -------
        dict
            A dictionary containing the robot's state information:
            - enable: Whether the robot is enabled. True means enabled, False means not enabled.
            - power: Whether the robot is powered on. 1 means powered on, 0 means not powered on.
            - errorCode: The corresponding error code.
            - errcode: The error code returned by the controller.
            - errorMsg: The corresponding error message.
            - msg: The error message returned by the controller.
        """
        return self._response_handler(self.send_command(str({"cmdName": "get_robot_state"})))
