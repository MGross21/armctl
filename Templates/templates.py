"""
This module defines abstract base classes and custom logging levels for robot communication and control.

Classes
-------
Communication : ABC
    Abstract base class for communication protocols with a robot.
Commands : ABC
    Abstract base class for defining robot commands.
"""

from abc import ABC, abstractmethod
import logging

class Communication(ABC):
    """
    Abstract base class for communication protocols with a robot.

    Methods
    -------
    connect():
        Connect to the robot.
    disconnect():
        Disconnect from the robot.
    send_command(command, timeout=5.0):
        Send a command to the robot with an optional timeout.
    """
    @abstractmethod
    async def connect(self): pass
    @abstractmethod
    async def disconnect(self): pass
    @abstractmethod
    async def send_command(self, command, timeout=5.0): pass

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
    async def sleep(self, seconds): pass

    @abstractmethod
    async def home(self): pass

    @abstractmethod
    async def move_joints(self, joint_positions,*args, **kwargs): pass

    @abstractmethod
    async def get_joint_positions(self): pass

    @abstractmethod
    async def move_cartesian(self, robot_pose, *args, **kwargs): pass

    @abstractmethod
    async def get_cartesian_position(self): pass

    @abstractmethod
    async def stop_motion(self): pass

    @abstractmethod
    async def get_robot_state(self): pass

##### CUSTOM LOGGING LEVELS #####
SEND_LEVEL = logging.INFO + 1
RECEIVE_LEVEL = logging.INFO + 2

logging.addLevelName(SEND_LEVEL, "SEND")
logging.addLevelName(RECEIVE_LEVEL, "RECV")

def send(self, message, *args, **kws):
    if self.isEnabledFor(SEND_LEVEL):
        self._log(SEND_LEVEL, message, args, **kws)

def receive(self, message, *args, **kws):
    if self.isEnabledFor(RECEIVE_LEVEL):
        self._log(RECEIVE_LEVEL, message, args, **kws)

logging.Logger.send = send
logging.Logger.receive = receive

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
