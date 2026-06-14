from __future__ import annotations

import socket
import struct
from enum import IntEnum

from . import config as rtde_config


class Command(IntEnum):
    REQUEST_PROTOCOL_VERSION = ord("V")
    GET_URCONTROL_VERSION = ord("v")
    TEXT_MESSAGE = ord("M")
    DATA_PACKAGE = ord("U")
    SETUP_OUTPUTS = ord("O")
    SETUP_INPUTS = ord("I")
    START = ord("S")


class RTDE:
    def __init__(self, hostname: str, port: int = 30004, timeout: float = 1.0):
        self.hostname = hostname
        self.port = port
        self.timeout = timeout
        self._sock = None
        self._buffer = bytearray()
        self._output_recipe_id: int | None = None
        self._input_recipe_id: int | None = None

    def connect(self) -> None:
        if self._sock is not None:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.connect((self.hostname, self.port))
        self._sock = sock
        if not self.negotiate_protocol_version():
            raise RuntimeError("Unable to negotiate RTDE protocol version")

    def disconnect(self) -> None:
        if self._sock is not None:
            self._sock.close()
            self._sock = None
        self._buffer.clear()

    def is_connected(self) -> bool:
        return self._sock is not None

    def negotiate_protocol_version(self) -> bool:
        payload = struct.pack(">H", 2)
        result = self._send_and_receive(
            Command.REQUEST_PROTOCOL_VERSION,
            payload,
            Command.REQUEST_PROTOCOL_VERSION,
        )
        return bool(result and result[0] == 1)

    def get_controller_version(self) -> tuple[int, int, int, int]:
        payload = self._send_and_receive(
            Command.GET_URCONTROL_VERSION, b"", Command.GET_URCONTROL_VERSION
        )
        if len(payload) != 16:
            raise RuntimeError("Unexpected UR control version payload size")
        return struct.unpack(">IIII", payload)

    def send_output_setup(self, frequency: float = 125) -> bool:
        request = (
            struct.pack(">d", float(frequency))
            + ",".join(rtde_config.OUTPUT_NAMES).encode()
        )
        payload = self._send_and_receive(
            Command.SETUP_OUTPUTS, request, Command.SETUP_OUTPUTS
        )
        if not payload:
            return False
        self._check_recipe_types(payload, rtde_config.OUTPUT_NAMES)
        self._output_recipe_id = payload[0]
        return True

    def send_input_setup(self) -> rtde_config.InputData:
        payload = self._send_and_receive(
            Command.SETUP_INPUTS,
            ",".join(rtde_config.INPUT_NAMES).encode(),
            Command.SETUP_INPUTS,
        )
        if not payload:
            raise RuntimeError("RTDE input setup failed: empty response")
        self._check_recipe_types(payload, rtde_config.INPUT_NAMES)
        inp = rtde_config.InputData()
        inp.recipe_id = payload[0]
        self._input_recipe_id = payload[0]
        return inp

    @staticmethod
    def _check_recipe_types(payload: bytes, names: list[str]) -> None:
        types = payload[1:].decode().split(",") if len(payload) > 1 else []
        bad = [
            name
            for name, t in zip(names, types)
            if t in ("NOT_FOUND", "IN_USE")
        ]
        if bad:
            raise RuntimeError(f"RTDE recipe rejected variables: {bad}")

    def send_start(self) -> bool:
        payload = self._send_and_receive(Command.START, b"", Command.START)
        return bool(payload and payload[0] == 1)

    def send(self, input_data: rtde_config.InputData) -> None:
        self._send_packet(Command.DATA_PACKAGE, bytes(input_data))

    def receive(self) -> rtde_config.OutputData:
        if self._output_recipe_id is None:
            raise RuntimeError("Output recipe not configured")
        _, payload = self._receive_packet(expected=Command.DATA_PACKAGE)
        return rtde_config.OutputData.from_buffer_copy(payload)

    def _send_and_receive(self, command: int, payload: bytes, expected: int) -> bytes:
        self._send_packet(command, payload)
        received_command, received_payload = self._receive_packet(expected)
        if received_command != expected:
            raise RuntimeError(
                f"Unexpected RTDE command: {received_command} != {expected}"
            )
        return received_payload

    def _send_packet(self, command: int, payload: bytes) -> None:
        if self._sock is None:
            raise ConnectionError("RTDE socket not connected")
        packet = struct.pack(">HB", len(payload) + 3, int(command)) + payload
        self._sock.sendall(packet)

    def _receive_packet(self, expected=None):
        if self._sock is None:
            raise ConnectionError("RTDE socket not connected")
        while True:
            while len(self._buffer) < 3:
                self._recv_into_buffer()
            size, command = struct.unpack_from(">HB", self._buffer, 0)
            while len(self._buffer) < size:
                self._recv_into_buffer()
            payload = bytes(self._buffer[3:size])
            del self._buffer[:size]
            if expected is not None and command != int(expected):
                if command == int(Command.TEXT_MESSAGE):
                    continue
            return command, payload

    def _recv_into_buffer(self) -> None:
        if self._sock is None:
            raise ConnectionError("RTDE socket not connected")
        try:
            chunk = self._sock.recv(4096)
        except socket.timeout as exc:
            raise TimeoutError("Timed out waiting for RTDE data") from exc
        if not chunk:
            self.disconnect()
            raise ConnectionError("RTDE socket disconnected")
        self._buffer.extend(chunk)
