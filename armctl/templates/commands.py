from abc import ABC, abstractmethod
from typing import List, Union


class Commands(ABC):
    """
    Abstract base class for communication protocols with a robot.

    Methods
    -------
    sleep(seconds):
        Pause the robot's operation for a specified number of seconds.
    move_joints(pos):
        Move the robot to specified joint positions.
    get_joint_positions():
        Retrieve the current joint positions of the robot.
    move_cartesian(pose):
        Move the robot to a specified Cartesian pose.
    get_cartesian_position():
        Retrieve the current Cartesian position of the robot.
    stop_motion():
        Stop all robot motion immediately.
    get_robot_state():
        Retrieve the current state of the robot.
    """

    @abstractmethod
    def sleep(self, seconds: float) -> None:
        pass

    @abstractmethod
    def move_joints(self, pos: List[float]) -> None:
        pass

    @abstractmethod
    def get_joint_positions(self) -> List[float]:
        pass

    @abstractmethod
    def move_cartesian(self, pose: List[float]) -> None:
        pass

    @abstractmethod
    def get_cartesian_position(self) -> List[float]:
        pass

    @abstractmethod
    def stop_motion(self) -> None:
        pass

    @abstractmethod
    def get_robot_state(self) -> Union[dict, str]:
        pass
