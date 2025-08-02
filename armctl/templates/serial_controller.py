"""
This module provides a base class `SerialController` for implementing serial-based
robot controllers. It provides methods for connecting, disconnecting, sending
commands, and handling responses with enhanced debugging features.

THIS CLASS IS NOT IMPLEMENTED YET.
"""

from .communication import Communication
from .logger import logger
import serial
import threading
import time


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
        self._serial = None
        self._lock = threading.Lock()

    def __enter__(self):
        """Context manager for automatic connection management."""
        self.connect()
        return self

    def __exit__(self, _, __, ___):
        """Ensure disconnection when leaving the context."""
        self.disconnect()

    def connect(self):
        """Establishes the serial connection to the robot."""
        if self._serial and self._serial.is_open:
            return
        try:
            self._serial = serial.Serial(self.port, self.baudrate, timeout=5)
            logger.info(f"Connected to {self.__class__.__name__}({self.port}:{self.baudrate})")
        except serial.SerialException:
            raise

    def disconnect(self):
        """Closes the serial connection to the robot."""
        if self._serial and self._serial.is_open:
            self._serial.close()
            logger.info(f"Disconnected from {self.__class__.__name__}")

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

        Returns
        -------
        str
            The response from the robot.
        """
        if not self._serial or not self._serial.is_open:
            raise ConnectionError(f"Robot is not connected. Call {self.connect.__name__} first.")
        with self._lock:
            try:
                logger.send(f"Sending command: {command}")
                self._serial.write((command + '\n').encode())
                self._serial.flush()
                start_time = time.time()
                response = b''
                while True:
                    if self._serial.in_waiting > 0:
                        response += self._serial.read(self._serial.in_waiting)
                        if response.endswith(b'\n'):
                            break
                    if (time.time() - start_time) > timeout:
                        raise TimeoutError("Command timed out.")
                    time.sleep(0.01)
                logger.receive(f"Received response: {response}")
                return response.decode(errors='ignore').strip()
            except serial.SerialException as e:
                raise
