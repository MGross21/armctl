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
from .templates import Communication, logger

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
        if not self.socket:
            raise ConnectionError(f"Not connected to {self:f}")
        
        try:
            logger.send(f"{self:f}: \t{command}")
            
            if isinstance(command, dict):
                command = json.dumps(command).encode('utf-8')
                response_format = 'dict'
            elif isinstance(command, str):
                command = command.encode('utf-8')
                response_format = 'str'
            elif isinstance(command, bytes):
                response_format = 'bytes'
            else:
                raise TypeError("Unsupported command type")
            
            await asyncio.wait_for(self._send(command), timeout=timeout)
            response = await asyncio.wait_for(self._receive(), timeout=timeout)
            
            if response_format == 'dict':
                decoded_response = json.loads(response.decode('utf-8'))
            elif response_format == 'str':
                decoded_response = response.decode('utf-8')
            elif response_format == 'bytes':
                decoded_response = response
            else:
                raise ValueError("Unsupported response format")
            
            logger.receive(f"{self:f}: \t{decoded_response}")
            return decoded_response
    
        except asyncio.TimeoutError:
            logger.error("Command timed out")
            raise TimeoutError("Command timed out")
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            raise ConnectionError("Failed to send command to the robot")
        finally:
            print()

    async def _send(self, data):
        await asyncio.get_event_loop().sock_sendall(self.socket, data)

    async def _receive(self, buffer_size=1024):
        return await asyncio.get_event_loop().sock_recv(self.socket, buffer_size)
