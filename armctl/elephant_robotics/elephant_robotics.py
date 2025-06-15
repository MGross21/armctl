from armctl.templates import SocketController as SCT, Commands
import time

class ElephantRobotics(SCT, Commands):
    def __init__(self, ip: str, port: int):
        super().__init__(ip, port)
        self.JOINT_RANGES = [
            (-180.00, 180.00),
            (-270.00, 90.00),
            (-150.00, 150.00),
            (-260.00, 80.00),
            (-168.00, 168.00),
            (-174.00, 174.00)
        ]
        self.DOF = len(self.JOINT_RANGES)

    def connect(self):
        super().connect()  # Socket Connection

        assert self.send_command("power_on()") == "power_on:[ok]"  # Power on the robot
        assert self.send_command("state_on()") == "state_on:[ok]"  # Enable the system

    def disconnect(self):
        self.stop_motion()  # Stop any ongoing motion
        # assert self.send_command("state_off()") == "state_off:[ok]"  # Shut down the system, but the robot is still powered on
        # assert self.send_command("power_off()") == "power_off:[ok]"  # Power off the robot
        super().disconnect()  # Socket disconnection

    def _waitforfinish(self):
        while True:
            if self.send_command("wait_command_done()", timeout=60) == "wait_command_done:0":
                break
            time.sleep(0.25)

    def sleep(self, seconds):
        assert isinstance(seconds, (int, float)), "Seconds must be a numeric value."
        assert seconds >= 0, "Seconds must be a non-negative value."
        self.send_command(f"wait({seconds})")
        time.sleep(seconds)

    def move_joints(self, 
                    joint_positions:list[float],
                    speed:int=500,
                    *args, **kwargs):
        """
        Move the robot to the specified joint positions.

        Parameters
        ----------
        joint_positions : list of float
            Joint positions in degrees [j1, j2, j3, j4, j5, j6].
        speed : int, optional
            Speed of the movement, range 0 ~ 2000 (default: 200).
        DOF : int, optional
            Degrees of freedom (default: 6).
        """

        if len(joint_positions) != self.DOF:
            raise ValueError("Joint positions must have 6 elements")

        for i, (low, high) in enumerate(self.JOINT_RANGES):
            if not (low <= joint_positions[i] <= high):
                raise ValueError(f"Joint {i+1} angle out of range: {low} ~ {high}")

        if not (0 <= speed <= 2000):
            raise ValueError("Speed out of range: 0 ~ 2000")

        command = "set_angles"
        response = self.send_command(f"{command}({','.join(map(str, joint_positions))},{speed})")
        assert response == f"{command}:[ok]", f"Failed to move joints: {response}"

        while any(abs(a - b) > 3 for a, b in zip(self.get_joint_positions(), joint_positions)):
            time.sleep(1)

    def move_cartesian(self, 
                       robot_pose:tuple[float,float,float,float,float,float], 
                       speed:int=500,
                       *args, **kwargs) -> None:
        """
        Move the robot to the specified Cartesian coordinates.

        Parameters
        ----------
        robot_pose : tuple of float
            Cartesian coordinates in the format `[x, y, z, rx, ry, rz]`.
        speed : int, optional
            Speed of the movement, range 0 ~ 2000 (default: 500).
        """

        if not (0 <= speed <= 2000):
            raise ValueError("Speed out of range: 0 ~ 2000")
        if len(robot_pose) != 6:
            raise ValueError("Robot pose must have 6 elements: [x, y, z, rx, ry, rz]")

        command = f"set_coords({','.join(map(str, robot_pose))},{speed})"

        assert self.send_command(command) == "set_coords:[ok]"

        while not all(abs(a - b) <= 1 for a, b in zip(self.get_cartesian_position(), robot_pose)):
            time.sleep(1)

    def get_joint_positions(self, *args, **kwargs):
        response = self.send_command("get_angles()")
        if response == "[-1.0, -2.0, -3.0, -4.0, -1.0, -1.0]":
            raise ValueError("Invalid joint positions response from robot")
        joint_positions = list(map(float, response[response.index("[")+1:response.index("]")].split(",")))  # From string list to float list
        return [round(x, 2) for x in joint_positions]

    def get_cartesian_position(self, *args, **kwargs):
        response = self.send_command("get_coords()")  # [x, y, z, rx, ry, rz]
        if response == "[-1.0, -2.0, -3.0, -4.0, -1.0, -1.0]":
            raise ValueError("Invalid cartesian position response from robot")
        cartesian_position = list(map(float, response[response.index("[")+1:response.index("]")].split(",")))  # From string list to float list
        return [round(x, 2) for x in cartesian_position]

    def stop_motion(self):
        command = "task_stop"
        response = self.send_command(f"{command}()")

        if not response.startswith(f"{command}:"):
            raise SystemError(f"Unexpected response: {response}")

        result = response.split(":", 1)[1]

        if result != "[ok]":
            raise SystemError(result)
        return True

    def get_robot_state(self):
        command = "check_running"
        response = self.send_command(f"{command}()")

        if not response.startswith(f"{command}:"):
            raise SystemError(f"Unexpected response format: {response}")

        status = response.partition(":")[2]  # Get everything after the colon

        if status == "1":
            return True
        elif status == "0":
            return False
        else:
            raise ValueError(f"Unknown robot state: {status}")
