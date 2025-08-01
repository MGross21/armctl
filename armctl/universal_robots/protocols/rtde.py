"""
RTDE Protocol Parser for Universal Robots

This module provides utilities to parse RTDE protocol messages received from a Universal Robots controller.
For detailed information, see:
https://www.universal-robots.com/developer/communication-protocol/rtde/
"""

import struct
from typing import Tuple, Optional, List, Dict
from pathlib import Path


class RTDE:
    """Parser for RTDE protocol messages from Universal Robots."""

    # Message type identifiers
    JOINT_ANGLES_MSG = 1
    TCP_POSE_MSG = 4

    # Constants for message sizes and data layout
    NUM_JOINTS = 6
    POSE_DOF = 6
    DOUBLE_SIZE = 8           # bytes in a double precision float
    PACKET_HEADER_SIZE = 4    # bytes for RTDE packet length header
    MSG_HEADER_SIZE = 5       # bytes for each message’s header (4 bytes length + 1 byte type)

    # Static XML recipe defining the output fields requested from the robot
    OUTPUT_RECIPE_XML = (Path(__file__).parent / 'config.xml').read_text()

    @staticmethod
    def joint_angles(data: bytes) -> Optional[Tuple[float, float, float, float, float, float]]:
        """
        Extract joint angles (radians) from raw RTDE binary data.

        Returns a tuple of 6 floats representing joint angles in radians,
        or None if parsing fails or data is invalid.
        """
        return RTDE._parse_message(data, RTDE.JOINT_ANGLES_MSG, RTDE.NUM_JOINTS)

    @staticmethod
    def tcp_pose(data: bytes) -> Optional[Tuple[float, float, float, float, float, float]]:
        """
        Extract TCP pose from raw RTDE binary data.

        Returns a tuple of 6 floats representing:
          X, Y, Z (meters) and RX, RY, RZ (rotation vector in radians),
        or None if parsing fails or data is invalid.
        """
        return RTDE._parse_message(data, RTDE.TCP_POSE_MSG, RTDE.POSE_DOF)

    @staticmethod
    def _parse_message(
        data: bytes,
        target_msg_type: int,
        count: int
    ) -> Optional[Tuple[float, ...]]:
        """
        Generic parser for RTDE data messages.

        Parses the packet, finds the target message type, and extracts 'count' doubles.

        Returns a tuple of floats if found, otherwise None.
        """
        if not data or len(data) < RTDE.PACKET_HEADER_SIZE:
            return None

        try:
            # Packet length: 4-byte unsigned int (big-endian)
            packet_length = struct.unpack('!I', data[:RTDE.PACKET_HEADER_SIZE])[0]
            if packet_length > len(data) or packet_length < RTDE.PACKET_HEADER_SIZE:
                return None

            offset = RTDE.PACKET_HEADER_SIZE
            expected_payload_size = count * RTDE.DOUBLE_SIZE

            # Iterate through messages inside the packet
            while offset + RTDE.MSG_HEADER_SIZE <= packet_length:
                # Prevent reading beyond actual data length
                if offset + RTDE.MSG_HEADER_SIZE > len(data):
                    break

                msg_len = struct.unpack('!I', data[offset:offset + 4])[0]
                msg_type = struct.unpack('!B', data[offset + 4:offset + 5])[0]

                # Validate message length
                if msg_len < RTDE.MSG_HEADER_SIZE or offset + msg_len > packet_length:
                    break

                if msg_type == target_msg_type:
                    start = offset + RTDE.MSG_HEADER_SIZE
                    end = start + expected_payload_size

                    if end <= len(data) and end <= offset + msg_len:
                        values = struct.unpack(f'!{count}d', data[start:end])
                        return values
                    else:
                        break  # Insufficient data

                offset += msg_len

        except (struct.error, IndexError, ValueError):
            pass

        # Return None if parsing fails or message not found
        return None

    @staticmethod
    def is_valid_packet(data: bytes) -> bool:
        """
        Validates if the data appears to be a valid RTDE packet.

        Returns True if the length header is consistent with data length.
        """
        if not data or len(data) < RTDE.PACKET_HEADER_SIZE:
            return False

        try:
            packet_length = struct.unpack('!I', data[:RTDE.PACKET_HEADER_SIZE])[0]
            return RTDE.PACKET_HEADER_SIZE <= packet_length <= len(data)
        except struct.error:
            return False

    @staticmethod
    def get_available_message_types(data: bytes) -> List[int]:
        """
        Returns a list of message types found in an RTDE packet.

        Useful for inspecting which data messages are present.
        """
        message_types: List[int] = []

        if not RTDE.is_valid_packet(data):
            return message_types

        try:
            packet_length = struct.unpack('!I', data[:RTDE.PACKET_HEADER_SIZE])[0]
            offset = RTDE.PACKET_HEADER_SIZE

            while offset + RTDE.MSG_HEADER_SIZE <= packet_length:
                if offset + RTDE.MSG_HEADER_SIZE > len(data):
                    break

                msg_len = struct.unpack('!I', data[offset:offset + 4])[0]
                msg_type = struct.unpack('!B', data[offset + 4:offset + 5])[0]

                if msg_len >= RTDE.MSG_HEADER_SIZE and offset + msg_len <= packet_length:
                    message_types.append(msg_type)
                    offset += msg_len
                else:
                    break

        except (struct.error, IndexError):
            pass

        return message_types

    @staticmethod
    def parse_all_available(data: bytes) -> Dict[str, Optional[Tuple[float, ...]]]:
        """
        Parses all recognized message types (joint angles and TCP pose) from RTDE data.

        Returns a dictionary with keys:
          'joint_angles' and 'tcp_pose', each containing a tuple of floats or None.
        """
        result = {'joint_angles': None, 'tcp_pose': None}

        types = RTDE.get_available_message_types(data)

        if RTDE.JOINT_ANGLES_MSG in types:
            angles = RTDE.joint_angles(data)
            if angles is not None:
                # Accept angles even if they include zeros (zeros might be valid)
                result['joint_angles'] = angles

        if RTDE.TCP_POSE_MSG in types:
            pose = RTDE.tcp_pose(data)
            if pose is not None:
                result['tcp_pose'] = pose

        return result