"""
Module: socket

This module provides a base class `SocketController` for implementing socket-based 
robot controllers. It extends the `Communication` class and provides methods for 
connecting, disconnecting, and sending commands to a robot over a socket connection.

Classes
-------
SocketController:
    A base class for managing socket-based communication with a robot. It includes 
    methods for establishing a connection, sending commands, and handling responses.
"""
import socket
import json
from .communication import Communication
from .logger import logger
class SocketController(Communication):
    """
    Base class for socket-based robot controllers with enhanced performance and streamlined functionality.

    Methods
    -------
    connect():
        Connect to the robot.
    disconnect():
        Disconnect from the robot.
    send_command(command, timeout=5.0):
        Send a command to the robot with an optional timeout.
    """

    def __init__(self, ip, port):
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

    def __format__(self, format_spec):
        """Format the connection string for logging."""
        return f"{self.__class__.__name__}({self.ip}:{self.port})" if format_spec == "f" else super().__format__(format_spec)

    def connect(self):
        """Connect to the robot."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.ip, self.port))
            logger.info(f"Connected to {self:f}")
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise ConnectionError(f"Failed to connect to {self:f}")

    def disconnect(self):
        """Disconnect from the robot."""
        try:
            if self.socket:
                self.socket.close()
            logger.info("Disconnected from robot")
        except Exception as e:
            logger.error(f"Disconnection failed: {e}")

    def send_command(self, command, timeout=5.0):
        """
        Send a command to the robot and wait for a response.

        Parameters
        ----------
        command : str, dict, or bytes
            The command to send to the robot.
        timeout : float
            Maximum time to wait for a response (default: 5.0 seconds).

        Returns
        -------
        Any
            The decoded response from the robot.

        Raises
        ------
        ConnectionError
            If not connected to the robot or command sending fails.
        TimeoutError
            If the command times out while waiting for a response.
        """
        if not self.socket:
            raise ConnectionError(f"Not connected to {self:f}")

        try:
            logger.send(f"{self:f}: \t{command}")

            # Format and encode command based on type
            command, response_format = self._format_command(command)

            # Send command
            self._send(command)

            # Receive response with dynamic buffer handling
            response = self._receive(timeout=timeout)

            # Decode and return the response
            decoded_response = self._decode_response(response, response_format)
            logger.receive(f"{self:f}: \t{decoded_response}")
            return decoded_response

        except socket.timeout:
            logger.error("Command timed out")
            raise TimeoutError("Command timed out")
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            raise ConnectionError(f"Failed to send command to the robot: {str(e)}")

    def _format_command(self, command):
        """Format and encode command based on its type."""
        if isinstance(command, dict):
            return json.dumps(command).encode('utf-8'), 'dict'
        elif isinstance(command, str):
            return command.encode('utf-8'), 'str'
        elif isinstance(command, bytes):
            return command, 'bytes'
        else:
            raise TypeError("Unsupported command type")

    def _decode_response(self, response, response_format):
        """Decode response based on format."""
        if response_format == 'dict':
            return json.loads(response.decode('utf-8'))
        elif response_format == 'str':
            return response.decode('utf-8')
        elif response_format == 'bytes':
            return response
        else:
            raise ValueError("Unsupported response format")

    def _send(self, data):
        """Send data using socket."""
        try:
            self.socket.sendall(data)
        except Exception as e:
            logger.error(f"Failed to send data: {e}")
            raise ConnectionError("Failed to send data")

    def _receive(self, buffer_size=1024, timeout=5.0):
        """
        Receive data using socket with dynamic buffer handling.

        Parameters
        ----------
        buffer_size : int
            The size of each chunk to read from the socket (default: 1024 bytes).
        timeout : float
            Maximum time to wait for a response (default: 5.0 seconds).

        Returns
        -------
        bytes
            The complete response from the robot.

        Raises
        ------
        ConnectionError
            If the connection is closed unexpectedly.
        TimeoutError
            If no valid response is received within the timeout period.
        """
        self.socket.settimeout(timeout)
        try:
            data = self.socket.recv(buffer_size)
            if not data:  # Handle connection closure
                raise ConnectionError("Connection closed unexpectedly")
            return data
        except socket.timeout:
            raise TimeoutError("Response timed out")
