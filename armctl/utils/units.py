"""
Minimal unit conversion utilities for robotics.
"""

from __future__ import annotations

import math

__all__ = [
    "deg2rad",
    "rad2deg",
    "mm2m",
    "m2mm",
    "joints2deg",
    "joints2rad",
    "pose2deg",
    "pose2rad",
]


def deg2rad(degrees: float) -> float:
    """Convert degrees to radians."""
    return math.radians(degrees)


def rad2deg(radians: float) -> float:
    """Convert radians to degrees."""
    return math.degrees(radians)


def mm2m(mm: float) -> float:
    """Convert millimeters to meters."""
    return mm * 1e-3


def m2mm(meters: float) -> float:
    """Convert meters to millimeters."""
    return meters * 1e3


def joints2deg(
    joint_positions: list[float] | list[tuple[float, float]],
) -> list[float] | list[tuple[float, float]]:
    """
    Convert joint positions from radians to degrees.
    Accepts either a list of floats or a list of (min, max) tuples.
    """
    if not joint_positions:
        return []

    if isinstance(joint_positions[0], (tuple, list)):
        return [
            (math.degrees(jmin), math.degrees(jmax))
            for jmin, jmax in joint_positions
        ]
    return [math.degrees(j) for j in joint_positions]


def joints2rad(
    joint_positions: list[float] | list[tuple[float, float]],
) -> list[float] | list[tuple[float, float]]:
    """
    Convert joint positions from degrees to radians.
    Accepts either a list of floats or a list of (min, max) tuples.
    """
    if not joint_positions:
        return []

    if isinstance(joint_positions[0], (tuple, list)):
        return [
            (math.radians(jmin), math.radians(jmax))
            for jmin, jmax in joint_positions
        ]
    return [math.radians(j) for j in joint_positions]


def pose2deg(pose: list[float]) -> list[float]:
    """Convert pose orientation (last 3 elements) from radians to degrees."""
    if len(pose) < 6:
        raise ValueError(
            "Pose must have at least 6 elements (x, y, z, rx, ry, rz)"
        )
    return pose[:3] + [math.degrees(a) for a in pose[3:]]


def pose2rad(pose: list[float]) -> list[float]:
    """Convert pose orientation (last 3 elements) from degrees to radians."""
    if len(pose) < 6:
        raise ValueError(
            "Pose must have at least 6 elements (x, y, z, rx, ry, rz)"
        )
    return pose[:3] + [math.radians(a) for a in pose[3:]]
