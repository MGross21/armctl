from __future__ import annotations

from pathlib import Path
from typing import NewType

from rtde import RTDE as _RTDE
from rtde.rtde_config import ConfigFile
from ctypes import c_uint32

u32 = NewType("u32", c_uint32)


class RTDE:
    def __init__(self, ip: str):
        config_file = Path(__file__).parent / "config.xml"
        config = ConfigFile(str(config_file))
        state_names, state_types = config.get_recipe("out")

        self.c = _RTDE(ip)
        self.c.connect()
        self.c.send_output_setup(state_names, state_types)
        self.controller_version = (
            self.c.get_controller_version()
        )  # (MAJOR, MINOR, BUGFIX, BUILD)
        self.c.send_start()

    def _get_data(self):
        if not self.c.is_connected():
            raise ConnectionError("RTDE connection has been lost.")
        return self.c.receive()

    def joint_angles(self) -> list[float]:
        """Return joint angles in radians."""
        return list(self._get_data().actual_q)

    def tcp_pose(self) -> list[float]:
        """Return TCP pose [x, y, z, rx, ry, rz]."""
        return list(self._get_data().actual_TCP_pose)

    def joint_torques(self) -> list[float]:
        """Return joint torques in Nm converted from current."""
        # See: https://www.universal-robots.com/articles/ur/release-notes/release-note-software-version-523x/
        if self.controller_version >= (5, 23, 0, 0):
            return list(self._get_data().actual_current_as_torque)
        else:
            raise NotImplementedError(
                "Joint torques not available for controller versions below 5.23.0.0"
            )

    def tcp_force(self) -> list[float]:
        """Return TCP force [Fx, Fy, Fz, Tx, Ty, Tz] in Newton and Newton-meters."""
        return list(self._get_data().actual_TCP_force)

    def robot_status(self) -> dict[str, bool]:
        """Return robot status.

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
        rsb: u32 = data.robot_status_bits
        ssb: u32 = data.safety_status_bits

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
