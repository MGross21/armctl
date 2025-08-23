import time
from typing import List, Optional, Union

from armctl.templates import Commands
from armctl.templates import SocketController as SCT
from armctl.templates import Properties
from armctl.templates.logger import logger
from armctl.utils import CommandCheck as cc


class Vention(SCT, Commands, Properties):
  

    def __init__(self, ip: str = "192.168.7.2", port: int = 9999):
        super().__init__(ip, port)
        self.JOINT_RANGES = [
            (0, 1250),  # Axis 1 range in mm
            (0, 1250),  # Axis 2 range in mm
            (0, 1250),  # Axis 3 range in mm
        ]
        self.MAX_JOINT_VELOCITY = 3000  # mm/s
        self.MAX_JOINT_ACCELERATION = 1000  # mm/s^2

    def connect(self) -> None:
        """Establishes connection to the Vention controller and checks readiness."""
        super().connect()
        response = self.send_command(
            "isReady;", timeout=3, suppress_input=True, suppress_output=True
        )
        if (
            "MachineMotion connection established" not in response
            and "MachineMotion isReady = true" not in response
        ):
            raise ConnectionError(
                f"Failed to connect to Vention robot. Received response: {response}"
            )
        # Check E-Stop status. Attempt to Release if engaged.
        estop_status = self.send_command(
            "estop/status;",
            timeout=10,
            suppress_input=True,
            suppress_output=True,
        )
        if "true" in estop_status:
            release_response = self.send_command(
                "estop/release/request;",
                timeout=10,
                suppress_input=True,
                suppress_output=True,
            )
            if "Ack estop/release/request" not in release_response:
                raise RuntimeError(
                    f"Failed to release E-Stop. Received response: {release_response}"
                )

    def disconnect(self) -> None:
        """Disconnects from the Vention controller."""
        super().disconnect()

    def sleep(self, seconds: float) -> None:
        """Pauses execution for a specified number of seconds."""
        cc.sleep(seconds)
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
        move_type: str = "abs",
    ) -> None:
        """Moves the axes to specified positions."""
        if move_type not in ("abs", "rel"):
            raise ValueError("Invalid move type. Must be 'abs' or 'rel'.")
        
        # Normalize input to a list
        if isinstance(pos, (float, int)):
            pos = [pos]
        
        # Validate using command checks
        cc.move_joints(self, pos, speed, acceleration)
        
        # Handle relative moves by adding to current positions
        if move_type == "rel":
            current_positions = self.get_joint_positions()
            pos = [curr + rel for curr, rel in zip(current_positions, pos)]
            # Re-validate the absolute positions after relative calculation
            cc.move_joints(self, pos, speed, acceleration)
        
        # Send commands to robot
        self.send_command(f"SET speed/{speed}/;")
        self.send_command(f"SET acceleration/{acceleration}/;")
        
        for axis, p in enumerate(pos, start=1):
            if axis > self.DOF:
                raise ValueError(
                    f"Invalid axis: {axis}. Robot has {self.DOF} axes."
                )
            ack = self.send_command(
                f"SET im_move_{move_type}_{axis}/{p}/;", timeout=30
            )
            if ack != "Ack":
                raise RuntimeError(f"Failed to set position for axis {axis}.")
        self._wait_for_finish()

    def _wait_for_finish(
        self, delay: float = 1.0, timeout: float = 120.0
    ) -> None:
        """Waits for the robot to finish its current task, with a timeout."""
        logger.info("Waiting for motion to complete...")
        start_time = time.time()
        while True:
            if "true" in self.send_command(
                "isMotionCompleted;",
                timeout=60,
                suppress_input=True,
                suppress_output=True,
            ):
                break
            if (time.time() - start_time) > timeout:
                raise TimeoutError(
                    "Motion did not complete within the expected time."
                )
            time.sleep(delay)
        logger.info("Motion completed.")

    def get_joint_positions(
        self, axis: Optional[int] = None
    ) -> Union[List[float], float]:
        """Gets the current position of an axis or all axes."""
        cc.get_joint_positions()
        
        if axis is not None:
            if axis < 1 or axis > self.DOF:
                raise ValueError(
                    f"Invalid axis: {axis}. Must be between 1 and {self.DOF}."
                )
            return self._get_axis_position(axis)
        
        axis_positions = [self._get_axis_position(ax) for ax in range(1, self.DOF + 1)]
        logger.receive(f"Received Response: {axis_positions}")
        return axis_positions

    def _get_axis_position(self, axis: int) -> float:
        """Fetches the position of a specific axis."""
        response = self.send_command(
            f"GET im_get_controller_pos_axis_{axis};",
            timeout=10,
            suppress_output=True,
        )
        try:
            stripped_response = response.strip("()")
            if "undefined" in stripped_response:
                return 0.0
            if "-1" in stripped_response:
                raise RuntimeError(
                    "Invalid axis position response from robot. Have you homed the robot?"
                )
            return float(stripped_response)
        except ValueError:
            raise RuntimeError(
                f"Failed to parse position from response: '{response}'"
            )

    def stop_motion(self) -> None:
        """Stops all robot motion."""
        cc.stop_motion()
        ack = self.send_command("im_stop;")
        if "Ack" not in ack:
            raise RuntimeError("Failed to stop motion.")

    def move_cartesian(self, pose: List[float]) -> None:
        """Moves the robot to a specified Cartesian pose (not implemented)."""
        cc.move_cartesian(self, pose)
        raise NotImplementedError("This method is not implemented yet.")

    def get_cartesian_position(self) -> List[float]:
        """Gets the current Cartesian position of the robot (not implemented)."""
        cc.get_cartesian_position()
        raise NotImplementedError("This method is not implemented yet.")

    def get_robot_state(self) -> None:
        """Gets the current state of the robot."""
        cc.get_robot_state()
        self.send_command("estop/status;")
        self.get_joint_positions()
