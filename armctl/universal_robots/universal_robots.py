from __future__ import annotations

import math
import time as _time

from armctl.templates import Commands, Properties
from armctl.templates import SocketController as SCT
from armctl.templates.logger import logger
from armctl.utils import CommandCheck as cc

from .protocols.codes import RobotMode, RuntimeState, SafetyMode
from .protocols.rtde import RTDE

### Notes ###
# Command Format: CMD(args)\n
# Output Units: radians, meters


class UniversalRobots(SCT, Commands, Properties):
    def __init__(self, ip: str, port: int | tuple[int, int] = 30_002):
        super().__init__(ip, port)
        self.JOINT_RANGES = [
            (-2 * math.pi, 2 * math.pi),
            (-2 * math.pi, 2 * math.pi),
            (-2 * math.pi, 2 * math.pi),
            (-2 * math.pi, 2 * math.pi),
            (-2 * math.pi, 2 * math.pi),
            (-2 * math.pi, 2 * math.pi),
        ]
        # Source: https://forum.universal-robots.com/t/maximum-axis-speed-acceleration/13338/2
        self.MAX_JOINT_VELOCITY = 2.0  # rad/s
        # Source: https://forum.universal-robots.com/t/maximum-axis-speed-acceleration/13338/4
        self.MAX_JOINT_ACCELERATION = 10.0  # rad/s^2
        self.rtde: RTDE | None = None

    def connect(self):
        super().connect()
        self.rtde = RTDE(self.ip)

    def disconnect(self):
        try:
            self.stop_motion()
        except Exception:
            pass
        if self.rtde is not None:
            self.rtde.c.disconnect()
            self.rtde = None
        super().disconnect()

    def sleep(self, seconds: float) -> None:
        cc.sleep(seconds)
        self.send_command(f"sleep({seconds})\n")
        _time.sleep(seconds)  # block Python side while controller sleeps

    def move_joints(
        self,
        pos: list[float],
        speed: float = 0.1,
        acceleration: float = 0.05,
        t: float = 0.0,
        radius: float = 0.0,
    ) -> None:
        """MoveJ — move to joint positions.

        Parameters
        ----------
        pos : list of float
            Target joint positions in radians [j1..j6].
        speed : float
            Speed in rad/s.
        acceleration : float
            Acceleration in rad/s^2.
        t : float
            Move duration in seconds (overrides speed/acceleration when > 0).
        radius : float
            Blend radius in metres. Non-zero disables blocking at this waypoint.
        """
        cc.move_joints(self, pos, speed, acceleration)
        command = (
            f"write_output_integer_register(0,0)\n"
            f"movej([{','.join(map(str, pos))}],"
            f" a={acceleration}, v={speed}, t={t}, r={radius})\n"
            f"write_output_integer_register(0,1)\n"
        )
        self.send_command(
            command, timeout=t + 10, suppress_output=True, raw_response=False
        )
        if radius == 0.0:
            timeout = (t + 15.0) if t > 0 else 120.0
            self.rtde.wait_until_stopped(timeout=timeout)

    def move_cartesian(
        self,
        pose: list[float],
        move_type: str = "movel",
        speed: float = 0.1,
        acceleration: float = 0.1,
        time: float = 0.0,
        radius: float = 0.0,
    ) -> None:
        """Move to Cartesian pose.

        Parameters
        ----------
        pose : list of float
            Target pose [x, y, z, rx, ry, rz] in metres and radians.
        move_type : str
            "movel" (linear), "movep" (circular), or "movej" (joint-space).
        speed : float
            Velocity in m/s.
        acceleration : float
            Acceleration in m/s^2.
        time : float
            Move duration in seconds (overrides speed/acceleration when > 0).
        radius : float
            Blend radius in metres. Non-zero disables blocking at this waypoint.
        """
        if move_type not in {"movel", "movep", "movej"}:
            raise ValueError(
                "Unsupported move type. Use 'movel', 'movep', or 'movej'."
            )

        cc.move_cartesian(self, pose)

        base = (
            f"{move_type}(p[{','.join(map(str, pose))}],"
            f" a={acceleration}, v={speed}"
        )
        if move_type in {"movel", "movej"}:
            command = f"write_output_integer_register(0,0)\n{base}, t={time}, r={radius})\nwrite_output_integer_register(0,1)\n"
        else:  # movep
            command = f"write_output_integer_register(0,0)\n{base}, r={radius})\nwrite_output_integer_register(0,1)\n"

        self.send_command(command, suppress_output=True)
        if radius == 0.0:
            timeout = (time + 15.0) if time > 0 else 120.0
            self.rtde.wait_until_stopped(timeout=timeout)

    def stop_motion(self) -> None:
        deceleration = 2.0  # rad/s^2
        self.send_command(f"stopj({deceleration})\n", suppress_output=True)

    def get_joint_positions(self) -> list[float]:
        """Return actual joint positions in radians."""
        angles = self.rtde.joint_angles()
        logger.receive(f"Received response: {angles}")
        return angles

    def get_joint_velocities(self) -> list[float]:
        """Return actual joint velocities in rad/s."""
        vels = self.rtde.joint_velocities()
        logger.receive(f"Received response: {vels}")
        return vels

    def get_joint_currents(self) -> list[float]:
        """Return actual joint currents in Amperes."""
        currents = self.rtde.joint_currents()
        logger.receive(f"Received response: {currents}")
        return currents

    def get_joint_torques(self) -> list[float]:
        """Return joint torques in Nm. Requires controller >= 5.23.0.0."""
        torques = self.rtde.joint_torques()
        logger.receive(f"Received response: {torques}")
        return torques

    def get_cartesian_position(self) -> list[float]:
        """Return actual TCP pose [x, y, z, rx, ry, rz] in metres and radians."""
        pose = self.rtde.tcp_pose()
        logger.receive(f"Received response: {pose}")
        return pose

    def get_tcp_speed(self) -> list[float]:
        """Return actual TCP speed [vx, vy, vz, wx, wy, wz] in m/s and rad/s."""
        speed = self.rtde.tcp_speed()
        logger.receive(f"Received response: {speed}")
        return speed

    def get_tcp_forces(self) -> list[float]:
        """Return TCP force [Fx, Fy, Fz, Tx, Ty, Tz] in Newton and Newton-metres."""
        forces = self.rtde.tcp_force()
        logger.receive(f"Received response: {forces}")
        return forces

    def get_target_joint_positions(self) -> list[float]:
        """Return target joint positions in radians."""
        target = self.rtde.target_joint_positions()
        logger.receive(f"Received response: {target}")
        return target

    def get_target_joint_velocities(self) -> list[float]:
        """Return target joint velocities in rad/s."""
        target = self.rtde.target_joint_velocities()
        logger.receive(f"Received response: {target}")
        return target

    def get_target_tcp_pose(self) -> list[float]:
        """Return target TCP pose [x, y, z, rx, ry, rz] in metres and radians."""
        target = self.rtde.target_tcp_pose()
        logger.receive(f"Received response: {target}")
        return target

    def get_target_tcp_speed(self) -> list[float]:
        """Return target TCP speed [vx, vy, vz, wx, wy, wz] in m/s and rad/s."""
        target = self.rtde.target_tcp_speed()
        logger.receive(f"Received response: {target}")
        return target

    def get_robot_state(self) -> dict[str, bool]:
        """Return robot and safety status bit fields."""
        status = self.rtde.robot_status()
        key_out = [
            "Power On",
            "Program Running",
            "Emergency Stopped",
            "Stopped Due to Safety",
        ]
        logger.receive(
            "Received response: "
            + ", ".join(f"{k}: {status[k]}" for k in key_out)
            + " ..."
        )
        return status

    def get_robot_mode(self) -> RobotMode:
        """Return robot mode as a RobotMode enum."""
        mode = self.rtde.robot_mode()
        logger.receive(f"Received response: {mode}")
        return mode

    def get_safety_mode(self) -> SafetyMode:
        """Return safety mode as a SafetyMode enum."""
        mode = self.rtde.safety_mode()
        logger.receive(f"Received response: {mode}")
        return mode

    def get_runtime_state(self) -> RuntimeState:
        """Return runtime state as a RuntimeState enum."""
        state = self.rtde.runtime_state()
        logger.receive(f"Received response: {state}")
        return state

    def get_speed_scaling(self) -> float:
        """Return current speed scaling factor in [0, 1]."""
        scaling = self.rtde.speed_scaling()
        logger.receive(f"Received response: {scaling}")
        return scaling

    def get_payload(self) -> dict:
        """Return payload mass (kg) and centre of gravity (m)."""
        payload = self.rtde.payload()
        logger.receive(f"Received response: {payload}")
        return payload

    def is_moving(self) -> bool:
        """Return True if the robot is currently in motion."""
        return self.rtde.is_moving()

    def get_analog_inputs(self) -> dict[str, float]:
        """Return standard and tool analog input values."""
        inputs = self.rtde.analog_inputs()
        logger.receive(f"Received response: {inputs}")
        return inputs

    def get_analog_outputs(self) -> dict[str, float]:
        """Return standard analog output values."""
        outputs = self.rtde.analog_outputs()
        logger.receive(f"Received response: {outputs}")
        return outputs

    def get_digital_inputs(self) -> dict[str, bool]:
        """Return digital input states (standard, configurable, tool)."""
        inputs = self.rtde.digital_inputs()
        logger.receive(f"Received response: {inputs}")
        return inputs

    def get_digital_outputs(self) -> dict[str, bool]:
        """Return digital output states (standard, configurable, tool)."""
        outputs = self.rtde.digital_outputs()
        logger.receive(f"Received response: {outputs}")
        return outputs

    def get_tool_io(self) -> dict:
        """Return tool I/O state (analog inputs, voltage, current, temperature)."""
        tool = self.rtde.tool_io()
        logger.receive(f"Received response: {tool}")
        return tool

    def set_speed_slider(self, fraction: float) -> None:
        """Set speed override slider fraction in [0.0, 1.0]."""
        logger.send(f"Setting speed slider: {fraction}")
        self.rtde.set_speed_slider(fraction)

    def set_digital_output(self, pin: int, value: bool) -> None:
        """Set a standard digital output pin (0-7) high or low."""
        logger.send(f"Setting digital output DO{pin} = {value}")
        self.rtde.set_digital_output(pin, value)

    def set_analog_output(self, channel: int, value: float) -> None:
        """Set standard analog output voltage on channel 0 or 1."""
        logger.send(f"Setting analog output AO{channel} = {value}V")
        self.rtde.set_analog_output(channel, value)
