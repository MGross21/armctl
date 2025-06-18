from abc import ABC, abstractmethod
from typing import Union

class Communication(ABC):
    """
    Abstract base class for communication protocols with a robot.

    Methods
    -------
    connect():
        Connect to the robot.
    disconnect():
        Disconnect from the robot.
    send_command(command, timeout):
        Send a command to the robot with an optional timeout.
    """
    @abstractmethod
    def connect(self) -> None: pass
    @abstractmethod
    def disconnect(self) -> None: pass
    @abstractmethod
    def send_command(self, command: Union[str, dict], timeout: float) -> Union[dict, str]: pass