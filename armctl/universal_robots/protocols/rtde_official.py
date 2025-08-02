from pathlib import Path

import rtde.rtde as rtde
import rtde.rtde_config as rtde_config

# Documentation: https://docs.universal-robots.com/tutorials/communication-protocol-tutorials/rtde-python-client-guide.html


class RTDE:
    def __init__(self, ip: str):
        self.config_file = Path(__file__).parent / "config.xml"
        self.config = rtde_config.ConfigFile(str(self.config_file))

        state_names, state_types = self.config.get_recipe("out")

        self.c = rtde.RTDE(ip)  # Initialize RTDE connection
        self.c.connect()  # Documentation says should return boolean. Code returns none

        self.c.send_output_setup(state_names, state_types)

        # Software version of the controller
        _v = self.c.get_controller_version()
        version_str = ".".join(str(part) for part in _v[:3])

        self.c.send_start()

        # TODO: Add assertion check to ensure xml is setup with minimums (joint and TCP pose)
        # Can use RTDE functions or xml parsing to check this

    def _get_data(self):
        if not self.c.is_connected():
            raise ConnectionError("RTDE connection has been lost.")

        return self.c.receive()

    def joint_angles(self) -> list[float]:
        """
        Extract joint angles from the RTDE data.

        Returns
        -------
        list of float
            The joint angles in radians.
        """

        data = self._get_data()
        return list(data.actual_q)

    def tcp_pose(self) -> list[float]:
        """
        Extract TCP pose from the RTDE data.

        Returns
        -------
        list of float
            The TCP pose in the format [x, y, z, rx, ry, rz].
        """
        data = self._get_data()
        return list(data.actual_TCP_pose)
