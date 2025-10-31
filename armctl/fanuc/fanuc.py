from armctl.templates import Commands, Properties
from armctl.templates import PLCController as PLC
from armctl.utils import CommandCheck as cc


# Non-Operational (1/31/2025)
class Fanuc(PLC, Commands, Properties):
    def __init__(self, ip: str, port: int):
        super().__init__(ip, port)
        self.JOINT_RANGES = None
        self.MAX_JOINT_VELOCITY = None
        self.MAX_JOINT_ACCELERATION = None
        raise NotImplementedError(
            f"{self.__class__.__name__.upper()} is not yet supported."
        )

    def move_joints(self, pos, speed=1.0):
        cc.move_joints(self, pos, speed)
        return self.send_command(
            {"type": "move_joints", "positions": pos, "speed": speed}
        )

    def move_cartesian(self, pose, speed=1.0):
        cc.move_cartesian(self, pose)
        return self.send_command(
            {"type": "move_cartesian", "position": pose, "speed": speed}
        )

    def get_joint_positions(self):
        return self.send_command({"type": "get_joint_positions"})

    def get_cartesian_position(self):
        return self.send_command({"type": "get_cartesian_position"})

    def stop_motion(self):
        return self.send_command({"type": "stop"})

    def get_robot_state(self):
        return self.send_command({"type": "get_state"})
