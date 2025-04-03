from agnostic_controller.templates import SocketController as SCT, Commands
from agnostic_controller.templates.logger import logger
from .rtde import RTDE
import math
import time
import warnings

class UniversalRobotics(SCT, Commands):
    def __init__(self, ip:str, port:int | tuple[int, int] = 30_002):  # 30002: Port for Sending URScript commands / 30003: Port for Receiving URScript commands
        super().__init__(ip, port)                                              # https://www.universal-robots.com/articles/ur/interface-communication/remote-control-via-tcpip/
        self.JOINT_RANGES = [ 
            (-math.pi, math.pi),
            (-math.pi, math.pi),
            (-math.pi, math.pi),
            (-math.pi, math.pi),
            (-math.pi, math.pi),
            (-math.pi, math.pi)
        ]
        self.DOF = len(self.JOINT_RANGES)
        self.MAX_JOINT_VELOCITY = 2.0  # rad/s
        self.MAX_ACCELERATION = 10.0  # rad/s^2

    
    def connect(self): 
        super().connect()
    
    def disconnect(self):
        super().disconnect()

    def sleep(self, seconds):
        self.send_command(f"sleep({seconds})\n")

    def move_joints(self, 
                    joint_positions, 
                    speed: float = 0.25, 
                    acceleration: float = 0.1, 
                    t: float = 0.0, 
                    radius: float = 0.0, 
                    *args, **kwargs) -> str:
        """
        MoveJ
        --------
        Move the robot to the specified joint positions.

        Parameters
        ----------
        joint_positions : list of float
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
        if len(joint_positions) != self.DOF:
            raise ValueError(f"Joint positions must have {self.DOF} elements")

        assert speed < self.MAX_JOINT_VELOCITY, f"Speed out of range: 0 ~ {self.MAX_JOINT_VELOCITY}" # Source: https://forum.universal-robots.com/t/maximum-axis-speed-acceleration/13338/4
        
        assert acceleration <= self.MAX_ACCELERATION, f"Acceleration out of range: 0 ~ {self.MAX_ACCELERATION}" # Source: https://forum.universal-robots.com/t/maximum-axis-speed-acceleration/13338/2

        for idx, pos in enumerate(joint_positions):
            if not (self.JOINT_RANGES[idx][0] <= pos <= self.JOINT_RANGES[idx][1]):
                raise ValueError(f"Joint {idx + 1} position {pos} is out of range: {self.JOINT_RANGES[idx]}")
            
        command = f"movej([{','.join(map(str, joint_positions))}], a={acceleration}, v={speed}, t={t}, r={radius})\n"
        self.send_command(command, suppress_output=True, raw_response=True)

    def move_cartesian(self, 
                       robot_pose, 
                        move_type: str = "movel",
                        speed: float = 0.25,
                        acceleration: float = 0.0,
                        time: float = 0.0,
                        radius: float = 0.0,
                       *args, **kwargs)->str:
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
        assert move_type in ["movel", "movep"], "Unsupported move type: movel or movep"

        assert speed < self.MAX_JOINT_VELOCITY, f"Speed out of range: 0 ~ {self.MAX_JOINT_VELOCITY}" # Source: https://forum.universal-robots.com/t/maximum-axis-speed-acceleration/13338/4
        
        assert acceleration <= self.MAX_ACCELERATION, f"Acceleration out of range: 0 ~ {self.MAX_ACCELERATION}" # Source: https://forum.universal-robots.com/t/maximum-axis-speed-acceleration/13338/2

        for pos in robot_pose[3:]:
            if not (0 <= pos <= math.pi*2):
                raise ValueError(f"Joint position {pos} out of range: 0 ~ {math.pi*2}")
            
        if self.send_command("is_within_safety_limits({})\n".format(','.join(map(str, robot_pose)))) == "False":
            raise ValueError("Cartesian position out of safety limits")

        command = f"{move_type}([{','.join(map(str, robot_pose))}], a={acceleration}, v={speed}, t={time}, r={radius})\n"
        return self.send_command(command, suppress_output=True, raw_response=True)

    def get_joint_positions(self, *args, **kwargs):
        """
        Get the current joint positions of the robot.

        Returns
        -------
        list of float
            Joint positions in radians [j1, j2, j3, j4, j5, j6].
        """
        response = self.send_command("get_actual_joint_positions()\n", suppress_output=True, raw_response=True, suppress_input=kwargs.get('suppress_input', False))
        angles = RTDE.joint_angles(response)
        logger.receive(f"Received response: {angles}")
        return angles

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
        response = self.send_command("get_actual_tcp_pose()\n", suppress_output=True, raw_response=True)
        pose = RTDE.tcp_pose(response)
        logger.receive(f"Received response: {pose}")
        return pose

    def stop_motion(self):
        self.send_command("stopj(2)\n",suppress_output=True) # deceleration: 2 rad/s^2

    def get_robot_state(self):
        return self.send_command("get_robot_status()\n")
    
    def set_gripper_position(self, position: float, name: str="rg2", force: float=10) -> None:
        """Set the analog position of the gripper (0-255)."""
        if position < 0 or position > 255:
            raise ValueError("Position must be between 0 and 255.")
        
        max_range = 140
        position = int((position / 255) * max_range) # Relinearize the position to the internal range of the gripper

        if force < 0 or force > 255:
            raise ValueError("Force must be between 0 and 255.")
        
        max_force = 255
        force = int((force / 255) * max_force)  # Linearize the force to the range 0-max_force
        
        valid_grippers = ["rg2", "rg6", "vgc10"]
        if name not in valid_grippers:
            raise ValueError(f"Gripper name must be one of {','.join(valid_grippers)}.")

        if isinstance(position, float):
            position = int(position)
            warnings.warn(f"Position converted to int: {position}", UserWarning, 2)

        self.send_command(f"{name}_set_force({force})\n", suppress_output=True)
        self.send_command(f"{name}_set_width({position})\n", suppress_output=True)

    def get_gripper_position(self) -> float:
        """Get the current position of the gripper."""
        response = self.send_command("rg2_get_width()\n", suppress_output=True, raw_response=True)
        return float(response.strip())
    
    def get_gripper_status(self) -> bool:
        """Get the current status of the gripper."""
        response = self.send_command("rg2_get_status()\n", suppress_output=True, raw_response=True)
        return response.strip() == "1"  # 1 means gripper is closed, 0 means open
    
    def open_gripper(self, force: float=150) -> None:
        self.send_command("rg2_open()\n", suppress_output=True)

    def close_gripper(self) -> None:
        self.send_command("rg2_close()\n", suppress_output=True)
        
