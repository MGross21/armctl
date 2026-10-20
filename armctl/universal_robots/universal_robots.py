from __future__ import annotations

import ctypes
import math
import time as _time

from typing_extensions import override

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
        self._seqno = ctypes.c_int32()

    @override
    def connect(self):
        super().connect()
        self.rtde = RTDE(self.ip)
        self._seqno.value = self.rtde.get_last_move_seqno()

    @override
    def disconnect(self):
        try:
            self.stop_motion()
        except Exception:
            pass
        if self.rtde is not None:
            self.rtde.disconnect()
            self.rtde = None
        super().disconnect()

    @property
    def _rtde(self) -> RTDE:
        if self.rtde is None:
            raise ConnectionError("Robot is not connected.")
        return self.rtde

    @override
    def sleep(self, seconds: float) -> None:
        cc.sleep(seconds)
        self.send_command(f"sleep({seconds})\n")
        _time.sleep(seconds)  # block Python side while controller sleeps

    @override
    def move_joints(
        self,
        pos: list[float],
        speed: float = 0.1,
        acceleration: float = 0.05,
        t: float = 0.0,
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
        """
        cc.move_joints(self, pos, speed, acceleration)
        joints = ",".join(map(str, pos))
        self._run_move(f"movej([{joints}], a={acceleration}, v={speed}, t={t})", t)

    @override
    def move_cartesian(
        self,
        pose: list[float],
        move_type: str = "movel",
        speed: float = 0.1,
        acceleration: float = 0.1,
        time: float = 0.0,
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
        """
        if move_type not in {"movel", "movep", "movej"}:
            raise ValueError("Unsupported move type. Use 'movel', 'movep', or 'movej'.")

        cc.move_cartesian(self, pose)

        duration = "" if move_type == "movep" else f", t={time}"
        target = ",".join(map(str, pose))
        self._run_move(f"{move_type}(p[{target}], a={acceleration}, v={speed}{duration})", time)

    def _run_move(self, motion: str, duration: float) -> None:
        """Run ``motion`` as one program and block until done."""
        self._seqno.value += 1
        seqno = self._seqno.value
        program = f"def armctl_move():\n{motion}\nwrite_output_integer_register(0,{seqno})\nend\n"
        self.send_command(program, timeout=duration + 10, suppress_output=True)
        timeout = (duration + 15.0) if duration > 0 else 120.0
        self._rtde.wait_for_move(seqno, timeout=timeout)

    @override
    def stop_motion(self) -> None:
        deceleration = 2.0  # rad/s^2
        self.send_command(f"stopj({deceleration})\n", suppress_output=True)

    @override
    def get_joint_positions(self) -> list[float]:
        """Return actual joint positions in radians."""
        angles = self._rtde.joint_angles()
        logger.receive(f"Received response: {angles}")
        return angles

    def get_joint_velocities(self) -> list[float]:
        """Return actual joint velocities in rad/s."""
        vels = self._rtde.joint_velocities()
        logger.receive(f"Received response: {vels}")
        return vels

    def get_joint_currents(self) -> list[float]:
        """Return actual joint currents in Amperes."""
        currents = self._rtde.joint_currents()
        logger.receive(f"Received response: {currents}")
        return currents

    def get_joint_torques(self) -> list[float]:
        """Return joint torques in Nm. Requires controller >= 5.23.0.0."""
        torques = self._rtde.joint_torques()
        logger.receive(f"Received response: {torques}")
        return torques

    @override
    def get_cartesian_position(self) -> list[float]:
        """Return actual TCP pose [x, y, z, rx, ry, rz] in metres and radians."""
        pose = self._rtde.tcp_pose()
        logger.receive(f"Received response: {pose}")
        return pose

    def get_tcp_speed(self) -> list[float]:
        """Return actual TCP speed [vx, vy, vz, wx, wy, wz] in m/s and rad/s."""
        speed = self._rtde.tcp_speed()
        logger.receive(f"Received response: {speed}")
        return speed

    def get_tcp_forces(self) -> list[float]:
        """Return TCP force [Fx, Fy, Fz, Tx, Ty, Tz] in Newton and Newton-metres."""
        forces = self._rtde.tcp_force()
        logger.receive(f"Received response: {forces}")
        return forces

    def get_target_joint_positions(self) -> list[float]:
        """Return target joint positions in radians."""
        target = self._rtde.target_joint_positions()
        logger.receive(f"Received response: {target}")
        return target

    def get_target_joint_velocities(self) -> list[float]:
        """Return target joint velocities in rad/s."""
        target = self._rtde.target_joint_velocities()
        logger.receive(f"Received response: {target}")
        return target

    def get_target_tcp_pose(self) -> list[float]:
        """Return target TCP pose [x, y, z, rx, ry, rz] in metres and radians."""
        target = self._rtde.target_tcp_pose()
        logger.receive(f"Received response: {target}")
        return target

    def get_target_tcp_speed(self) -> list[float]:
        """Return target TCP speed [vx, vy, vz, wx, wy, wz] in m/s and rad/s."""
        target = self._rtde.target_tcp_speed()
        logger.receive(f"Received response: {target}")
        return target

    @override
    def get_robot_state(self) -> dict[str, bool]:
        """Return robot and safety status bit fields."""
        status = self._rtde.robot_status()
        key_out = [
            "Power On",
            "Program Running",
            "Emergency Stopped",
            "Stopped Due to Safety",
        ]
        logger.receive(
            "Received response: " + ", ".join(f"{k}: {status[k]}" for k in key_out) + " ..."
        )
        return status

    def get_robot_mode(self) -> RobotMode:
        """Return robot mode as a RobotMode enum."""
        mode = self._rtde.robot_mode()
        logger.receive(f"Received response: {mode}")
        return mode

    def get_safety_mode(self) -> SafetyMode:
        """Return safety mode as a SafetyMode enum."""
        mode = self._rtde.safety_mode()
        logger.receive(f"Received response: {mode}")
        return mode

    def get_runtime_state(self) -> RuntimeState:
        """Return runtime state as a RuntimeState enum."""
        state = self._rtde.runtime_state()
        logger.receive(f"Received response: {state}")
        return state

    def get_speed_scaling(self) -> float:
        """Return current speed scaling factor in [0, 1]."""
        scaling = self._rtde.speed_scaling()
        logger.receive(f"Received response: {scaling}")
        return scaling

    def get_payload(self) -> dict:
        """Return payload mass (kg) and centre of gravity (m)."""
        payload = self._rtde.payload()
        logger.receive(f"Received response: {payload}")
        return payload

    def is_moving(self) -> bool:
        """Return True if the robot is currently in motion."""
        return self._rtde.is_moving()

    def get_analog_inputs(self) -> dict[str, float]:
        """Return standard and tool analog input values."""
        inputs = self._rtde.analog_inputs()
        logger.receive(f"Received response: {inputs}")
        return inputs

    def get_analog_outputs(self) -> dict[str, float]:
        """Return standard analog output values."""
        outputs = self._rtde.analog_outputs()
        logger.receive(f"Received response: {outputs}")
        return outputs

    def get_digital_inputs(self) -> dict[str, bool]:
        """Return digital input states (standard, configurable, tool)."""
        inputs = self._rtde.digital_inputs()
        logger.receive(f"Received response: {inputs}")
        return inputs

    def get_digital_outputs(self) -> dict[str, bool]:
        """Return digital output states (standard, configurable, tool)."""
        outputs = self._rtde.digital_outputs()
        logger.receive(f"Received response: {outputs}")
        return outputs

    def get_tool_io(self) -> dict:
        """Return tool I/O state (analog inputs, voltage, current, temperature)."""
        tool = self._rtde.tool_io()
        logger.receive(f"Received response: {tool}")
        return tool

    def set_speed_slider(self, fraction: float) -> None:
        """Set speed override slider fraction in [0.0, 1.0]."""
        logger.send(f"Setting speed slider: {fraction}")
        self._rtde.set_speed_slider(fraction)

    def set_digital_output(self, pin: int, value: bool) -> None:
        """Set a standard digital output pin (0-7) high or low."""
        logger.send(f"Setting digital output DO{pin} = {value}")
        self._rtde.set_digital_output(pin, value)

    def set_analog_output(self, channel: int, value: float) -> None:
        """Set standard analog output voltage on channel 0 or 1."""
        logger.send(f"Setting analog output AO{channel} = {value}V")
        self._rtde.set_analog_output(channel, value)
