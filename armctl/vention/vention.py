import time
from typing import Union, List, Optional
from armctl.templates import SocketController as SCT, Commands
from armctl.templates.logger import logger

class Vention(SCT, Commands):
    MAX_JOINT_RANGE = 1250  # mm
    MIN_JOINT_RANGE = 0     # mm
    VALID_AXES = (1, 2, 3)

    def __init__(self, ip: str = "192.168.7.2", port: int = 9999):
        super().__init__(ip, port)

    def connect(self) -> None:
        """Establishes connection to the Vention controller and checks readiness."""
        super().connect()
        response = self.send_command("isReady;", timeout=3, suppress_input=True, suppress_output=True)
        if ("MachineMotion connection established" not in response and
                "MachineMotion isReady = true" not in response):
            raise ConnectionError(f"Failed to connect to Vention robot. Received response: {response}")
        # Check E-Stop status. Attempt to Release if engaged.
        estop_status = self.send_command("estop/status;", timeout=10, suppress_input=True, suppress_output=True)
        if "true" in estop_status:
            release_response = self.send_command("estop/release/request;", timeout=10, suppress_input=True, suppress_output=True)
            if "Ack estop/release/request" not in release_response:
                raise RuntimeError(f"Failed to release E-Stop. Received response: {release_response}")

    def disconnect(self) -> None:
        """Disconnects from the Vention controller."""
        super().disconnect()

    def sleep(self, seconds: float) -> None:
        """Pauses execution for a specified number of seconds."""
        if not isinstance(seconds, (int, float)):
            raise TypeError("Seconds must be a numeric value.")
        if seconds < 0:
            raise ValueError("Seconds must be a non-negative value.")
        time.sleep(seconds)

    def home(self) -> None:
        """Homes all axes of the robot."""
        response = self.send_command("im_home_axis_all;", timeout=30)
        if "completed" not in response:
            raise RuntimeError(f"Homing failed. {response}")
        self._wait_for_finish(delay=1)

    def move_joints(
        self,
        pos: Union[List[float], float, int],
        speed: int = 2500,
        acceleration: int = 500,
        move_type: str = 'abs'
    ) -> None:
        """Moves the axes to specified positions."""
        if move_type not in ('abs', 'rel'):
            raise ValueError("Invalid move type. Must be 'abs' or 'rel'.")
        # Normalize input to a list
        if isinstance(pos, (float, int)):
            pos = [pos]
        elif not (isinstance(pos, list) and all(isinstance(p, (int, float)) for p in pos)):
            raise TypeError("Joint positions must be a list of numeric values, or a single numeric value.")
        if len(pos) > len(self.VALID_AXES):
            raise ValueError(f"Too many joint positions. Maximum supported axes are {len(self.VALID_AXES)}.")
        # Check if in range
        if move_type == "abs":
            for p in pos:
                if not (self.MIN_JOINT_RANGE <= p <= self.MAX_JOINT_RANGE):
                    raise ValueError(f"Absolute joint positions must be within the range {self.MIN_JOINT_RANGE} to {self.MAX_JOINT_RANGE} mm.")
        elif move_type == "rel":
            current_positions = self.get_joint_positions()
            for curr_pos, rel_pos in zip(current_positions, pos):
                new_pos = curr_pos + rel_pos
                if not (self.MIN_JOINT_RANGE <= new_pos <= self.MAX_JOINT_RANGE):
                    raise ValueError(f"Relative joint positions must result in positions within the range {self.MIN_JOINT_RANGE} to {self.MAX_JOINT_RANGE} mm.")
        if not (0 <= speed <= 3000):
            raise ValueError("Speed must be between 0 and 3000mm/s.")
        if not (0 <= acceleration <= 1000):
            raise ValueError("Acceleration must be between 0 and 1000mm/s^2.")
        self.send_command(f"SET speed/{speed}/;")
        self.send_command(f"SET acceleration/{acceleration}/;")
        for axis, p in enumerate(pos, start=1):
            if axis not in self.VALID_AXES:
                raise ValueError(f"Invalid axis: {axis}. Must be one of {self.VALID_AXES}.")
            ack = self.send_command(f"SET im_move_{move_type}_{axis}/{p}/;", timeout=30)
            if ack != "Ack":
                raise RuntimeError(f"Failed to set position for axis {axis}.")
        self._wait_for_finish()

    def _wait_for_finish(self, delay: float = 1.0, timeout: float = 120.0) -> None:
        """Waits for the robot to finish its current task, with a timeout."""
        logger.info("Waiting for motion to complete...")
        start_time = time.time()
        while True:
            if "true" in self.send_command("isMotionCompleted;", timeout=60, suppress_input=True, suppress_output=True):
                break
            if (time.time() - start_time) > timeout:
                raise TimeoutError("Motion did not complete within the expected time.")
            time.sleep(delay)
        logger.info("Motion completed.")

    def get_joint_positions(self, axis: Optional[int] = None) -> Union[List[float], float]:
        """Gets the current position of an axis or all axes."""
        if axis is not None:
            if axis not in self.VALID_AXES:
                raise ValueError(f"Invalid axis: {axis}. Must be one of {self.VALID_AXES} or None for all axes.")
            return self._get_axis_position(axis)
        axis_positions = [self._get_axis_position(ax) for ax in self.VALID_AXES]
        logger.receive(f"Received Response: {axis_positions}")
        return axis_positions

    def _get_axis_position(self, axis: int) -> float:
        """Fetches the position of a specific axis."""
        response = self.send_command(f"GET im_get_controller_pos_axis_{axis};", timeout=10, suppress_output=True)
        try:
            stripped_response = response.strip("()")
            if "undefined" in stripped_response:
                return 0.0
            if "-1" in stripped_response:
                raise RuntimeError("Invalid axis position response from robot. Have you homed the robot?")
            return float(stripped_response)
        except ValueError:
            raise RuntimeError(f"Failed to parse position from response: '{response}'")

    def stop_motion(self) -> None:
        """Stops all robot motion."""
        ack = self.send_command("im_stop;")
        if "Ack" not in ack:
            raise RuntimeError("Failed to stop motion.")

    def move_cartesian(self, pose: List[float]) -> None:
        """Moves the robot to a specified Cartesian pose (not implemented)."""
        raise NotImplementedError("This method is not implemented yet.")

    def get_cartesian_position(self) -> List[float]:
        """Gets the current Cartesian position of the robot (not implemented)."""
        raise NotImplementedError("This method is not implemented yet.")

    def get_robot_state(self) -> None:
        """Gets the current state of the robot."""
        self.send_command("estop/status;")
        self.get_joint_positions()