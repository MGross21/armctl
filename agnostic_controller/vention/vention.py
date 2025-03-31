from agnostic_controller.templates import SocketController as SCT
import time
from typing import Union, List

class Vention(SCT):
    def __init__(self, ip: str = "192.168.7.2", port: int = 9999):
        super().__init__(ip, port)

    def connect(self) -> None:
        """Establishes connection to the Vention controller and checks readiness."""
        super().connect()
        response = self.send_command("isReady;", timeout=1)
        
        if "MachineMotion connection established" not in response and "MachineMotion isReady = true" not in response:
            raise AssertionError(f"Failed to connect to Vention robot. Received response: {response}")
        
        # Optional: Check E-Stop status
        # estop_status = self.send_command("estop/status;", timeout=10)
        # if "true" in estop_status:
        #     release_response = self.send_command("estop/release/request;", timeout=10)
        #     assert "Ack estop/release/request" in release_response, "Failed to release E-Stop"

    def sleep(self, seconds: float) -> None:
        """Pauses execution for a specified number of seconds."""
        time.sleep(seconds)

    def home(self) -> None:
        """Homes all axes of the robot."""
        response = self.send_command("im_home_axis_all;")
        assert "completed" in response, "Homing failed"

    def move_joints(self, joint_positions: List[float]) -> None:
        """Moves the axis to specified positions (absolute movement)."""
        if isinstance(joint_positions, (int, float)):
            joint_positions = [joint_positions]
        
        if len(joint_positions) != 1:
            raise ValueError("Single axis slider only accepts one joint position.")
        
        # Send absolute movement command for axis 1
        position = joint_positions[0]
        self.send_command(f"SET de_move_abs_1/{position}/;")
        
        # Execute movement
        self.send_command("de_move_abs_exec;")
        
        # Wait for motion completion
        timeout = 30  # seconds
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            motion_status = self.send_command("isMotionCompleted;")
            if "true" in motion_status:
                return
            time.sleep(0.1)
        
        raise TimeoutError("Movement timed out.")

    def get_joint_positions(self, axis: Union[int, None] = None) -> Union[List[float], float]:
        """Gets the current position of an axis or all axes."""
        valid_axes = [1, 2, 3]
        
        if axis is not None and axis not in valid_axes:
            raise ValueError("Axis must be 1, 2, 3, or None for all axes.")
        
        def fetch_position(ax: int) -> float:
            response = self.send_command(f"GET im_get_controller_pos_axis_{ax};", timeout=10)
            return float(response.split('=')[-1].strip('; '))

        if axis is not None:
            return fetch_position(axis)
        
        positions = [fetch_position(ax) for ax in valid_axes]
        return positions

    def stop_motion(self) -> None:
        """Stops all motion."""
        stop_response = self.send_command("Stop all motion;")
        
        if "Ack Stop all motion" not in stop_response:
            raise RuntimeError("Failed to stop motion.")

    def move_cartesian(self, robot_pose: List[float], *args, **kwargs) -> None:
        """Moves the robot to a specified Cartesian pose (not implemented)."""
        raise NotImplementedError("This method is not implemented yet.")

    def get_cartesian_position(self) -> List[float]:
        """Gets the current Cartesian position of the robot (not implemented)."""
        raise NotImplementedError("This method is not implemented yet.")

    def get_robot_state(self) -> dict:
        """Gets the current state of the robot (not implemented)."""
        raise NotImplementedError("This method is not implemented yet.")