from agnostic_controller.templates import SocketController as SCT, Commands
import math

class UniversalRobotics(SCT, Commands):
    def __init__(self, ip:str, port:int | tuple[int, int] = (30_002, 30_003)):  # 30002: Port for Sending URScript commands / 30003: Port for Receiving URScript commands
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
    
    def connect(self): 
        super().connect()
    
    def disconnect(self):
        super().disconnect()

    def sleep(self, seconds):
        self.send_command(f"sleep({seconds})\n")

    def move_joints(self, 
                    joint_positions, 
                    speed: float = 0.1, 
                    acceleration: float = 0.0, 
                    time: float = 0.0, 
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
            Speed of the movement in rad/s (default: 0.1).
        acceleration : float, optional
            Acceleration of the movement in rad/s^2 (default: 0.0).
        time : float, optional
            The time in seconds to make the move. If specified, the command will ignore the speed and acceleration values (default: 0.0).
        r : float, optional
            Blend radius in meters (default: 0.0).
        DOF : int, optional
            Degrees of freedom (default: 6).
        """
        if len(joint_positions) != self.DOF:
            raise ValueError(f"Joint positions must have {self.DOF} elements")

        assert speed < 2, "Speed out of range: 0 ~ 2" # Source: https://forum.universal-robots.com/t/maximum-axis-speed-acceleration/13338/4
        
        assert acceleration <= 10, "Acceleration out of range: 0 ~ 10" # Source: https://forum.universal-robots.com/t/maximum-axis-speed-acceleration/13338/2

        for pos in joint_positions:
            if not (0 <= pos <= math.pi*2):
                raise ValueError(f"Joint position {pos} out of range: 0 ~ {math.pi*2}")
            
        command = f"movej(p[{','.join(map(str, joint_positions))}], a={acceleration}, v={speed}, t={time}, r={radius})\n"
        return self.send_command(command)

    def move_cartesian(self, 
                       robot_pose, 
                        move_type: str = "movel",
                        speed: float = 0.1,
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
        moveType : str, optional
            Type of movement: "movel" for linear cartesian pathing or "movep" for circular cartesian pathing (default: "movel").
        speed : float, optional
            Velocity of the movement in m/s (default: 0.1).
        acceleration : float, optional
            Acceleration of the movement in m/s^2 (default: 0.0).
        time : float, optional
            The time in seconds to make the move. If specified, the command will ignore the speed and acceleration values (default: 0.0).
        r : float, optional
            Blend radius in meters (default: 0.0).
        """
        assert move_type in ["movel", "movep"], "Unsupported move type: movel or movep"

        assert speed < 2, "Speed out of range: 0 ~ 2" # Source: https://forum.universal-robots.com/t/maximum-axis-speed-acceleration/13338/4
        
        assert acceleration <= 10, "Acceleration out of range: 0 ~ 10" # Source: https://forum.universal-robots.com/t/maximum-axis-speed-acceleration/13338/2

        for pos in robot_pose[3:]:
            if not (0 <= pos <= math.pi*2):
                raise ValueError(f"Joint position {pos} out of range: 0 ~ {math.pi*2}")
            
        if self.send_command("is_within_safety_limits({})\n".format(','.join(map(str, robot_pose)))) == "False":
            raise ValueError("Cartesian position out of safety limits")

        command = f"{move_type}(p[{','.join(map(str, robot_pose))}], a={acceleration}, v={speed}, t={time}, r={radius})\n"
        return self.send_command(command)

    def get_joint_positions(self, *args, **kwargs):
        return self.send_command("get_actual_joint_positions()\n")

    def get_cartesian_position(self, *args, **kwargs):
        return self.send_command("get_actual_tcp_pose()\n")

    def stop_motion(self):
        return self.send_command("stopj(2)\n") # deceleration: 2 rad/s^2

    def get_robot_state(self):
        return self.send_command("get_robot_status()\n")
