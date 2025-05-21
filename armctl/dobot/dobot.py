from armctl.templates import SocketController as SCT

class Dobot(SCT):
    def __init__(self, ip: str, port: int):
        super().__init__(ip, port)
        raise NotImplementedError(f"{self.__class__.__name__.upper()} is not yet supported.")

    def sleep(self, seconds):
        self.send_command(f"sleep({seconds})")

    def move_joints(self, joint_positions, *args, **kwargs) -> str:
        "MovJ"

        if len(joint_positions) != kwargs.get("DOF", 4):
            raise ValueError("Joint positions must have 4 elements")
        
        joint_ranges = [
            (-135.00, 135.00),
            (-5.00, 80.00),
            (-10.00, 85.00),
            (-145.00, 145.00)
        ]
        for i, (low, high) in enumerate(joint_ranges):
            if not (low <= joint_positions[i] <= high):
                raise ValueError(f"Joint {i+1} angle out of range: {low} ~ {high}")
            
        command = "MOVJ({})".format(','.join(map(str, joint_positions)))
        return self.send_command(command)

    def move_cartesian(self, robot_pose, *args, **kwargs) -> str:
        "MOVEL"

        if len(robot_pose) == 3:
            robot_pose.append(0)

        # Now check again if the robot pose has 4 elements
        if len(robot_pose) != 4:    
            raise ValueError("Robot pose must have 3 ([x, y, z]) or 4 elements: [x, y, z, rz]")
        
        command = "MOVEL({})".format(','.join(map(str, robot_pose)))
        return self.send_command(command)

    def get_joint_positions(self): pass

    def get_cartesian_position(self): pass

    def stop_motion(self): pass

    def get_robot_state(self): pass

    def move_arc(self, command):
        """The trajectory of ARC mode is an arc, which is determined by three points (the current point, any point and the end point on the arc)"""
        if len(command) != 3:
            raise ValueError("Invalid ARC command. Must have 3 points")
        
        self.send_command(f"ARC({','.join(map(str, command))})")

    def move_jump(self, command):
        """If the movement of two points is required to lift upwards by amount of height, such as sucking up, grabbing, you can choose JUMP"""
        if len(command) != 2:
            raise ValueError("Invalid JUMP command. Must have 2 points")
        
        self.send_command(f"JUMP({','.join(map(str, command))})")
