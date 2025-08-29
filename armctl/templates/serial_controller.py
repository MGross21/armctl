"""
This module provides a base class `SerialController` for implementing serial-based
robot controllers. It provides methods for connecting, disconnecting, sending
commands, and handling responses with enhanced debugging features.

THIS CLASS IS NOT IMPLEMENTED YET.
"""

from __future__ import annotations

from .communication import Communication


class SerialController(Communication):
    def __init__(self, port: str, baudrate: int = 115200):
        """
        Initialize the SerialController with support for separate send/receive ports.

        Parameters
        ----------
        port : str
            The serial port of the robot.
        baudrate : int
            The baud rate for the serial connection.
        """
        self.port = port
        self.baudrate = baudrate

    def __enter__(self):
        """Context manager for automatic connection management."""
        self.connect()
        return self

    def __exit__(self, _, __, ___):
        """Ensure disconnection when leaving the context."""
        self.disconnect()

    def connect(self):
        raise NotImplementedError("Serial connection not implemented yet.")

    def disconnect(self):
        raise NotImplementedError("Serial disconnection not implemented yet.")

    def send_command(self, command, timeout=5, **kwargs):
        """
        Send a command to the robot with an optional timeout.

        Parameters
        ----------
        command : str
            The command to send.
        timeout : float
            The timeout for the command in seconds.
        **kwargs : dict
            Additional arguments for the command.
        """
        raise NotImplementedError("Serial command sending not implemented yet.")
