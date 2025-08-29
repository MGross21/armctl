from __future__ import annotations

from armctl.templates import Commands, Properties


class CommandCheck(Commands):
    """Validates command parameters for robot operations."""

    @staticmethod
    def sleep(seconds: int | float) -> None:
        """Validate sleep duration parameter."""
        if not isinstance(seconds, (int, float)):
            raise TypeError(
                f"Sleep duration must be a number, got {type(seconds).__name__}"
            )
        if seconds < 0:
            raise ValueError(
                f"Sleep duration must be non-negative, got {seconds}"
            )

    @staticmethod
    def move_joints(
        robot_instance: Properties,
        positions: list[float],
        velocity: float = None,
        acceleration: float = None,
    ) -> None:
        """Validate joint positions against robot ranges."""
        # Basic type validation
        if not isinstance(positions, list):
            raise TypeError(
                f"Joint positions must be a list, got {type(positions).__name__}"
            )

        if any(isinstance(x, list) for x in positions):
            raise TypeError("Joint positions must not contain nested lists")

        if not all(isinstance(p, (int, float)) for p in positions):
            invalid_types = [
                type(p).__name__
                for p in positions
                if not isinstance(p, (int, float))
            ]
            raise TypeError(
                f"All joint positions must be numbers, found: {set(invalid_types)}"
            )

        # Robot-specific validation using guaranteed Properties interface
        joint_ranges = robot_instance.JOINT_RANGES
        dof = robot_instance.DOF
        v = robot_instance.MAX_JOINT_VELOCITY
        a = robot_instance.MAX_JOINT_ACCELERATION

        if len(positions) != dof:
            raise ValueError(
                f"Expected {dof} joint positions for {robot_instance.__class__.__name__}, "
                f"got {len(positions)}"
            )

        # Check each joint against its ranges
        for i, (position, (min_limit, max_limit)) in enumerate(
            zip(positions, joint_ranges)
        ):
            if not (min_limit <= position <= max_limit):
                raise ValueError(
                    f"Joint {i} position {position:.3f} outside range "
                    f"[{min_limit:.3f}, {max_limit:.3f}]"
                )

        if velocity is not None and velocity > v:
            raise ValueError(f"Velocity {velocity} exceeds max {v}")

        if acceleration is not None and acceleration > a:
            raise ValueError(f"Acceleration {acceleration} exceeds max {a}")

    @staticmethod
    def get_joint_positions() -> None:
        """No validation required for joint position getter."""
        pass

    @staticmethod
    def move_cartesian(robot_instance: Properties, pose: list[float]) -> None:
        """Validate 6DOF cartesian pose (x, y, z, rx, ry, rz)."""
        if not isinstance(pose, list):
            raise TypeError(
                f"Cartesian pose must be a list, got {type(pose).__name__}"
            )

        dof = robot_instance.DOF
        if len(pose) != dof:
            raise ValueError(
                f"Cartesian pose must have {dof} elements (x,y,z,rx,ry,rz), got {len(pose)}"
            )

        if not all(isinstance(p, (int, float)) for p in pose):
            invalid_types = [
                type(p).__name__
                for p in pose
                if not isinstance(p, (int, float))
            ]
            raise TypeError(
                f"All pose values must be numbers, found: {set(invalid_types)}"
            )

    @staticmethod
    def get_cartesian_position() -> None:
        """No validation required for cartesian position getter."""
        pass

    @staticmethod
    def stop_motion() -> None:
        """No validation required for stop motion command."""
        pass

    @staticmethod
    def get_robot_state() -> None:
        """No validation required for robot state getter."""
        pass
