from armctl.templates import Commands
from armctl.templates import SocketController as Socket
import time

TEST_STRING_PREFIX = "MOCK!!"

def _format_mock_command(method_name: str, arg=None):
    if arg is not None:
        return f"{TEST_STRING_PREFIX} {method_name.upper()}: {arg}"
    return f"{TEST_STRING_PREFIX} {method_name.upper()}"

class MockSerialRobot(Socket, Commands):
    def __init__(self, ip: str = "127.0.0.1", port: int = 8_000):
        super().__init__(ip, port)

    def move_joints(self, pos) -> str:
        return self.send_command(_format_mock_command(self.move_joints.__name__, pos))

    def move_cartesian(self, pose) -> str:
        return self.send_command(_format_mock_command(self.move_cartesian.__name__, pose))

    def get_joint_positions(self) -> str:
        return self.send_command(_format_mock_command(self.get_joint_positions.__name__))

    def get_cartesian_position(self) -> str:
        return self.send_command(_format_mock_command(self.get_cartesian_position.__name__))

    def stop_motion(self) -> str:
        return self.send_command(_format_mock_command(self.stop_motion.__name__))

    def get_robot_state(self) -> str:
        return self.send_command(_format_mock_command(self.get_robot_state.__name__))
    
    def sleep(self, seconds):
        return time.sleep(seconds)