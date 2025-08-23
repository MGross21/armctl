"""
Unit conversion utilities with enum-based type safety.
"""

import math
from enum import Enum
from typing import List, Union


class Units:
    class Length(Enum):
        """Length units with conversion factors to meters."""
        MM = 1e-3
        CM = 1e-2
        M = 1.0
        KM = 1e3
        INCH = 0.0254
        FEET = 0.3048
        YARD = 0.9144

    class Angle(Enum):
        """Angle units with conversion factors to radians."""
        DEGREE = math.pi / 180
        RADIAN = 1.0
        REVOLUTION = 2 * math.pi


class UnitConverter:
    """Generic unit converter for any enum-based unit system."""
    
    @staticmethod
    def _resolve_unit(unit: Union[Enum, str], unit_enum: type) -> Enum:
        """Convert string to enum if needed."""
        return unit_enum[unit.upper()] if isinstance(unit, str) else unit
    
    @staticmethod
    def convert(value: float, from_unit: Union[Enum, str], to_unit: Union[Enum, str], unit_enum: type) -> float:
        """Convert between any two units of the same type."""
        from_unit = UnitConverter._resolve_unit(from_unit, unit_enum)
        to_unit = UnitConverter._resolve_unit(to_unit, unit_enum)
        return value * from_unit.value / to_unit.value
    
    @staticmethod
    def convert_list(values: List[float], from_unit: Union[Enum, str], to_unit: Union[Enum, str], unit_enum: type) -> List[float]:
        """Convert a list of values between units."""
        if (isinstance(from_unit, str) and isinstance(to_unit, str) and from_unit.upper() == to_unit.upper()) or from_unit == to_unit:
            return values.copy()
        return [UnitConverter.convert(v, from_unit, to_unit, unit_enum) for v in values]


class Length:
    """Length conversion utilities."""
    
    @staticmethod
    def to_meters(value: float, unit: Union[Units.Length, str]) -> float:
        """Convert to meters."""
        return UnitConverter.convert(value, unit, Units.Length.M, Units.Length)
    
    @staticmethod
    def from_meters(value: float, unit: Union[Units.Length, str]) -> float:
        """Convert from meters."""
        return UnitConverter.convert(value, Units.Length.M, unit, Units.Length)


class Angle:
    """Angle conversion utilities."""
    
    @staticmethod
    def to_radians(value: float, unit: Union[Units.Angle, str]) -> float:
        """Convert to radians."""
        return UnitConverter.convert(value, unit, Units.Angle.RADIAN, Units.Angle)
    
    @staticmethod
    def from_radians(value: float, unit: Union[Units.Angle, str]) -> float:
        """Convert from radians."""
        return UnitConverter.convert(value, Units.Angle.RADIAN, unit, Units.Angle)
    
    @staticmethod
    def convert_list(values: List[float], from_unit: Union[Units.Angle, str], to_unit: Union[Units.Angle, str]) -> List[float]:
        """Convert a list of angle values between units."""
        return UnitConverter.convert_list(values, from_unit, to_unit, Units.Angle)


class Pose:
    """Pose conversion utilities for joint positions and Cartesian poses."""
    
    @staticmethod
    def joints_to_degrees(joint_positions: List[float]) -> List[float]:
        """Convert joint positions from radians to degrees."""
        return [math.degrees(j) for j in joint_positions]
    
    @staticmethod
    def joints_to_radians(joint_positions: List[float]) -> List[float]:
        """Convert joint positions from degrees to radians."""
        return [math.radians(j) for j in joint_positions]
    
    @staticmethod
    def cartesian_to_degrees(pose: List[float]) -> List[float]:
        """Convert Cartesian pose orientation from radians to degrees."""
        if len(pose) < 6:
            raise ValueError("Cartesian pose must have at least 6 elements (x, y, z, rx, ry, rz)")
        return pose[:3] + [math.degrees(a) for a in pose[3:]]
    
    @staticmethod
    def cartesian_to_radians(pose: List[float]) -> List[float]:
        """Convert Cartesian pose orientation from degrees to radians."""
        if len(pose) < 6:
            raise ValueError("Cartesian pose must have at least 6 elements (x, y, z, rx, ry, rz)")
        return pose[:3] + [math.radians(a) for a in pose[3:]]