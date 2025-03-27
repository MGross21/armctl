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
from .communication import Communication
from .logger import logger

class SocketController(Communication):
    # __doc__ = Communication.__doc__
    """
    Base class for socket-based robot controllers.

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
        self.ip, self.port, self.socket = ip, port, None
        self.isConnected = False
    
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.disconnect()

    def __format__(self, format_spec):
        if format_spec == "f":
            return f"{self.__class__.__name__}({self.ip}:{self.port})"
        else:
            return super().__format__(format_spec)

    async def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            await asyncio.get_event_loop().sock_connect(self.socket, (self.ip, self.port))
            logger.info(f"Connected to {self:f}")
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise ConnectionError(f"Failed to connect to {self:f}")
        self.isConnected = True

    async def disconnect(self):
        if self.socket:
            self.socket.close()
            self.socket = None
            logger.info("Disconnected from robot")
        self.isConnected = False

    async def send_command(self, command, timeout=5.0):
        """
        Asynchronously send a command to the robot and wait for a response.
        
        Parameters
        ----------
        command : str, dict, or bytes
            The command to send to the robot
        timeout : float, optional
            Maximum time to wait for a response, by default 5.0
            
        Returns
        -------
        Any
            The decoded response from the robot
        
        Raises
        ------
        ConnectionError
            If not connected to the robot or command sending fails
        TimeoutError
            If the command times out
        """
        if not self.socket:
            raise ConnectionError(f"Not connected to {self:f}")
        
        try:
            logger.send(f"{self:f}: \t{command}")
            
            # Process and encode command based on type
            command, response_format = self._format_command(command)
            
            # Send the command
            await asyncio.wait_for(self._send(command), timeout=timeout)
            
            # Receive response
            response = await asyncio.wait_for(self._receive(), timeout=timeout)
            
            # Decode the response
            decoded_response = self._decode_response(response, response_format)
            
            logger.receive(f"{self:f}: \t{decoded_response}")
            return decoded_response
        
        except asyncio.TimeoutError:
            logger.error("Command timed out")
            raise TimeoutError("Command timed out")
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            raise ConnectionError(f"Failed to send command to the robot: {str(e)}")
        finally:
            print()

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

    async def _get_response(self, timeout, wait_for_reponse_str, response_format):
        raise DeprecationWarning("Not Used")
        """Get response from socket, optionally waiting for specific string."""
        if not wait_for_reponse_str:
            return await asyncio.wait_for(self._receive(), timeout=timeout)
        
        # Wait for specific string in response
        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            remaining = timeout - (asyncio.get_event_loop().time() - start_time)
            response = await asyncio.wait_for(self._receive(), timeout=remaining)
            
            # Check if the expected string is in the response
            if self._response_contains_string(response, wait_for_reponse_str, response_format):
                return response
        
        # If we exit the loop without breaking, we timed out
        raise TimeoutError(f"Timed out waiting for '{wait_for_reponse_str}' in response")

    def _response_contains_string(self, response, search_string, response_format):
        """Check if response contains the specified string based on format."""
        if response_format in ['dict', 'str']:
            return search_string in response.decode('utf-8')
        elif response_format == 'bytes':
            return search_string.encode('utf-8') in response
        return False

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
        await asyncio.get_event_loop().sock_sendall(self.socket, data)

    async def _receive(self, buffer_size=1024):
        return await asyncio.get_event_loop().sock_recv(self.socket, buffer_size)
