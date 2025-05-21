from abc import ABC, abstractmethod

class Commands(ABC):
    """
    Abstract base class for communication protocols with a robot.

    Methods
    -------
    sleep(seconds):
        Pause the robot's operation for a specified number of seconds.
    home():
        Move the robot to its home position.
    move_joints(joint_positions, *args, **kwargs):
        Move the robot to specified joint positions.
    get_joint_positions():
        Retrieve the current joint positions of the robot.
    move_cartesian(robot_pose, *args, **kwargs):
        Move the robot to a specified Cartesian pose.
    get_cartesian_position():
        Retrieve the current Cartesian position of the robot.
    stop_motion():
        Stop all robot motion immediately.
    get_robot_state():
        Retrieve the current state of the robot.
    """
    @abstractmethod
    def sleep(self, seconds): pass

    @abstractmethod
    def move_joints(self, joint_positions,*args, **kwargs): pass

    @abstractmethod
    def get_joint_positions(self, *args, **kwargs): pass

    @abstractmethod
    def move_cartesian(self, robot_pose, *args, **kwargs): pass

    @abstractmethod
    def get_cartesian_position(self, *args, **kwargs): pass

    @abstractmethod
    def stop_motion(self): pass

    @abstractmethod
    def get_robot_state(self): pass