from __future__ import annotations

import time
from zaber_motion import ascii

from armctl.templates import Commands, Properties
from armctl.utils import CommandCheck as cc
from armctl.templates.logger import logger


class Zaber(Commands, Properties):
    """
    Zaber motion controller for linear actuators.
    
    Uses the official zaber-motion library for ASCII protocol communication.
    Supports multi-axis linear motion systems via TCP connection.
    
    Reference:
    - ASCII Protocol: https://www.zaber.com/protocol-manual
    - Python API: https://software.zaber.com/motion-library/api/py
    - Examples: https://github.com/zabertech/zaber-examples
    """

    def __init__(
        self,
        ip: str,
        port: int = 55550,
        device_address: int = 1,
        num_axes: int = 1,
    ):
        """
        Initialize Zaber device connection parameters.
        
        Args:
            ip: IP address of Zaber device or network interface
            port: TCP port (default: 55550)
            device_address: Device address on the bus (default: 1)
            num_axes: Number of axes on this device (auto-detected if not set)
        """
        self.ip = ip
        self.port = port
        self.device_address = device_address
        self.num_axes = num_axes
        
        self.connection = None
        self.device = None
        self.axes = []
        
        # Define Properties - for linear systems, ranges are in meters
        # Default: single axis with typical range
        self.JOINT_RANGES: list[tuple[float, float]] = [
            (0.0, 0.3) for _ in range(num_axes)  # 0-300mm typical range
        ]
        self.MAX_JOINT_VELOCITY: float | None = 10.0  # m/s
        self.MAX_JOINT_ACCELERATION: float | None = None

    def connect(self) -> None:
        """Establish connection to Zaber device via TCP."""
        try:
            logger.info(f"Connecting to Zaber at {self.ip}:{self.port}")
            # Open TCP connection using first-party zaber-motion library
            self.connection = ascii.Connection.open_tcp(self.ip, self.port)
            
            # Get the device
            self.device = self.connection.get_device(self.device_address)
            logger.info(f"Connected to device at address {self.device_address}")
            
            # Identify and cache available axes
            identity = self.device.identify()
            self.num_axes = identity.axis_count
            logger.info(f"Device has {self.num_axes} axes")
            
            # Get axis objects for later use
            self.axes = [self.device.get_axis(i + 1) for i in range(self.num_axes)]
            
        except Exception as e:
            logger.error(f"Failed to connect to Zaber: {e}")
            raise

    def disconnect(self) -> None:
        """Close connection to Zaber device."""
        try:
            if self.connection:
                self.connection.close()
                logger.info("Disconnected from Zaber device")
        except Exception as e:
            logger.warning(f"Error during disconnect: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False

    def sleep(self, seconds: float) -> None:
        """Sleep for the specified number of seconds."""
        cc.sleep(seconds)
        time.sleep(seconds)

    def move_joints(self, pos: list[float]) -> None:
        """
        Move axes to specified positions in meters.
        
        Args:
            pos: List of positions in meters (one per axis)
        """
        cc.move_joints(pos)
        
        try:
            if len(pos) != len(self.axes):
                raise ValueError(
                    f"Expected {len(self.axes)} positions, got {len(pos)}"
                )
            
            # Move each axis to target position
            for i, axis in enumerate(self.axes):
                target = pos[i]
                logger.debug(f"Moving axis {i + 1} to {target} m")
                axis.move_absolute(target, unit="m")
            
            # Wait for all axes to complete movement
            for axis in self.axes:
                axis.wait_until_idle()
                
        except Exception as e:
            logger.error(f"Failed to move joints: {e}")
            raise

    def get_joint_positions(self) -> list[float]:
        """Get current position of all axes in meters."""
        cc.get_joint_positions()
        
        try:
            positions = []
            for i, axis in enumerate(self.axes):
                pos = axis.get_position(unit="m")
                positions.append(pos)
                logger.debug(f"Axis {i + 1} position: {pos} m")
            return positions
            
        except Exception as e:
            logger.error(f"Failed to get joint positions: {e}")
            raise

    def move_cartesian(self, pose: list[float]) -> None:
        """
        Move to cartesian position.
        
        For linear systems, this is equivalent to move_joints.
        
        Args:
            pose: List of positions in meters [x, y, z, ...] or applicable axes
        """
        cc.move_cartesian(pose)
        # For linear systems, cartesian movement is same as joint movement
        self.move_joints(pose[: len(self.axes)])

    def get_cartesian_position(self) -> list[float]:
        """
        Get current cartesian position.
        
        For linear systems, this is equivalent to get_joint_positions.
        """
        cc.get_cartesian_position()
        return self.get_joint_positions()

    def stop_motion(self) -> None:
        """Stop all axes immediately."""
        cc.stop_motion()
        
        try:
            logger.info("Stopping all axes")
            for i, axis in enumerate(self.axes):
                axis.stop()
                
        except Exception as e:
            logger.error(f"Failed to stop motion: {e}")
            raise

    def get_robot_state(self) -> dict:
        """Get current device and axis states."""
        cc.get_robot_state()
        
        try:
            state = {
                "device_address": self.device_address,
                "num_axes": self.num_axes,
                "axes": [],
            }
            
            for i, axis in enumerate(self.axes):
                axis_state = axis.get_state()
                state["axes"].append({
                    "axis": i + 1,
                    "is_moving": axis.is_busy(),
                    "is_homed": axis.is_homed(),
                    "state": str(axis_state),
                })
            
            return state
            
        except Exception as e:
            logger.error(f"Failed to get robot state: {e}")
            raise

    def home(self) -> None:
        """Home all axes to their home position."""
        try:
            logger.info("Homing all axes")
            for i, axis in enumerate(self.axes):
                axis.home()
                logger.debug(f"Homing axis {i + 1}")
            
            # Wait for all axes to complete homing
            for axis in self.axes:
                axis.wait_until_idle()
                
        except Exception as e:
            logger.error(f"Failed to home axes: {e}")
            raise
