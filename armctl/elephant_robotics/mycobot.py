from .elephant_robotics import ElephantRobotics


class Pro600(ElephantRobotics):
    def __init__(self, ip: str = "192.168.1.159", port: int = 5001):
        """Elephant Robotics myCobot Pro600"""
        super().__init__(ip, port)
        self.HOME_POSITION = [0, -90, 90, -90, -90, 0]
        self.JOINT_RANGES = [
            (-180.00, 180.00),
            (-270.00, 90.00),
            (-150.00, 150.00),
            (-260.00, 80.00),
            (-168.00, 168.00),
            (-174.00, 174.00),
        ]
        self.DOF = len(self.JOINT_RANGES)

        self.__class__.__name__ = f"{self.__class__.__bases__[0].__name__} {__name__.split('.')[-1]} {self.__class__.__name__}"

    def home(self):
        """
        Move the robot to the home position: `[0, -90, 90, -90, -90, 0]`.
        """
        self.move_joints(self.HOME_POSITION, speed=750)
