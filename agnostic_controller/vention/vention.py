from agnostic_controller.templates import SocketController as SCT, Commands
import time
from typing import Union, List

class Vention(SCT, Commands):
    def __init__(self, ip: str = "192.168.7.2", port: int = 9999):
        super().__init__(ip, port)

    def connect(self) -> None:
        """Establishes connection to the Vention controller and checks readiness."""
        super().connect()
        response = self.send_command("isReady;", timeout=1)
        
        if "MachineMotion connection established" not in response and "MachineMotion isReady = true" not in response:
            raise AssertionError(f"Failed to connect to Vention robot. Received response: {response}")
        
        # Optional: Check E-Stop status
        estop_status = self.send_command("estop/status;", timeout=10)
        if "true" in estop_status:
            release_response = self.send_command("estop/release/request;", timeout=10)
            assert "Ack estop/release/request" in release_response, "Failed to release E-Stop"

    def disconnect(self) -> None:
        """Disconnects from the Vention controller."""
        # self.stop_motion()
        super().disconnect()

    def sleep(self, seconds: float) -> None:
        """Pauses execution for a specified number of seconds."""
        time.sleep(seconds)

    def home(self) -> None:
        """Homes all axes of the robot."""
        response = self.send_command("im_home_axis_all;", timeout=30)
        if "completed" not in response:
            raise AssertionError(f"Homing failed. {response}")

    def move_joints(self, joint_positions: Union[List[float], float, int], *args, **kwargs) -> None:
        """Moves the axes to specified positions"""
        valid_axes = {1, 2, 3}

        # Normalize input to a list
        if isinstance(joint_positions, (float, int)):
            joint_positions = [joint_positions]
        elif not isinstance(joint_positions, list) or not all(isinstance(pos, (int, float)) for pos in joint_positions):
            raise TypeError("Joint positions must be a list of numeric values, or a single numeric value.")

        if len(joint_positions) > len(valid_axes):
            raise ValueError(f"Too many joint positions. Maximum supported axes are {len(valid_axes)}.")

        # Set speed and acceleration
        self.send_command("SET speed/{}/;".format(kwargs.get('speed', 300)))
        self.send_command("SET acceleration/{}/;".format(kwargs.get('acceleration', 100)))

        move_type = kwargs.get('move_type', 'abs')
        if move_type not in ['abs', 'rel']:
            raise ValueError("Invalid move type. Must be 'abs' or 'rel'.")
        # elif move_type == 'rel':
        #     prefix = "de"
        # else:
        #     prefix = "de"

        # Send movement commands for each axis
        for axis, position in enumerate(joint_positions, start=1):
            if axis not in valid_axes:
                raise ValueError(f"Invalid axis: {axis}. Must be one of {valid_axes}.")
            
            self.send_command(f"SET de_move_{move_type}{axis}/{position}/;")
        
        # Execute movement
        assert self.send_command(f"de_move_{move_type}_exec;", timeout=30) == "Ack", "Failed to execute movement."
        time.sleep(5)  # Optional delay for command processing
        
        # Wait for motion completion
        timeout = 60  # seconds
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            time.sleep(3)
            motion_status = self.send_command("isMotionCompleted;").strip()
            if "true" in motion_status:
                return


        raise TimeoutError("Movement timed out.")

    def get_joint_positions(self, axis: Union[int, None] = None, *args, **kwargs) -> Union[List[float], float]:
        """Gets the current position of an axis or all axes."""
        valid_axes = {1, 2, 3}

        if axis is not None:
            if axis not in valid_axes:
                raise ValueError(f"Invalid axis: {axis}. Must be one of {valid_axes} or None for all axes.")
            return self._get_axis_position(axis)

        return [self._get_axis_position(ax) for ax in valid_axes]

    def _get_axis_position(self, axis: int) -> float:
        """Fetches the position of a specific axis."""
        response = self.send_command(f"GET im_get_controller_pos_axis_{axis};", timeout=10)
        try:
            stripped_response = response.strip("()")
            if "undefined" in stripped_response: # Response: (undefined) if axis does not exists on robot
                return 0.0
            elif "-1" in stripped_response:
                raise RuntimeError("Invalid axis position response from robot. Have you homed the robot?")
            else:
                return float(stripped_response)
        except ValueError:
            raise RuntimeError(f"Failed to parse position from response: '{response}'")

    def stop_motion(self) -> None:
        if "Ack" not in self.send_command("im_stop;"):
            raise RuntimeError("Failed to stop motion.")

    def move_cartesian(self, robot_pose: List[float], *args, **kwargs) -> None:
        """Moves the robot to a specified Cartesian pose (not implemented)."""
        raise NotImplementedError("This method is not implemented yet.")

    def get_cartesian_position(self, *args, **kwargs) -> List[float]:
        """Gets the current Cartesian position of the robot (not implemented)."""
        raise NotImplementedError("This method is not implemented yet.")

    def get_robot_state(self) -> dict:
        """Gets the current state of the robot (not implemented)."""
        raise NotImplementedError("This method is not implemented yet.")
    
    def reset(self) -> None:
        """Resets the robot to its initial state."""
        self.send_command("estop/systemreset/request;")