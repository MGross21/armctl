from .elephant_robotics import ElephantRobotics

# My Cobot Pro 600
class Pro600(ElephantRobotics):
        def __init__(self, ip:str, port:int):
            super().__init__(ip, port)
            super().HOME_POSITION = [0,-90, 90,-90,-90,0]
            super().JOINT_RANGES = [
                (-180.00, 180.00),
                (-270.00, 90.00),
                (-150.00, 150.00),
                (-260.00, 80.00),
                (-168.00, 168.00),
                (-174.00, 174.00)
            ]
            super().DOF = len(super().JOINT_RANGES)

        async def home(self):
            await super().move_joints(super().HOME_POSITION, speed=750)
