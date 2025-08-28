from armctl.templates import SerialController as SCT
from armctl.templates import Commands
from armctl.templates import Properties
from armctl.utils import CommandCheck as cc

import math


class Dobot(SCT, Commands, Properties):
    def __init__(self, ip: str, port: int):
        super().__init__(ip, port)
        self.JOINT_RANGES = [
            (-math.radians(135.00), math.radians(135.00)),
            (-math.radians(5.00), math.radians(80.00)),
            (-math.radians(10.00), math.radians(85.00)),
            (-math.radians(145.00), math.radians(145.00)),
        ]
        self.MAX_JOINT_VELOCITY = None
        self.MAX_JOINT_ACCELERATION = None

        raise NotImplementedError(
            f"{self.__class__.__name__.upper()} is not yet supported."
        )

    def sleep(self, seconds):
        cc.sleep(seconds)
        self.send_command(f"sleep({seconds})")

    def move_joints(self, pos) -> str:
        "MovJ"

        cc.move_joints(self, pos)

        command = "MOVJ({})".format(",".join(map(str, pos)))
        return self.send_command(command)

    def move_cartesian(self, pose) -> str:
        """
        Moves the robot arm to a specified Cartesian position.

        Parameters:
            pose (list or tuple): Target position as [x, y, z, r].

        Returns:
            str: The response from the robot after executing the MOVEL command.

        Notes:
            - The method sends a MOVEL command to the robot controller.
            - The pose is expected in m for x, y, z and radians for r.
        """
        cc.move_cartesian(self, pose)

        command = "MOVEL({})".format(",".join(map(str, pose)))
        return self.send_command(command)

    def get_joint_positions(self):
        pass

    def get_cartesian_position(self):
        pass

    def stop_motion(self):
        pass

    def get_robot_state(self):
        pass

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
