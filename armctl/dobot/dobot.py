import math

from armctl.templates import Commands, Properties
from armctl.templates import SerialController as SCT
from armctl.utils import CommandCheck as cc
from armctl.utils import units as uu

### Notes ###
# - Command Format: CMD(arg)
# - Command units are degrees & mm.


class Dobot(SCT, Commands, Properties):
    def __init__(self, ip: str, port: int):
        super().__init__(ip, port)
        self.JOINT_RANGES = uu.joints2rad(
            [
                (-135.00, 135.00),
                (-5.00, 80.00),
                (-10.00, 85.00),
                (-145.00, 145.00),
            ]
        )
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
            pose (list or tuple): Target position as [x, y, z, r]. x, y, z are in meters and r is in radians.

        Returns:
            str: The response from the robot after executing the MOVEL command.

        Notes:
            - The method sends a MOVEL command to the robot controller.
            - The pose is expected in m for x, y, z and radians for r.
        """
        cc.move_cartesian(self, pose)
        # Convert x, y, z from meters to millimeters, r from radians to degrees

        command = "MOVEL({})".format(
            ",".join(
                map(
                    str,
                    [
                        pose[0] * 1000,  # x in mm
                        pose[1] * 1000,  # y in mm
                        pose[2] * 1000,  # z in mm
                        math.degrees(pose[3]),  # r in degrees
                    ],
                )
            )
        )
        return self.send_command(command)

    def get_joint_positions(self):
        pass

    def get_cartesian_position(self):
        pass

    def stop_motion(self):
        pass

    def get_robot_state(self):
        pass
