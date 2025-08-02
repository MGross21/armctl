from pathlib import Path
import rtde.rtde as rtde
import rtde.rtde_config as rtde_config

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
