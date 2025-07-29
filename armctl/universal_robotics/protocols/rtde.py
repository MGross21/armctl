"""
Real-Time Data Exchange (RTDE) Protocol

This module provides utilities for parsing RTDE protocol messages from Universal Robots.
For more information, see:
https://www.universal-robots.com/developer/communication-protocol/rtde/
"""

import struct
from typing import Optional, Tuple


class RTDE:
    """RTDE protocol parser for Universal Robots."""

    # Message type constants
    JOINT_ANGLES_MSG = 1
    TCP_POSE_MSG = 4

    # Protocol constants
    NUM_JOINTS = 6
    POSE_DOF = 6
    DOUBLE_SIZE = 8  # bytes
    HEADER_SIZE = 4  # bytes for packet length
    MSG_HEADER_SIZE = 5  # bytes for message header

    @staticmethod
    def joint_angles(
        data: bytes,
    ) -> Tuple[float, float, float, float, float, float]:
        """
        Extract joint angles from the raw socket response data.

        Args:
            data: Raw response data from the socket.

        Returns:
            A tuple of 6 joint angles in radians.
            Returns zeros if parsing fails.

        Example:
            >>> angles = RTDE.joint_angles(data)
            >>> print(f"Joint 1: {angles[0]:.3f} rad")
        """
        return RTDE._parse_message(data, RTDE.JOINT_ANGLES_MSG, RTDE.NUM_JOINTS)

    @staticmethod
    def tcp_pose(
        data: bytes,
    ) -> Tuple[float, float, float, float, float, float]:
        """
        Extract TCP pose (X, Y, Z, RX, RY, RZ) from the raw socket response data.

        Args:
            data: Raw response data from the socket.

        Returns:
            A tuple of 6 floats representing pose:
            - X, Y, Z: Position in meters
            - RX, RY, RZ: Rotation vector in radians
            Returns zeros if parsing fails.

        Example:
            >>> pose = RTDE.tcp_pose(data)
            >>> x, y, z, rx, ry, rz = pose
            >>> print(f"Position: ({x:.3f}, {y:.3f}, {z:.3f})")
        """
        return RTDE._parse_message(data, RTDE.TCP_POSE_MSG, RTDE.POSE_DOF)

    @staticmethod
    def _parse_message(
        data: bytes, target_msg_type: int, count: int
    ) -> Tuple[float, ...]:
        """
        Generic parser for RTDE messages with improved error handling.

        Args:
            data: Raw response data from the socket.
            target_msg_type: Message type to extract.
            count: Number of doubles to extract.

        Returns:
            Parsed values as a tuple of floats.
            Returns zeros if parsing fails or data is corrupted.
        """
        # Input validation
        if not data or len(data) < RTDE.HEADER_SIZE:
            return tuple(0.0 for _ in range(count))

        try:
            # Parse packet length with proper format specifier
            packet_length = struct.unpack("!I", data[: RTDE.HEADER_SIZE])[0]

            # Validate packet length
            if packet_length > len(data) or packet_length < RTDE.HEADER_SIZE:
                return tuple(0.0 for _ in range(count))

            offset = RTDE.HEADER_SIZE
            expected_data_size = count * RTDE.DOUBLE_SIZE

            # Parse messages within packet
            while offset + RTDE.MSG_HEADER_SIZE <= packet_length:
                # Ensure we don't read beyond data bounds
                if offset + RTDE.MSG_HEADER_SIZE > len(data):
                    break

                # Parse message length and type
                msg_len = struct.unpack("!I", data[offset : offset + 4])[0]
                msg_type = struct.unpack("!B", data[offset + 4 : offset + 5])[0]

                # Validate message length
                if (
                    msg_len < RTDE.MSG_HEADER_SIZE
                    or offset + msg_len > packet_length
                ):
                    break

                # Check if this is the target message type
                if msg_type == target_msg_type:
                    data_start = offset + RTDE.MSG_HEADER_SIZE
                    data_end = data_start + expected_data_size

                    # Ensure we have enough data for the expected values
                    if data_end <= len(data) and data_end <= offset + msg_len:
                        values = struct.unpack(
                            f"!{count}d", data[data_start:data_end]
                        )
                        return values
                    else:
                        # Insufficient data for complete message
                        break

                # Move to next message
                offset += msg_len

        except (struct.error, IndexError, ValueError):
            # Handle any parsing errors gracefully
            pass

        # Return zeros if message not found or parsing failed
        return tuple(0.0 for _ in range(count))

    @staticmethod
    def is_valid_packet(data: bytes) -> bool:
        """
        Check if the data appears to be a valid RTDE packet.

        Args:
            data: Raw data to validate.

        Returns:
            True if data appears to be a valid RTDE packet, False otherwise.
        """
        if not data or len(data) < RTDE.HEADER_SIZE:
            return False

        try:
            packet_length = struct.unpack("!I", data[: RTDE.HEADER_SIZE])[0]
            return packet_length >= RTDE.HEADER_SIZE and packet_length <= len(
                data
            )
        except struct.error:
            return False

    @staticmethod
    def get_available_message_types(data: bytes) -> list[int]:
        """
        Get a list of available message types in the RTDE packet.

        Args:
            data: Raw RTDE data.

        Returns:
            List of message type integers found in the packet.
        """
        message_types = []

        if not RTDE.is_valid_packet(data):
            return message_types

        try:
            packet_length = struct.unpack("!I", data[: RTDE.HEADER_SIZE])[0]
            offset = RTDE.HEADER_SIZE

            while offset + RTDE.MSG_HEADER_SIZE <= packet_length:
                if offset + RTDE.MSG_HEADER_SIZE > len(data):
                    break

                msg_len = struct.unpack("!I", data[offset : offset + 4])[0]
                msg_type = struct.unpack("!B", data[offset + 4 : offset + 5])[0]

                if (
                    msg_len >= RTDE.MSG_HEADER_SIZE
                    and offset + msg_len <= packet_length
                ):
                    message_types.append(msg_type)
                    offset += msg_len
                else:
                    break

        except (struct.error, IndexError):
            pass

        return message_types

    @staticmethod
    def parse_all_available(
        data: bytes,
    ) -> dict[str, Optional[Tuple[float, ...]]]:
        """
        Parse all available known message types from RTDE data.

        Args:
            data: Raw RTDE data.

        Returns:
            Dictionary with keys 'joint_angles' and 'tcp_pose' containing
            the parsed data, or None if not available.
        """
        available_types = RTDE.get_available_message_types(data)
        result = {"joint_angles": None, "tcp_pose": None}

        if RTDE.JOINT_ANGLES_MSG in available_types:
            angles = RTDE.joint_angles(data)
            # Only include if we got actual data (not all zeros)
            if any(angle != 0.0 for angle in angles):
                result["joint_angles"] = angles

        if RTDE.TCP_POSE_MSG in available_types:
            pose = RTDE.tcp_pose(data)
            # Only include if we got actual data (not all zeros)
            if any(val != 0.0 for val in pose):
                result["tcp_pose"] = pose

        return result
