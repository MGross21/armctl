"""
Real-Time Data Exchange (RTDE) Protocol

This module provides utilities for parsing RTDE protocol messages from Universal Robots.
For more information, see:
https://www.universal-robots.com/developer/communication-protocol/rtde/
"""

import struct

class RTDE:
    @staticmethod
    def joint_angles(data) -> tuple[float, float, float, float, float, float]:
        """
        Extract joint angles from the raw socket response data.
        
        Args:
        - data (bytes): Raw response data from the socket.
        
        Returns:
        - list: A list of 6 joint angles.
        """
        angles = [0] * 6
        i = 0
        # Process the packet length and message
        packet_length = struct.unpack('!i', data[0:4])[0]
        while i + 5 < packet_length:
            msg_len = struct.unpack('!i', data[5 + i:9 + i])[0]
            msg_type = struct.unpack('!b', data[9 + i:10 + i])[0]
            
            if msg_type == 1:  # Joint data message type
                for j in range(6):
                    angles[j] = struct.unpack('!d', data[10 + i + (j * 41):18 + i + (j * 41)])[0]
                break
            i += msg_len
        return angles

    @staticmethod
    def tcp_pose(data) -> tuple[float, float, float, float, float, float]:
        """
        Extract TCP pose (X, Y, Z, RX, RY, RZ) from the raw socket response data.
        
        Args:
        - data (bytes): Raw response data from the socket.
        
        Returns:
        - tuple: A tuple containing X, Y, Z, RX, RY, RZ.
        """
        tcp_pose = (0, 0, 0, 0, 0, 0)  # Default zero values
        i = 0
        # Process the packet length and message
        packet_length = struct.unpack('!i', data[0:4])[0]
        while i + 5 < packet_length:
            msg_len = struct.unpack('!i', data[5 + i:9 + i])[0]
            msg_type = struct.unpack('!b', data[9 + i:10 + i])[0]
            
            if msg_type == 4:  # Cartesian data message type (TCP Pose)
                x = struct.unpack('!d', data[10 + i:18 + i])[0]
                y = struct.unpack('!d', data[18 + i:26 + i])[0]
                z = struct.unpack('!d', data[26 + i:34 + i])[0]
                rx = struct.unpack('!d', data[34 + i:42 + i])[0]
                ry = struct.unpack('!d', data[42 + i:50 + i])[0]
                rz = struct.unpack('!d', data[50 + i:58 + i])[0]
                
                tcp_pose = (x, y, z, rx, ry, rz)
                break
            i += msg_len
        return tcp_pose