from agnostic_controller.templates import SocketController as SCT, Commands
from agnostic_controller.templates.logger import logger
import math
import ast


class Jaka(SCT, Commands):
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

        raise NotImplementedError("Jaka Robot is not supported yet")    # TODO: Implement Jaka Robot

    def _response_handler(self, response: str):
        try:
            return ast.literal_eval(response)
        except (ValueError, SyntaxError) as e:
            raise RuntimeError(f"Failed to parse response: {response}") from e
        
    
    def connect(self): 
        super().connect()

        # POWER ON ROBOT
        power_cmd = "power_on"
        power_on = self._response_handler(self.send_command(str({"cmdName": power_cmd})))
        if not (isinstance(power_on, dict) and power_on.get("errorCode") == "0" and power_on.get("cmdName") == power_cmd):
            raise RuntimeError(f"Failed to power on the robot: {power_on}. {power_on.get('errorMsg')}")
        
        # CHECK E-STOP
        estop_cmd = "emergency_stop_status"
        estop_status = self._response_handler(self.send_command(str({"cmdName": estop_cmd})))
        if not (isinstance(estop_status, dict) and estop_status.get("errorCode") == "0" and estop_status.get("cmdName") == estop_cmd):
            raise RuntimeError(f"Failed to check E-Stop status: {estop_status}. {estop_status.get('errorMsg')}")

        # ENABLE ROBOT
        enable_cmd = "enable_robot"
        enable_robot = self._response_handler(self.send_command(str({"cmdName": enable_cmd})))
        if not (isinstance(enable_robot, dict) and enable_robot.get("errorCode") == "0" and enable_robot.get("cmdName") == enable_cmd):
            raise RuntimeError(f"Failed to enable the robot: {enable_robot}. {enable_robot.get('errorMsg')}")

        # INITIALIZE ROBOT MOUNTING ANGLE
        installation_cmd ={
            "cmdName": "set_installation_angle",
            "angleX": 0,    # Robot rotation angle in the X direction, range: [0, 180] degrees.
            "angleZ": 0,    # Robot rotation angle in the Z direction, range: [0, 360) degrees.
        }
        installation = self._response_handler(self.send_command())
        if not (isinstance(installation, dict) and installation.get("errorCode") == "0" and installation.get("cmdName") == installation_cmd):
            raise RuntimeError(f"Failed to install the robot: {installation}. {installation.get('errorMsg')}")

    def disconnect(self):

        disable_cmd = "disable_robot"
        disable_robot = self._response_handler(self.send_command(str({"cmdName": disable_cmd})))
        if not (isinstance(disable_robot, dict) and disable_robot.get("errorCode") == "0" and disable_robot.get("cmdName") == disable_cmd):
            raise RuntimeError(f"Failed to disable the robot: {disable_robot}. {disable_robot.get('errorMsg')}")
        
        # NOT RECOMMENDED: Shuts down the Robot TCP Server
        # shutdown_cmd = "shutdown"
        # shutdown_robot = self._response_handler(self.send_command(str({"cmdName": shutdown_cmd})))

        super().disconnect()

    def sleep(self, seconds):
        self.send_command(f"sleep({seconds})\n")

    def move_joints(self, 
                    joint_positions:list[float], 
                    speed: float = 0.25, 
                    acceleration: float = 0.1, 
                    *args, **kwargs) -> str:
        """
        Move the robot to the specified joint positions.

        Parameters
        ----------
        joint_positions : list of float
            Target joint positions in degrees [j1, j2, j3, j4, j5, j6]
        speed : float
            Joint velocity in degrees
        acceleration : float
            Joint acceleration in deg/s²
        relFlag : int
            0 for absolute motion, 1 for relative motion. 
        Returns
        -------
        dict
            Response from the robot controller.
        """

        # # Convert radians to degrees for the command
        # joint_deg = [math.degrees(j) for j in joint_positions]
        # speed_deg = math.degrees(speed)
        # accel_deg = math.degrees(acceleration)


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
            "jointPosition": joint_positions,
            "speed": speed,
            "accel": acceleration,
        }


        response = self._response_handler(self.send_command(str(cmd)))
        if not (isinstance(response, dict) and response.get("errorCode") == "0" and response.get("cmdName") == "joint_move"):
            raise RuntimeError(f"Failed to move joints: {response}. {response.get('errorMsg')}")
        return response

    def move_cartesian(self, 
                       robot_pose: list[float], 
                       speed: float = 0.25,
                       acceleration: float = 0.0,
                       *args, **kwargs) -> str:
        """
        Move the robot to the specified cartesian position. (`movel` or `movep`)

        Parameters
        ----------
        robot_pose : list of float
            Cartesian position and orientation [x, y, z, rx, ry, rz] in meters and radians.
        move_type : str, optional
            Type of movement: "movel" for linear cartesian pathing or "movep" for circular cartesian pathing.
        speed : float, optional
            Velocity of the movement in m/s.
        acceleration : float, optional
            Acceleration of the movement in m/s^2.
        time : float, optional
            The time in seconds to make the move. If specified, the command will ignore the speed and acceleration values.
        radius : float, optional
            Blend radius in meters.
        """

        assert speed < self.MAX_JOINT_VELOCITY, f"Speed out of range: 0 ~ {self.MAX_JOINT_VELOCITY}"
        assert acceleration < self.MAX_JOINT_ACCELERATION, f"Acceleration out of range: 0 ~ {self.MAX_JOINT_ACCELERATION}"

        for pos in robot_pose[3:]:
            if not (0 <= pos <= math.pi*2):
                raise ValueError(f"Joint position {pos} out of range: 0 ~ {math.pi*2}")

        cmd = {
            "cmdName": "end_move",
            "end_position": robot_pose,
            "speed": speed,
            "accel": acceleration,
        }

        response = self._response_handler(self.send_command(str(cmd)))
        if not (isinstance(response, dict) and response.get("errorCode") == "0" and response.get("cmdName") == "joint_move"):
            raise RuntimeError(f"Failed to move joints: {response}. {response.get('errorMsg')}")
        return response

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

    def get_cartesian_position(self, *args, **kwargs):
        """
        Retrieves the current Cartesian position of the robot's tool center point (TCP).

        This method sends a command to the robot to obtain the actual TCP pose and
        processes the response to return the Cartesian position.

        Returns:
            list: A list representing the Cartesian position of the TCP in the format
                  [X, Y, Z, Rx, Ry, Rz], where X, Y, Z are the position coordinates in meters,
                  and Rx, Ry, Rz are the rotation vector components in radians.
        """
        cmd = {"cmdName": "get_tcp_pos"}
        response = self._response_handler(self.send_command(str(cmd)))

        if not (isinstance(response, dict) and response.get("errorCode") == "0" and response.get("cmdName") == cmd["cmdName"]):
            raise RuntimeError(f"Failed to get TCP position: {response}. {response.get('errorMsg')}")
        return response["tcp_pos"]

    def stop_motion(self):
        self.send_command(str({"cmdName": "stop_program"}))

    def get_robot_state(self):
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
