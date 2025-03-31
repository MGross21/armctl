
"""
Module: socket

This module provides a base class `SocketController` for implementing socket-based 
robot controllers. It provides methods for connecting, disconnecting, sending 
commands, and handling responses with enhanced debugging features.
"""
import socket
from .logger import logger
from .communication import Communication

class SocketController(Communication):
    """
    Base class for socket-based robot controllers with enhanced debugging features.

    Methods
    -------
    connect():
        Connect to the robot.
    disconnect():
        Disconnect from the robot.
    send_command(command, timeout=5.0):
        Send a command to the robot and wait for a response.
    """

    def __init__(self, ip, port):
        """
        Initialize the SocketController.

        Parameters
        ----------
        ip : str
            The IP address of the robot.
        port : int
            The port number to connect to.
        """
        self.ip = ip
        self.port = port
        self.socket = None

    def __enter__(self):
        """Context manager for automatic connection management."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Ensure disconnection when leaving the context."""
        self.disconnect()

    def connect(self):
        """Connect to the robot."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.ip, self.port))
            logger.info(f"Connected to {self.ip}:{self.port}")
            
            # Optional: Check initial response
            response = self.socket.recv(1024).decode()
            logger.debug(f"Initial response: {response}")
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise ConnectionError(f"Failed to connect to {self.ip}:{self.port}")

    def disconnect(self):
        """Disconnect from the robot."""
        try:
            if self.socket:
                self.socket.close()
                logger.info("Disconnected from robot")
                self.socket = None
        except Exception as e:
            logger.error(f"Disconnection failed: {e}")

    def send_command(self, command, timeout=5.0):
        """
        Send a command to the robot and wait for a response.

        Parameters
        ----------
        command : str
            The command to send to the robot.
        timeout : float
            Maximum time to wait for a response (default: 5.0 seconds).

        Returns
        -------
        str
            The decoded response from the robot.

        Raises
        ------
        ConnectionError
            If not connected to the robot or command sending fails.
        TimeoutError
            If the command times out while waiting for a response.
        """
        if not self.socket:
            raise ConnectionError("Not connected to the robot")

        try:
            # Send command
            logger.send(f"Sending command: {command}")
            self.socket.sendall(command.encode())

            # Wait for response with timeout handling
            self.socket.settimeout(timeout)
            response = self.socket.recv(1024).decode()
            
            logger.receive(f"Received response: {response}")
            return response

        except socket.timeout:
            logger.error("Command timed out")
            raise TimeoutError("Command timed out")
        
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            raise ConnectionError(f"Failed to send command: {command}")