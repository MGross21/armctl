"""
SerialController: robot-agnostic base class for serial-port communication.
"""

from __future__ import annotations

import threading
import time

import serial

from .communication import Communication
from .logger import logger


class SerialController(Communication):
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 5.0):
        """
        Parameters
        ----------
        port : str
            Serial port path (e.g. ``'/dev/ttyUSB0'``, ``'COM3'``).
        baudrate : int
            Baud rate.
        timeout : float
            Default read timeout in seconds.
        """
        self.port = port
        self.baudrate = baudrate
        self._timeout = timeout
        self._serial: serial.Serial | None = None
        self._lock = threading.Lock()

    def __enter__(self) -> SerialController:
        self.connect()
        return self

    def __exit__(self, *_) -> None:
        self.disconnect()

    def connect(self) -> None:
        """Open the serial port. No-op if already open."""
        if self._serial and self._serial.is_open:
            return
        try:
            self._serial = serial.Serial(
                self.port, self.baudrate, timeout=self._timeout
            )
            logger.info(
                f"Connected to {self.__class__.__name__}({self.port}:{self.baudrate})"
            )
        except serial.SerialException:
            raise

    def disconnect(self) -> None:
        """Close the serial port."""
        if self._serial and self._serial.is_open:
            self._serial.close()
            logger.info(f"Disconnected from {self.__class__.__name__}")
        self._serial = None

    def send_command(
        self,
        command: str | bytes,
        timeout: float = 5.0,
        suppress_input: bool = False,
        suppress_output: bool = False,
        raw_response: bool = False,
    ) -> str | bytes:
        """
        Send a command and return the response.

        Parameters
        ----------
        command : str | bytes
            ``str`` — encoded UTF-8 with ``'\\n'`` appended.
            ``bytes`` — sent as-is.
        timeout : float
            Per-command read timeout in seconds.
        suppress_input : bool
            Skip send-side log entry.
        suppress_output : bool
            Skip receive-side log entry.
        raw_response : bool
            Return raw ``bytes`` instead of a decoded ``str``.

        Returns
        -------
        str or bytes
            Decoded response string, or raw bytes when ``raw_response=True``.

        Raises
        ------
        ConnectionError
            Port is not open.
        TimeoutError
            No newline-terminated response within *timeout* seconds.
        serial.SerialException
            Low-level serial error.
        """
        if not self._serial or not self._serial.is_open:
            raise ConnectionError("Not connected. Call connect() first.")

        with self._lock:
            if isinstance(command, bytes):
                payload = command
                if not suppress_input:
                    logger.send(f"Sending bytes: {command.hex()}")
            else:
                payload = (command + "\n").encode()
                if not suppress_input:
                    logger.send(f"Sending command: {command.strip()}")

            self._serial.reset_input_buffer()
            self._serial.write(payload)
            self._serial.flush()

            deadline = time.monotonic() + timeout
            response = bytearray()

            while True:
                if self._serial.in_waiting:
                    response.extend(self._serial.read(self._serial.in_waiting))
                    if response.endswith(b"\n"):
                        break
                if time.monotonic() > deadline:
                    raise TimeoutError(f"Command timed out after {timeout}s")
                time.sleep(0.005)

            raw = bytes(response)

            if raw_response:
                if not suppress_output:
                    logger.receive(f"Received bytes: {raw.hex()}")
                return raw

            for encoding in ("utf-8", "latin1"):
                try:
                    decoded = raw.decode(encoding).strip()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                decoded = raw.decode("utf-8", errors="replace").strip()

            if not suppress_output:
                logger.receive(f"Received response: {decoded}")
            return decoded
