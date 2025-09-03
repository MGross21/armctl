from __future__ import annotations

from pathlib import Path
from typing import NewType

import rtde.rtde as rtde
import rtde.rtde_config as rtde_config

UINT32 = NewType("UINT32", int)


class RTDE:
    def __init__(self, ip: str):
        config_file = Path(__file__).parent / "config.xml"
        config = rtde_config.ConfigFile(str(config_file))
        state_names, state_types = config.get_recipe("out")

        self.c = rtde.RTDE(ip)
        self.c.connect()
        self.c.send_output_setup(state_names, state_types)
        self.c.get_controller_version()
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
        rsb: UINT32 = data.robot_status_bits
        ssb: UINT32 = data.safety_status_bits

        return {
            # Robot status bits
            "Power On": bool(rsb & 1),
            "Program Running": bool(rsb & 2),
            "Teach Button": bool(rsb & 4),
            "Power Button": bool(rsb & 8),
            # Safety status bits
            "Normal Mode": bool(ssb & 1),
            "Reduced Mode": bool(ssb & 2),
            "Protective Stop": bool(ssb & 4),
            "Recovery Mode": bool(ssb & 8),
            "Safeguard Stopped": bool(ssb & 16),
            "System Emergency Stopped": bool(ssb & 32),
            "Robot Emergency Stopped": bool(ssb & 64),
            "Emergency Stopped": bool(ssb & 128),
            "Violation": bool(ssb & 256),
            "Fault": bool(ssb & 512),
            "Stopped Due to Safety": bool(ssb & 1024),
        }
