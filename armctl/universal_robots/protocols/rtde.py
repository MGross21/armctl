from __future__ import annotations

import time

from .codes import RobotMode, RuntimeState, SafetyMode
from .rtde_core import RTDE as _RTDE


_MOVING_VELOCITY_THRESHOLD = 1e-3  # rad/s — below this on all joints = stopped


class RTDE:
    def __init__(self, ip: str):
        self.c = _RTDE(ip)
        self.c.connect()
        self.c.send_output_setup()
        self._input = self.c.send_input_setup()
        self.controller_version = self.c.get_controller_version()
        self.c.send_start()

    def _get_data(self):
        if not self.c.is_connected():
            raise ConnectionError("RTDE connection has been lost.")
        return self.c.receive()

    def joint_angles(self) -> list[float]:
        """Return actual joint angles in radians."""
        return list(self._get_data().actual_q)

    def joint_velocities(self) -> list[float]:
        """Return actual joint velocities in rad/s."""
        return list(self._get_data().actual_qd)

    def joint_currents(self) -> list[float]:
        """Return actual joint currents in Amperes."""
        return list(self._get_data().actual_current)

    def joint_torques(self) -> list[float]:
        """Return joint torques in Nm converted from current.

        Requires controller >= 5.23.0.0.
        See: https://www.universal-robots.com/articles/ur/release-notes/release-note-software-version-523x/
        """
        if self.controller_version >= (5, 23, 0, 0):
            return list(self._get_data().actual_current_as_torque)
        raise NotImplementedError(
            "Joint torques not available for controller versions below 5.23.0.0"
        )

    def tcp_pose(self) -> list[float]:
        """Return actual TCP pose [x, y, z, rx, ry, rz] in metres and radians."""
        return list(self._get_data().actual_TCP_pose)

    def tcp_speed(self) -> list[float]:
        """Return actual TCP speed [vx, vy, vz, wx, wy, wz] in m/s and rad/s."""
        return list(self._get_data().actual_TCP_speed)

    def tcp_force(self) -> list[float]:
        """Return TCP force [Fx, Fy, Fz, Tx, Ty, Tz] in Newton and Newton-metres."""
        return list(self._get_data().actual_TCP_force)

    def target_joint_positions(self) -> list[float]:
        """Return target joint positions in radians."""
        return list(self._get_data().target_q)

    def target_joint_velocities(self) -> list[float]:
        """Return target joint velocities in rad/s."""
        return list(self._get_data().target_qd)

    def target_tcp_pose(self) -> list[float]:
        """Return target TCP pose [x, y, z, rx, ry, rz] in metres and radians."""
        return list(self._get_data().target_TCP_pose)

    def target_tcp_speed(self) -> list[float]:
        """Return target TCP speed [vx, vy, vz, wx, wy, wz] in m/s and rad/s."""
        return list(self._get_data().target_TCP_speed)

    def robot_mode(self) -> RobotMode:
        """Return robot mode as a RobotMode enum."""
        return RobotMode(self._get_data().robot_mode)

    def safety_mode(self) -> SafetyMode:
        """Return safety mode as a SafetyMode enum."""
        return SafetyMode(self._get_data().safety_mode)

    def runtime_state(self) -> RuntimeState:
        """Return runtime state as a RuntimeState enum."""
        return RuntimeState(self._get_data().runtime_state)

    def robot_status(self) -> dict[str, bool]:
        """Return robot and safety status bit fields.

        Robot status bits (UINT32):
        - **`Bit 0`**: Is power on
        - **`Bit 1`**: Is program running
        - **`Bit 2`**: Is teach button pressed
        - **`Bit 3`**: Is power button pressed

        Safety status bits (UINT32):
        - **`Bit 0`**: Is normal mode
        - **`Bit 1`**: Is reduced mode
        - **`Bit 2`**: Is protective stop
        - **`Bit 3`**: Is recovery mode
        - **`Bit 4`**: Is safeguard stopped
        - **`Bit 5`**: Is system emergency stopped
        - **`Bit 6`**: Is robot emergency stopped
        - **`Bit 7`**: Is Emergency Stopped
        - **`Bit 8`**: Is violation
        - **`Bit 9`**: Is Fault
        - **`Bit 10`**: Is stopped due to safety
        """
        data = self._get_data()
        rsb = data.robot_status_bits
        ssb = data.safety_status_bits

        bit = lambda data, n: bool(data & (1 << n))

        return {
            # Robot status bits
            "Power On": bit(rsb, 0),
            "Program Running": bit(rsb, 1),
            "Teach Button": bit(rsb, 2),
            "Power Button": bit(rsb, 3),
            # Safety status bits
            "Normal Mode": bit(ssb, 0),
            "Reduced Mode": bit(ssb, 1),
            "Protective Stop": bit(ssb, 2),
            "Recovery Mode": bit(ssb, 3),
            "Safeguard Stopped": bit(ssb, 4),
            "System Emergency Stopped": bit(ssb, 5),
            "Robot Emergency Stopped": bit(ssb, 6),
            "Emergency Stopped": bit(ssb, 7),
            "Violation": bit(ssb, 8),
            "Fault": bit(ssb, 9),
            "Stopped Due to Safety": bit(ssb, 10),
        }

    def speed_scaling(self) -> float:
        """Return current speed scaling factor in [0, 1]."""
        return float(self._get_data().speed_scaling)

    def payload(self) -> dict:
        """Return payload mass (kg) and centre of gravity (m)."""
        data = self._get_data()
        return {
            "mass_kg": float(data.payload),
            "cog": list(data.payload_cog),
        }

    def analog_inputs(self) -> dict[str, float]:
        """Return standard and tool analog input values (V or mA)."""
        data = self._get_data()
        return {
            "standard_0": float(data.standard_analog_input0),
            "standard_1": float(data.standard_analog_input1),
            "tool_0": float(data.tool_analog_input0),
            "tool_1": float(data.tool_analog_input1),
        }

    def analog_outputs(self) -> dict[str, float]:
        """Return standard analog output values (V or mA)."""
        data = self._get_data()
        return {
            "standard_0": float(data.standard_analog_output0),
            "standard_1": float(data.standard_analog_output1),
        }

    def digital_inputs(self) -> dict[str, bool]:
        """Return digital input states.

        Bits 0-7:   Standard DI 0-7
        Bits 8-15:  Configurable DI 0-7
        Bits 16-17: Tool DI 0-1
        """
        bits = self._get_data().standard_digital_input_bits
        bit = lambda n: bool(bits & (1 << n))
        return {
            **{f"DI{i}": bit(i) for i in range(8)},
            **{f"CDI{i}": bit(i + 8) for i in range(8)},
            "Tool_DI0": bit(16),
            "Tool_DI1": bit(17),
        }

    def digital_outputs(self) -> dict[str, bool]:
        """Return digital output states.

        Bits 0-7:   Standard DO 0-7
        Bits 8-15:  Configurable DO 0-7
        Bits 16-17: Tool DO 0-1
        """
        bits = self._get_data().standard_digital_output_bits
        bit = lambda n: bool(bits & (1 << n))
        return {
            **{f"DO{i}": bit(i) for i in range(8)},
            **{f"CDO{i}": bit(i + 8) for i in range(8)},
            "Tool_DO0": bit(16),
            "Tool_DO1": bit(17),
        }

    def tool_io(self) -> dict:
        """Return tool I/O state."""
        data = self._get_data()
        return {
            "analog_input_0": float(data.tool_analog_input0),
            "analog_input_1": float(data.tool_analog_input1),
            "output_voltage": int(data.tool_output_voltage),
            "output_current": float(data.tool_output_current),
            "temperature": float(data.tool_temperature),
        }

    def is_moving(self, threshold: float = _MOVING_VELOCITY_THRESHOLD) -> bool:
        """Return True if any joint velocity exceeds threshold (rad/s)."""
        return any(abs(v) > threshold for v in self._get_data().actual_qd)

    def wait_until_stopped(
        self, timeout: float = 120.0, poll_interval: float = 0.05
    ) -> None:
        """Block until all joints are stopped or timeout expires.

        Waits for motion to begin, then polls joint velocities via RTDE
        until all fall below _MOVING_VELOCITY_THRESHOLD.

        Parameters
        ----------
        timeout : float
            Maximum seconds to wait after motion starts.
        poll_interval : float
            RTDE poll interval in seconds.

        Raises
        ------
        TimeoutError
            If the robot does not stop within timeout.
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._get_data().output_int_registers_0 == 1:
                return
            time.sleep(poll_interval)
        raise TimeoutError(f"Robot did not stop within {timeout}s")

    def set_speed_slider(self, fraction: float) -> None:
        """Set speed override slider fraction in [0.0, 1.0]."""
        if not 0.0 <= fraction <= 1.0:
            raise ValueError(
                f"Speed fraction must be in [0, 1], got {fraction}"
            )
        self._input.speed_slider_mask = 1
        self._input.speed_slider_fraction = fraction
        self.c.send(self._input)

    def set_digital_output(self, pin: int, value: bool) -> None:
        """Set a standard digital output pin (0-7) high or low."""
        if not 0 <= pin <= 7:
            raise ValueError(f"Digital output pin must be 0-7, got {pin}")
        mask = 1 << pin
        self._input.standard_digital_output_mask = mask
        self._input.standard_digital_output = mask if value else 0
        self.c.send(self._input)

    def set_analog_output(self, channel: int, value: float) -> None:
        """Set standard analog output voltage (channel 0 or 1).

        Parameters
        ----------
        channel : int
            Output channel — 0 or 1.
        value : float
            Output value in Volts [0, 10] (voltage mode).
        """
        if channel not in (0, 1):
            raise ValueError(
                f"Analog output channel must be 0 or 1, got {channel}"
            )
        self._input.standard_analog_output_mask = 1 << channel
        self._input.standard_analog_output_type = 0  # 0 = voltage mode
        if channel == 0:
            self._input.standard_analog_output_0 = value
        else:
            self._input.standard_analog_output_1 = value
        self.c.send(self._input)
