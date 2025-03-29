"""
Module: socket

This module provides a base class `SocketController` for implementing socket-based 
robot controllers. It extends the `Communication` class and provides asynchronous 
methods for connecting, disconnecting, and sending commands to a robot over a 
socket connection.

Classes
-------
SocketController:
    A base class for managing socket-based communication with a robot. It includes 
    methods for establishing a connection, sending commands, and handling responses 
    asynchronously.
"""
import asyncio
import socket
import json
import zlib
from .communication import Communication
from .logger import logger

class SocketController(Communication):
    """
    Base class for socket-based robot controllers with enhanced performance and streamlined functionality.

    Methods
    -------
    connect():
        Asynchronously connect to the robot.
    disconnect():
        Asynchronously disconnect from the robot.
    send_command(command, timeout=5.0):
        Asynchronously send a command to the robot with an optional timeout.
    """

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = None
        self.reader = None
        self.writer = None

    async def __aenter__(self):
        """Async context manager for automatic connection management."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Ensure disconnection when leaving the context."""
        await self.disconnect()

    def __format__(self, format_spec):
        """Format the connection string for logging."""
        return f"{self.__class__.__name__}({self.ip}:{self.port})" if format_spec == "f" else super().__format__(format_spec)

    async def connect(self):
        """Asynchronously connect to the robot."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setblocking(False)  # Non-blocking socket for async operations
            await asyncio.get_event_loop().sock_connect(self.socket, (self.ip, self.port))
            self.reader, self.writer = await asyncio.open_connection(sock=self.socket)
            logger.info(f"Connected to {self:f}")
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise ConnectionError(f"Failed to connect to {self:f}")

    async def disconnect(self):
        """Asynchronously disconnect from the robot."""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        if self.socket:
            self.socket.close()
        logger.info("Disconnected from robot")

    async def send_command(self, command, timeout=5.0):
        """
        Asynchronously send a command to the robot and wait for a response.

        Parameters
        ----------
        command : str, dict, or bytes
            The command to send to the robot.
        timeout : float, optional
            Maximum time to wait for a response, by default 5.0

        Returns
        -------
        Any
            The decoded response from the robot.
        
        Raises
        ------
        ConnectionError
            If not connected to the robot or command sending fails.
        TimeoutError
            If the command times out.
        """
        if not self.writer:
            raise ConnectionError(f"Not connected to {self:f}")

        try:
            logger.send(f"{self:f}: \t{command}")

            # Format and encode command based on type
            command, response_format = self._format_command(command)

            # Send command asynchronously
            await asyncio.wait_for(self._send(command), timeout=timeout)

            # Receive response asynchronously
            response = await asyncio.wait_for(self._receive(), timeout=timeout)

            # Decode and return the response
            decoded_response = self._decode_response(response, response_format)
            logger.receive(f"{self:f}: \t{decoded_response}")
            return decoded_response

        except asyncio.TimeoutError:
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

    async def _send(self, data):
        """Send data using asyncio StreamWriter."""
        # Compress data for large payloads to optimize transmission
        data = self._compress_data(data)
        self.writer.write(data)
        await self.writer.drain()  # Ensure all data is sent

    async def _receive(self, buffer_size=1024):
        """Receive data asynchronously using asyncio StreamReader."""
        return await self.reader.read(buffer_size)

    def _compress_data(self, data):
        """Compress data for better network efficiency when it's large."""
        if len(data) > 1024:  # Compress data larger than 1KB
            return zlib.compress(data)
        return data

    def _decompress_data(self, data):
        """Decompress data when receiving compressed responses."""
        try:
            return zlib.decompress(data)
        except Exception:
            return data  # If not compressed, return data as is