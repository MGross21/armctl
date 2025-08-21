"""
This module provides utility classes for unit conversions, ensuring that user input units remain constant while converting values internally.
This approach creates a consistent environment for handling length and angle measurements.
"""


import math

class Length:
    """Length conversion factors to meters."""
    MM = 1e-3
    CM = 1e-2
    M = 1.0
    KM = 1e3
    INCH = 0.0254
    FEET = 0.3048
    YARD = 0.9144

    @staticmethod
    def to_meters(value: float, unit: "Length") -> float:
        """Convert a length value to meters."""
        return value * getattr(Length, unit.upper(), 1.0)

    @staticmethod
    def from_meters(value: float, unit: "Length") -> float:
        """Convert a length value from meters to the specified unit."""
        return value / getattr(Length, unit.upper(), 1.0)
    

class Angle:
    """Angle conversion factors to radians."""
    DEGREE = math.pi / 180
    RADIAN = 1.0
    REVOLUTION = 2 * math.pi

    @staticmethod
    def to_radians(value: float, unit: "Angle") -> float:
        """Convert an angle value to radians."""
        return value * getattr(Angle, unit.upper(), 1.0)

    @staticmethod
    def from_radians(value: float, unit: "Angle") -> float:
        """Convert an angle value from radians to the specified unit."""
        return value / getattr(Angle, unit.upper(), 1.0)
    

class Joints:
    @staticmethod
    def to_degrees(joint_positions):
        """Convert a list of joint positions from radians to degrees."""
        return [math.degrees(j) for j in joint_positions]

    @staticmethod
    def to_radians(joint_positions):
        """Convert a list of joint positions from degrees to radians."""
        return [math.radians(j) for j in joint_positions]

class Cartesian:
    @staticmethod
    def to_degrees(pose):
        """Convert a Cartesian pose from radians to degrees."""
        return pose[:3] + [math.degrees(a) for a in pose[3:]]

    @staticmethod
    def to_radians(pose):
        """Convert a Cartesian pose from degrees to radians."""
        return pose[:3] + [math.radians(a) for a in pose[3:]]