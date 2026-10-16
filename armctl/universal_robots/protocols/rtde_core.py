from __future__ import annotations

import select
import socket
import struct
from enum import IntEnum

from .config import InputData, OutputData, Recipe


class Command(IntEnum):
    REQUEST_PROTOCOL_VERSION = ord("V")
    GET_URCONTROL_VERSION = ord("v")
    TEXT_MESSAGE = ord("M")
    DATA_PACKAGE = ord("U")
    SETUP_OUTPUTS = ord("O")
    SETUP_INPUTS = ord("I")
    START = ord("S")


class RTDEClient:
    _HEADER = struct.Struct(">HB")  # packet size incl. header, command

    def __init__(self, hostname: str, port: int = 30004, timeout: float = 1.0):
        self.address = (hostname, port)
        self.timeout = timeout
        self._sock: socket.socket | None = None
        self._buffer = bytearray()

    def connect(self) -> None:
        if self._sock is not None:
            return
        self._sock = socket.create_connection(self.address, self.timeout)
        self._sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        if self._request(Command.REQUEST_PROTOCOL_VERSION, struct.pack(">H", 2)) != b"\x01":
            raise RuntimeError("Unable to negotiate RTDE protocol version")

    def disconnect(self) -> None:
        if self._sock is not None:
            self._sock.close()
            self._sock = None
        self._buffer.clear()

    def get_controller_version(self) -> tuple[int, int, int, int]:
        return struct.unpack(">IIII", self._request(Command.GET_URCONTROL_VERSION))

    def send_output_setup(self, frequency: float = 125) -> None:
        request = struct.pack(">d", frequency) + ",".join(OutputData.names()).encode()
        self._check_recipe_types(self._request(Command.SETUP_OUTPUTS, request), OutputData)

    def send_input_setup(self) -> InputData:
        payload = self._request(Command.SETUP_INPUTS, ",".join(InputData.names()).encode())
        self._check_recipe_types(payload, InputData)
        return InputData(recipe_id=payload[0])

    def send_start(self) -> None:
        if self._request(Command.START) != b"\x01":
            raise RuntimeError("RTDE controller refused to start synchronization")

    def send(self, data: InputData) -> None:
        self._send(Command.DATA_PACKAGE, bytes(data))

    def receive(self) -> OutputData:
        """Return the newest buffered data package, blocking until one arrives."""
        while select.select([self._socket], [], [], 0)[0]:
            self._recv()
        payload = self._read_packet(Command.DATA_PACKAGE)
        while self._packet_ready():
            payload = self._read_packet(Command.DATA_PACKAGE)
        return OutputData.from_buffer_copy(payload)

    @staticmethod
    def _check_recipe_types(payload: bytes, recipe: type[Recipe]) -> None:
        actual = payload[1:].decode().split(",")
        expected = recipe.rtde_types()
        if actual != expected:
            bad = [f"{n}: {a}" for n, e, a in zip(recipe.names(), expected, actual) if a != e]
            raise RuntimeError(f"RTDE {recipe.__name__} mismatch (name: controller type): {bad}")

    @property
    def _socket(self) -> socket.socket:
        if self._sock is None:
            raise ConnectionError("RTDE socket not connected")
        return self._sock

    def _request(self, command: Command, payload: bytes = b"") -> bytes:
        self._send(command, payload)
        return self._read_packet(command)

    def _send(self, command: Command, payload: bytes) -> None:
        self._socket.sendall(self._HEADER.pack(self._HEADER.size + len(payload), command) + payload)

    def _packet_ready(self) -> bool:
        return (
            len(self._buffer) >= self._HEADER.size
            and len(self._buffer) >= self._HEADER.unpack_from(self._buffer)[0]
        )

    def _read_packet(self, expected: Command) -> bytes:
        """Pop the next packet's payload, skipping text messages."""
        while True:
            while not self._packet_ready():
                self._recv()
            size, command = self._HEADER.unpack_from(self._buffer)
            payload = bytes(self._buffer[self._HEADER.size : size])
            del self._buffer[:size]
            if command == expected:
                return payload
            if command != Command.TEXT_MESSAGE:
                raise RuntimeError(f"Unexpected RTDE command {command}, expected {expected!r}")

    def _recv(self) -> None:
        try:
            chunk = self._socket.recv(65536)
        except socket.timeout as exc:
            raise TimeoutError("Timed out waiting for RTDE data") from exc
        if not chunk:
            self.disconnect()
            raise ConnectionError("RTDE socket disconnected")
        self._buffer.extend(chunk)
