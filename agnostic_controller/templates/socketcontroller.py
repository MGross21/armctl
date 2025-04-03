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
    def __init__(self, ip: str, port: int | tuple[int, int]):
        """
        Initialize the SocketController with support for separate send/receive ports.

        Parameters
        ----------
        ip : str
            The IP address of the robot.
        port : int or tuple[int, int]
            If an int is provided, it will be used for both sending and receiving.
            If a tuple (send_port, recv_port) is provided, the first is used for sending,
            and the second is used for receiving.
        """
        self.ip = ip
        if isinstance(port, int):
            self.send_port = self.recv_port = port
        else:
            self.send_port, self.recv_port = port

        self.send_socket = None
        self.recv_socket = None

    def __enter__(self):
        """Context manager for automatic connection management."""
        self.connect()
        return self

    def __exit__(self, _, __, ___):
        """Ensure disconnection when leaving the context."""
        self.disconnect()

    def connect(self):
        """Connect to the robot using separate sockets for sending and receiving if needed."""
        try:
            # Create send socket
            self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.send_socket.connect((self.ip, self.send_port))
            logger.info(f"Connected to {self.ip}:{self.send_port} " + ("(SEND/RECV)" if self.send_port == self.recv_port else "(SEND)"))

            # Create separate receive socket if different port is used
            if self.recv_port != self.send_port:
                self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.recv_socket.connect((self.ip, self.recv_port))
                logger.info(f"Connected to {self.ip}:{self.recv_port} (RECV)")
            else:
                self.recv_socket = self.send_socket  # Use the same socket if ports are identical

            # Optional: Check initial response
            try:
                response = self.recv_socket.recv(4096)
                decoded_response = response.decode("utf-8", errors="replace")
                logger.debug(f"Initial response: {decoded_response}")
            except Exception as e:
                logger.error(f"Error receiving initial response: {e}")
                raise ConnectionError("Failed to receive initial response")

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise ConnectionError(f"Failed to connect to {self.ip}:{self.send_port}/{self.recv_port}")

    def disconnect(self):
        """Disconnect from the robot by closing both sockets."""
        try:
            if self.send_socket:
                self.send_socket.close()
                logger.info("Disconnected socket (SEND)")
                self.send_socket = None
            
            if self.recv_socket and self.recv_socket != self.send_socket:
                self.recv_socket.close()
                logger.info("Disconnected socket (RECV)")
                self.recv_socket = None

        except Exception as e:
            logger.error(f"Disconnection failed: {e}")

    def send_command(self, 
                     command: str, 
                     timeout: float = 5.0,
                     suppress_input: bool=False,
                     suppress_output: bool = False, 
                     raw_response: bool = False) -> str | bytes:
        """
        Send a command to the robot and wait for a response.

        Parameters
        ----------
        command : str
            The command to send to the robot.
        timeout : float
            Maximum time to wait for a response (default: 5.0 seconds).
        suppress_input : bool
            If True, suppress logging of input command (default: False).
        suppress_output : bool
            If True, suppress logging of command and response (default: False).
        raw_response : bool
            If True, return the raw binary response instead of decoding it (default: False).

        Returns
        -------
        str or bytes
            The decoded response from the robot, or the raw binary response if `raw_response` is True.

        Raises
        ------
        ConnectionError
            If not connected to the robot or command sending fails.
        TimeoutError
            If the command times out while waiting for a response.
        """
        if not self.send_socket:
            raise ConnectionError("Not connected to the robot")

        try:
            # Send command
            if not suppress_input:
                logger.send(f"Sending command: {command.strip().replace(chr(10), '//n')}") # replace newlines for clarity

            self.send_socket.sendall(command.encode())

            # Wait for response with timeout handling
            self.recv_socket.settimeout(timeout)
            response = self.recv_socket.recv(4096)

            if raw_response:
                if not suppress_output:
                    logger.receive(f"Received raw response: {response}")
                return response

            # Decode response
            try:
                decoded_response = response.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    decoded_response = response.decode("ISO-8859-1")  # Alternative encoding
                except UnicodeDecodeError:
                    decoded_response = response.decode("latin1", errors="replace")  # Last resort

            if not suppress_output:
                logger.receive(f"Received response: {decoded_response}")
            return decoded_response

        except socket.timeout:
            logger.error("Command timed out")
            raise TimeoutError("Command timed out")
        
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            raise ConnectionError(f"Failed to send command: {command}")