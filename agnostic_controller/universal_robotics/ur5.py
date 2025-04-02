from .universal_robotics import UniversalRobotics as UR

class UR5(UR):
        def __init__(self, ip:str):
            super().__init__(ip)
            self.HOME_POSITION = [0, -90, 90, -90, -90, 0]

        def home(self):
            self.move_joints(self.HOME_POSITION, speed=0.1)

# Mirror the UR5e class to UR5
UR5e = UR5