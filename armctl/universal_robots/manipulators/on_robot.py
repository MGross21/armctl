from __future__ import annotations

import warnings

from armctl.templates import SocketController as SCT


class OnRobot(SCT):
    def __init__(
        self, ip: str = "192.168.1.111", port: int | tuple[int, int] = 30_002
    ):
        super().__init__(ip, port)
        raise NotImplementedError("OnRobot gripper is not yet supported.")

    def connect(self):
        super().connect()
        self.send_command(
            "rg2_activate()\n", suppress_output=True
        )  # activate Gripper
        # self.send_command("write_register(1000, 0x0100, unit=9)\n") # activate Gripper

    def disconnect(self):
        super().disconnect()

    def set_position(
        self, position: float, name: str = "rg2", force: float = 10
    ) -> None:
        """Set the analog position of the gripper (0-255)."""
        if position < 0 or position > 255:
            raise ValueError("Position must be between 0 and 255.")

        max_range = 140
        position = int(
            (position / 255) * max_range
        )  # Relinearize the position to the internal range of the gripper

        if force < 0 or force > 255:
            raise ValueError("Force must be between 0 and 255.")

        max_force = 255
        force = int(
            (force / 255) * max_force
        )  # Linearize the force to the range 0-max_force

        valid_grippers = ["rg2", "rg6", "vgc10"]
        if name not in valid_grippers:
            raise ValueError(
                f"Gripper name must be one of {','.join(valid_grippers)}."
            )

        if isinstance(position, float):
            position = int(position)
            warnings.warn(
                f"Position converted to int: {position}", UserWarning, 2
            )

        self.send_command(f"{name}_set_force({force})\n", suppress_output=True)
        self.send_command(
            f"{name}_set_width({position})\n", suppress_output=True
        )

    def get_position(self, name: str = "rg2") -> float:
        """Get the current position of the gripper."""
        response = self.send_command(
            f"{name}_get_width()\n", suppress_output=True, raw_response=True
        )
        return float(response.strip())

    def get_status(self) -> bool:
        """Get the current status of the gripper."""
        response = self.send_command(
            "rg2_get_status()\n", suppress_output=True, raw_response=True
        )
        return (
            response.strip() == "1"
        )  # 1 means gripper is closed, 0 means open

    def open(self, force: float = 20) -> None:
        self.send_command("rg2_open()\n", suppress_output=True)
        self.set_position(255, force=force)

    def close(self) -> None:
        self.send_command("rg2_close()\n", suppress_output=True)
