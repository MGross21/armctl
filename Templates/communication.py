from abc import ABC, abstractmethod

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