"""
Dobot Magician controller — serial binary protocol (115200 baud).

Packet layout: [0xAA][0xAA][Length][ID][Ctrl][Params...][Checksum]

- Length   = 2 + len(Params), excludes checksum byte
- Checksum = (-sum(Length, ID, Ctrl, *Params)) & 0xFF
- Byte order: little-endian

Ctrl byte — bit 0: RW (0=read, 1=write), bit 1: Queue (0=immediate, 1=queued).

Sources
-------
https://www.littlechip.co.nz/blog/communicating-with-the-dobot-magician-using-raw-protocol
https://download.dobot.cc/development-protocol/dobot-magician/pdf/en/Dobot-Magician-API-Description-V1.2.2.pdf
"""

from __future__ import annotations

import math
import struct
import time

from armctl.templates import SerialController as SCT
from armctl.utils import CommandCheck as cc
from armctl.utils import units as uu

from .dobot import Dobot


class DobotMagician(SCT, Dobot):
    """Dobot Magician 4-DOF desktop arm."""

    JOINT_RANGES = uu.joints2rad(
        [
            (-135.0, 135.0),  # J1: base
            (-5.0, 80.0),  # J2: rear arm
            (-10.0, 85.0),  # J3: forearm
            (-145.0, 145.0),  # J4: end-effector
        ]
    )
    MAX_JOINT_VELOCITY: float = uu.deg2rad(200.0)
    MAX_JOINT_ACCELERATION: float = uu.deg2rad(400.0)

    _CTRL_R = 0x00  # read, immediate
    _CTRL_W = 0x01  # write, immediate
    _CTRL_WQ = 0x03  # write, queued

    _CMD_GET_POSE = 10
    _CMD_SET_PTP = 84
    _CMD_QUEUED_START = 240
    _CMD_QUEUED_STOP = 241
    _CMD_QUEUED_FORCE_STOP = 242
    _CMD_QUEUED_CLEAR = 245
    _CMD_GET_QUEUE_INDEX = 246
    _CMD_GET_QUEUE_STATUS = 247

    _PTP_MOVJ_XYZ = 1  # joint-interpolated to Cartesian target
    _PTP_MOVL_XYZ = 2  # linear to Cartesian target
    _PTP_MOVJ_ANGLE = 4  # joint-interpolated to joint-angle target

    def __init__(self, port: str, baudrate: int = 115200):
        super().__init__(port, baudrate)
        self._last_queue_idx: int = 0

    def connect(self) -> None:
        """Open port and reset the command queue."""
        super().connect()
        self._send_packet(self._CMD_QUEUED_FORCE_STOP, self._CTRL_W)
        self._send_packet(self._CMD_QUEUED_CLEAR, self._CTRL_W)
        self._send_packet(self._CMD_QUEUED_START, self._CTRL_W)

    def disconnect(self) -> None:
        """Force-stop motion and close port."""
        try:
            self._send_packet(self._CMD_QUEUED_FORCE_STOP, self._CTRL_W)
        except Exception:
            pass
        super().disconnect()

    @staticmethod
    def _checksum(data: bytes | bytearray) -> int:
        return (-sum(data)) & 0xFF

    def _build_packet(
        self, cmd_id: int, ctrl: int, params: bytes = b""
    ) -> bytes:
        length = 2 + len(params)
        body = bytes([length, cmd_id, ctrl]) + params
        return b"\xaa\xaa" + body + bytes([self._checksum(body)])

    def _send_packet(
        self,
        cmd_id: int,
        ctrl: int = _CTRL_W,
        params: bytes = b"",
        timeout: float = 5.0,
    ) -> bytes:
        """Send binary packet; return response params bytes."""
        if not self._serial or not self._serial.is_open:
            raise ConnectionError("Not connected.")
        packet = self._build_packet(cmd_id, ctrl, params)
        with self._lock:
            self._serial.reset_input_buffer()
            self._serial.write(packet)
            self._serial.flush()
            return self._recv_packet(timeout)

    def _recv_packet(self, timeout: float = 5.0) -> bytes:
        """Read and validate one response packet; return params bytes."""
        deadline = time.monotonic() + timeout
        buf = bytearray()

        while time.monotonic() < deadline:
            if self._serial.in_waiting:
                buf.extend(self._serial.read(self._serial.in_waiting))

            start = -1
            for i in range(len(buf) - 1):
                if buf[i] == 0xAA and buf[i + 1] == 0xAA:
                    start = i
                    break
            if start < 0:
                time.sleep(0.005)
                continue
            buf = buf[start:]

            if len(buf) < 3:
                time.sleep(0.005)
                continue

            length = buf[2]
            total = (
                4 + length
            )  # header(2) + length(1) + payload(length) + checksum(1)

            if len(buf) < total:
                time.sleep(0.005)
                continue

            packet = bytes(buf[:total])
            expected = self._checksum(packet[2:-1])
            if packet[-1] != expected:
                raise ValueError(
                    f"Checksum mismatch: got {packet[-1]:#04x}, "
                    f"expected {expected:#04x}"
                )
            return packet[5:-1]

        raise TimeoutError(f"No packet received within {timeout}s")

    def _wait_for_motion(self, target_idx: int, timeout: float = 60.0) -> None:
        """Block until queue index reaches target_idx."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            resp = self._send_packet(self._CMD_GET_QUEUE_INDEX, self._CTRL_R)
            if (
                len(resp) >= 8
                and struct.unpack_from("<Q", resp)[0] >= target_idx
            ):
                return
            time.sleep(0.1)
        raise TimeoutError(f"Motion did not complete within {timeout}s")

    def sleep(self, seconds: float) -> None:
        """Host-side sleep; no robot command issued."""
        cc.sleep(seconds)
        time.sleep(seconds)

    def move_joints(
        self,
        pos: list[float],
        speed: float = uu.deg2rad(100.0),
        acceleration: float = uu.deg2rad(80.0),
    ) -> None:
        """
        Joint-interpolated move to joint positions.

        Parameters
        ----------
        pos : list of float
            [J1, J2, J3, J4] in radians.
        speed : float
            Joint speed in rad/s.
        acceleration : float
            Joint acceleration in rad/s².
        """
        cc.move_joints(self, pos, speed, acceleration)
        j1, j2, j3, j4 = uu.joints2deg(pos)
        params = struct.pack("<Bffff", self._PTP_MOVJ_ANGLE, j1, j2, j3, j4)
        resp = self._send_packet(self._CMD_SET_PTP, self._CTRL_WQ, params)
        if len(resp) >= 8:
            self._last_queue_idx = struct.unpack_from("<Q", resp)[0]
        self._wait_for_motion(self._last_queue_idx)

    def move_cartesian(self, pose: list[float]) -> None:
        """
        Linear move to Cartesian pose.

        Parameters
        ----------
        pose : list of float
            [x, y, z, r] — x/y/z in meters, r in radians.
        """
        cc.move_cartesian(self, pose)
        x_mm = pose[0] * 1000.0
        y_mm = pose[1] * 1000.0
        z_mm = pose[2] * 1000.0
        r_deg = math.degrees(pose[3])
        params = struct.pack(
            "<Bffff", self._PTP_MOVL_XYZ, x_mm, y_mm, z_mm, r_deg
        )
        resp = self._send_packet(self._CMD_SET_PTP, self._CTRL_WQ, params)
        if len(resp) >= 8:
            self._last_queue_idx = struct.unpack_from("<Q", resp)[0]
        self._wait_for_motion(self._last_queue_idx)

    def get_joint_positions(self) -> list[float]:
        """
        Current joint angles.

        Returns
        -------
        list of float
            [J1, J2, J3, J4] in radians.
        """
        cc.get_joint_positions()
        resp = self._send_packet(self._CMD_GET_POSE, self._CTRL_R)
        if len(resp) < 32:
            raise RuntimeError(f"GetPose response too short: {len(resp)} bytes")
        return [math.radians(j) for j in struct.unpack_from("<8f", resp)[4:8]]

    def get_cartesian_position(self) -> list[float]:
        """
        Current Cartesian pose.

        Returns
        -------
        list of float
            [x, y, z, r] — x/y/z in meters, r in radians.
        """
        cc.get_cartesian_position()
        resp = self._send_packet(self._CMD_GET_POSE, self._CTRL_R)
        if len(resp) < 32:
            raise RuntimeError(f"GetPose response too short: {len(resp)} bytes")
        x, y, z, r = struct.unpack_from("<4f", resp)
        return [x / 1000.0, y / 1000.0, z / 1000.0, math.radians(r)]

    def stop_motion(self) -> None:
        """Force-stop motion and clear the command queue."""
        cc.stop_motion()
        self._send_packet(self._CMD_QUEUED_FORCE_STOP, self._CTRL_W)
        self._send_packet(self._CMD_QUEUED_CLEAR, self._CTRL_W)
        self._send_packet(self._CMD_QUEUED_START, self._CTRL_W)

    def get_robot_state(self) -> dict:
        """
        Queue running status.

        Returns
        -------
        dict
            {"is_running": bool, "queue_index": int}
        """
        cc.get_robot_state()
        resp = self._send_packet(self._CMD_GET_QUEUE_STATUS, self._CTRL_R)
        is_running = bool(struct.unpack_from("<B", resp)[0]) if resp else False
        return {"is_running": is_running, "queue_index": self._last_queue_idx}
