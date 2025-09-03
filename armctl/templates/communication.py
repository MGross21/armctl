from __future__ import annotations

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
    send_command(command, timeout):
        Send a command to the robot with an optional timeout.
    """

    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def send_command(self, command: str | dict, timeout: float) -> dict | str:
        pass
