from armctl.templates import SerialController as Serial
from armctl.templates import SocketController as Socket
from armctl.templates import Commands
from armctl.templates import Properties
from armctl.utils import CommandCheck as cc
from armctl.utils import units as uu
import math

### Notes ###
# - Command Format: CMD(arg)
# - Command units are degrees & mm.


class DobotSerial(Serial, Commands, Properties):
    def __init__(self, ip: str, port: int):
        super().__init__(ip, port)
        self.JOINT_RANGES = uu.joints2rad(
            [
                (-135.00, 135.00),
                (-5.00, 80.00),
                (-10.00, 85.00),
                (-145.00, 145.00),
            ]
        )
        self.MAX_JOINT_VELOCITY = None
        self.MAX_JOINT_ACCELERATION = None

        raise NotImplementedError(
            f"{self.__class__.__name__.upper()} is not yet supported."
        )

    def sleep(self, seconds):
        cc.sleep(seconds)
        self.send_command(f"sleep({seconds})")

    def move_joints(self, pos) -> str:
        "MovJ"

        cc.move_joints(self, pos)

        command = "MOVJ({})".format(",".join(map(str, pos)))
        return self.send_command(command)

    def move_cartesian(self, pose) -> str:
        """
        Moves the robot arm to a specified Cartesian position.

        Parameters:
            pose (list or tuple): Target position as [x, y, z, r]. x, y, z are in meters and r is in radians.

        Returns:
            str: The response from the robot after executing the MOVEL command.

        Notes:
            - The method sends a MOVEL command to the robot controller.
            - The pose is expected in m for x, y, z and radians for r.
        """
        cc.move_cartesian(self, pose)
        # Convert x, y, z from meters to millimeters, r from radians to degrees

        command = "MOVEL({})".format(
            ",".join(
                map(
                    str,
                    [
                        pose[0] * 1000,  # x in mm
                        pose[1] * 1000,  # y in mm
                        pose[2] * 1000,  # z in mm
                        math.degrees(pose[3]),  # r in degrees
                    ],
                )
            )
        )
        return self.send_command(command)

    def get_joint_positions(self):
        pass

    def get_cartesian_position(self):
        pass

    def stop_motion(self):
        pass

    def get_robot_state(self):
        pass


class Codes:
    COMMAND = {
        0: "No error: Delivered successfully",
        5: "Robot in Motion (Immediate Execution)",
        7: "Robot in Motion (Queued)",
        -1: "Failed to receive or execute",
        -10000: "Command does not exist",
        -20000: "Incorrect number of command parameters",
        -30001: "First parameter type incorrect",
        -30002: "Second parameter type incorrect",
        -30003: "Third parameter type incorrect",
        -30004: "Fourth parameter type incorrect",
        -40001: "First parameter out of range",
        -40002: "Second parameter out of range",
        -40003: "Third parameter out of range",
        -40004: "Fourth parameter out of range",
    }

    STATE = {
        1: "ROBOT_MODE_INIT - Initialized status",
        2: "ROBOT_MODE_BRAKE_OPEN - Brake switched on",
        3: "ROBOT_MODE_POWER_STATUS - Power-off status",
        4: "ROBOT_MODE_DISABLED - Disabled (no brake switched on)",
        5: "ROBOT_MODE_ENABLE - Enabled and idle (no project running, no alarm)",
        6: "ROBOT_MODE_BACKDRIVE - Drag mode",
        7: "ROBOT_MODE_RUNNING - Running status (including trajectory playback/fitting, executing motion commands, running project)",
        8: "ROBOT_MODE_RECORDING - Trajectory recording mode",
        9: "ROBOT_MODE_ERROR - There are uncleared alarms. This status has the highest priority. It returns 9 when there is an alarm, regardless of the status of the robot arm.",
        10: "ROBOT_MODE_PAUSE - Pause status",
        11: "ROBOT_MODE_JOG - Jogging status",
    }

    @classmethod
    def get_cmd_message(cls, code: int) -> str:
        return cls.COMMAND.get(code, f"Unknown error code: {code}")

    @classmethod
    def get_state_message(cls, code: int) -> str:
        return cls.STATE.get(code, f"Unknown state code: {code}")


class DobotSocket(Socket, Commands):
    def __init__(self, ip: str, port: int | tuple[int, int] = (30_003, 30_004)):
        super().__init__(ip, port)

    def _send(self, s: str):
        """
        Message Response Format:
        "ErrorID,{value,...,valueN},Message name(Param1,Param2,Param3……ParamN);"

        - If ErrorID is 0, the command is received successfully.
        - {value,...,valueN} refers to the return value. {} means no return value.
        - Message name(Param1,Param2,Param3……ParamN) refers to the content delivered.
        """
        c, r, m = self.send_command(f"{s}\n").strip().split(sep=",")
        code = int(c)
        response = r.strip("{}")
        message = m.strip(";")
        return code, response, message

    def _send_and_check(
        self, cmd: str, motion: bool = False
    ) -> list[float] | None:
        """Send a command to the robot and check for errors in the response."""

        code, response, _ = self._send(cmd)  # Queue Command

        if 0 == code and response == "":
            # Return the values inside the curly braces as a list, or None if empty
            result = (
                [float(x) for x in response.split(",")] if response else None
            )

            if motion:
                self._send("Sync()")
                code2, _, _ = self._send("RobotMode()")  # Get the robot
                # TODO: check order of status codes
                # if code2 in (5, 7):
                #     pass
                # else:
                #     raise RuntimeError(
                #         f"Error {code2}: {Codes.get_cmd_message(code2)}"
                #     )
            return result
        else:
            raise RuntimeError(f"Error {code}: {Codes.get_cmd_message(code)}")

    def connect(self):
        super().connect()
        # 0, 1, or all 4 parameters can be set to enable the robot.
        enable = {
            "load": 0.0,  # Load in kg
            "centerX": 0.0,  # Center X in mm (-500 to 500)
            "centerY": 0.0,  # Center Y in mm (-500 to 500)
            "centerZ": 0.0,  # Center Z in mm (-500 to 500)
        }
        self._send_and_check(
            "EnableRobot({},{},{},{})".format(
                enable["load"],
                enable["centerX"],
                enable["centerY"],
                enable["centerZ"],
            )
        )

        # Clear the alarms of the robot
        self._send_and_check("ClearError()")
        # Required to restart motion Queue after clearing alarms
        self._send_and_check("Continue()")
        # Stop the robot and clear the planned command queue
        self._send_and_check("ResetRobot()")

    def disconnect(self):
        # self._send_and_check("StopScript()")

        super().disconnect()

    def get_robot_state(self) -> str:
        """Get the current state of the robot."""
        code, _, _ = self._send("RobotMode()")
        return Codes.get_state_message(code)

    def get_joint_positions(self):
        """Get the joint coordinates of current posture"""
        return self._send_and_check("GetAngle()")

    def get_cartesian_position(self):
        """Get the Cartesian coordinates of current posture"""
        return self._send_and_check("GetPose()")

    def move_cartesian(self, pose):
        self._send_and_check("MoveJ({},{},{},{})".format(*pose), motion=True)

    def move_joints(self, pos):
        self._send_and_check(
            "JointMoveJ({})".format(",".join(map(str, pos))), motion=True
        )

    def sleep(self, seconds):
        self._send_and_check(f"wait({seconds})")
