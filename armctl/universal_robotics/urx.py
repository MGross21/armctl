from .universal_robotics import UniversalRobotics as UR
import math


class UR3(UR):
    def __init__(self, ip: str, port: int = 30_002):
        super().__init__(ip, port)
        self.HOME_POSITION = [
            math.pi / 2,
            -math.pi / 2,
            math.pi / 2,
            -math.pi / 2,
            -math.pi / 2,
            0,
        ]  # Not Verified, but assumed similar to UR5

    def home(self):
        self.move_joints(self.HOME_POSITION, speed=0.1)


class UR5(UR):
    def __init__(self, ip: str = "192.168.1.111", port: int = 30_002):
        super().__init__(ip, port)
        self.HOME_POSITION = [
            math.pi / 2,
            -math.pi / 2,
            math.pi / 2,
            -math.pi / 2,
            -math.pi / 2,
            0,
        ]  # VERIFIED VENTION TABLE UR5: 4/2/2025

    def home(self):
        self.move_joints(self.HOME_POSITION, speed=0.1)


# Mirror the UR5e class to UR5
class UR5e(UR5):
    def __init__(self, ip: str = "192.168.1.111", port: int = 30_002):
        super().__init__(ip, port)


class UR10(UR):
    def __init__(self, ip: str, port: int = 30_002):
        super().__init__(ip, port)
        self.HOME_POSITION = [
            math.pi / 2,
            -math.pi / 2,
            math.pi / 2,
            -math.pi / 2,
            -math.pi / 2,
            0,
        ]  # Default home position for UR10

    def home(self):
        self.move_joints(self.HOME_POSITION, speed=0.1)


class UR16(UR):
    def __init__(self, ip: str, port: int = 30_002):
        super().__init__(ip, port)
        self.HOME_POSITION = [
            math.pi / 2,
            -math.pi / 2,
            math.pi / 2,
            -math.pi / 2,
            -math.pi / 2,
            0,
        ]  # Default home position for UR16

    def home(self):
        self.move_joints(self.HOME_POSITION, speed=0.1)
