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

    def __init__(self, ip: str, port: int):
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
            try:
                response = self.socket.recv(4096)
                decoded_response = response.decode("utf-8", errors="replace")
                logger.debug(f"Initial response: {decoded_response}")
            except Exception as e:
                logger.error(f"Error receiving initial response: {e}")
                raise ConnectionError("Failed to receive initial response")

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

    def send_command(self, command: str, timeout: float = 5.0, suppress_output: bool = False) -> str:
        """
        Send a command to the robot and wait for a response.

        Parameters
        ----------
        command : str
            The command to send to the robot.
        timeout : float
            Maximum time to wait for a response (default: 5.0 seconds).
        suppress_output : bool
            If True, suppress logging of command and response (default: False).

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
            if not suppress_output:
                logger.info(f"Sending command: {command}")
            self.socket.sendall((command + "\n").encode())  # Ensure newline character

            # Wait for response with timeout handling
            self.socket.settimeout(timeout)
            
            # Read raw binary data first and decode safely
            try:
                response = self.socket.recv(4096)  # Increased buffer size for larger responses
                decoded_response = response.decode("utf-8", errors="replace")
                if not suppress_output:
                    logger.info(f"Received response: {decoded_response}")
                return decoded_response
            
            except UnicodeDecodeError:
                logger.error("Failed to decode response using UTF-8")
                raw_response = self.socket.recv(4096)
                fallback_response = raw_response.decode("ISO-8859-1", errors="replace")
                logger.debug(f"(Fallback decoding) Response: {fallback_response}")
                return fallback_response

        except socket.timeout:
            logger.error("Command timed out")
            raise TimeoutError("Command timed out")
        
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            raise ConnectionError(f"Failed to send command: {command}")