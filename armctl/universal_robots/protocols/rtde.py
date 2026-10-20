from __future__ import annotations

import time

from .codes import RobotMode, RuntimeState, SafetyMode
from .config import (
    AnalogOutputInput,
    DigitalOutputInput,
    OutputData,
    Recipe,
    SpeedSliderInput,
    TorqueOutputData,
)
from .rtde_core import RTDEClient


class RTDE:
    def __init__(self, ip: str):
        self._client = RTDEClient(ip)
        self._client.connect()
        # (MAJOR, MINOR, BUGFIX, BUILD)
        self.controller_version = self._client.get_controller_version()
        self._client.send_output_setup(
            TorqueOutputData if self.controller_version >= (5, 23, 0, 0) else OutputData
        )
        self._input_ids = {
            recipe: self._client.send_input_setup(recipe)
            for recipe in (SpeedSliderInput, DigitalOutputInput, AnalogOutputInput)
        }
        self._client.send_start()

    def disconnect(self) -> None:
        self._client.disconnect()

    def _get_data(self):
        return self._client.receive()

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

        def bit(data, n):
            return bool(data & (1 << n))

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
        bits = self._get_data().actual_digital_input_bits

        def bit(n):
            return bool(bits & (1 << n))

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
        bits = self._get_data().actual_digital_output_bits

        def bit(n):
            return bool(bits & (1 << n))

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

    def is_moving(self, threshold: float = 1e-3) -> bool:
        """Return True if any joint velocity exceeds threshold (rad/s)."""
        return any(abs(v) > threshold for v in self._get_data().actual_qd)

    def get_last_move_seqno(self) -> int:
        """Return the sequence number of the last completed move program."""
        return self._get_data().output_int_register_0

    def wait_for_move(
        self, seqno: int, timeout: float = 120.0, poll_interval: float = 0.05
    ) -> None:
        """Block until the move program writes seqno to output int register 0.

        Parameters
        ----------
        seqno : int
            Sequence number written by the move program on completion.
        timeout : float
            Maximum seconds to wait.
        poll_interval : float
            RTDE poll interval in seconds.

        Raises
        ------
        TimeoutError
            If the move does not finish within timeout.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.get_last_move_seqno() == seqno:
                return
            time.sleep(poll_interval)
        raise TimeoutError(f"Move {seqno} did not finish within {timeout}s")

    def set_speed_slider(self, fraction: float) -> None:
        """Set speed override slider fraction in [0.0, 1.0]."""
        if not 0.0 <= fraction <= 1.0:
            raise ValueError(f"Speed fraction must be in [0, 1], got {fraction}")
        self._send(SpeedSliderInput, speed_slider_mask=1, speed_slider_fraction=fraction)

    def set_digital_output(self, pin: int, value: bool) -> None:
        """Set a standard digital output pin (0-7) high or low."""
        if not 0 <= pin <= 7:
            raise ValueError(f"Digital output pin must be 0-7, got {pin}")
        mask = 1 << pin
        self._send(
            DigitalOutputInput,
            standard_digital_output_mask=mask,
            standard_digital_output=mask if value else 0,
        )

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
            raise ValueError(f"Analog output channel must be 0 or 1, got {channel}")
        if not 0.0 <= value <= 10.0:
            raise ValueError(f"Analog output voltage must be in [0, 10], got {value}")
        self._send(
            AnalogOutputInput,
            standard_analog_output_mask=1 << channel,
            standard_analog_output_type=1 << channel,  # set bit = voltage mode
            **{f"standard_analog_output_{channel}": value / 10.0},  # 0..1 ratio
        )

    def _send(self, recipe: type[Recipe], **fields: float) -> None:
        recipe_id = self._input_ids[recipe]
        if recipe_id is None:
            raise RuntimeError(f"RTDE {recipe.__name__} fields are in use by another client")
        self._client.send(recipe(recipe_id=recipe_id, **fields))
