"""
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
            logger.info(f"Connected to {self.__class__.__name__}({self.ip}:{self.send_port})" + ("(SEND/RECV)" if self.send_port == self.recv_port else "(SEND)"))

            # Create separate receive socket if different port is used
            if self.recv_port != self.send_port:
                self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.recv_socket.connect((self.ip, self.recv_port))
                logger.info(f"Connected to {self.__class__.__name__}({self.ip}:{self.recv_port}) (RECV)")
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
            raise ConnectionError(f"Failed to connect to {self.ip}:{self.send_port}|{self.recv_port}")

    def disconnect(self):
        """Disconnect from the robot by closing both sockets."""
        try:
            for sock in {self.send_socket, self.recv_socket}:
                if sock:
                    sock.close()
            self.send_socket = self.recv_socket = None
            logger.info(f"Disconnected from {self.__class__.__name__}")

        except Exception as e:
            logger.error(f"Disconnection failed: {e}")

    def send_command(self, 
                     command: str, 
                     timeout: float = 5.0,
                     suppress_input: bool = False,
                     suppress_output: bool = False, 
                     raw_response: bool = False) -> str | bytes:
        """
        Send a command to the robot and return the response.

        Parameters
        ----------
        command : str
            Command to send to the robot.
        timeout : float
            Timeout for response in seconds.
        suppress_input : bool
            Suppress input command logging.
        suppress_output : bool
            Suppress output/response logging.
        raw_response : bool
            Return raw bytes instead of decoded string.

        Returns
        -------
        str or bytes
            Decoded string or raw response bytes.

        Raises
        ------
        ConnectionError
            If socket isn't connected or fails.
        TimeoutError
            If response times out.
        """
        if not self.send_socket or not self.recv_socket:
            raise ConnectionError("Robot is not connected.")
        
        if not suppress_input:
            logger.send(f"Sending command: {command.strip().replace(chr(10), '//n')}")  # Explicitly show newline char in logger

        try:
            self.send_socket.sendall(command.encode())  # Send Command
            self.recv_socket.settimeout(timeout)        # Set timeout for receiving response
            response = self.recv_socket.recv(4096)      # Receive response
           
        except socket.timeout:
            raise TimeoutError("Command timed out")

        except Exception as e:
            raise ConnectionError(f"Failed to send command: {command}") from e
        
        if raw_response:
            if not suppress_output:
                logger.receive(f"Received raw response: {response}")
            return response

        # Preferred decoding chain for robot protocols
        for encoding in ("utf-8", "latin1"):
            try:
                decoded = response.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            decoded = response.decode("utf-8", errors="replace")

        if not suppress_output:
            logger.receive(f"Received response: {decoded}")

        return decoded