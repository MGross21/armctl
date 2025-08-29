from .elephant_robotics import ElephantRobotics, uu


class Pro600(ElephantRobotics):
    def __init__(self, ip: str = "192.168.1.159", port: int = 5001):
        """Elephant Robotics myCobot Pro600"""
        super().__init__(ip, port)
        self.HOME_POSITION = uu.joints2rad([0, -90, 90, -90, -90, 0])

    def home(self):
        """
        Move the robot to the home position: `[0, -90, 90, -90, -90, 0]`.
        """
        self.move_joints(self.HOME_POSITION, speed=750)
