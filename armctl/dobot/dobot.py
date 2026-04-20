"""
Dobot manufacturer base class and shared error/state tables.

All public methods use SI units: positions in radians, translations in meters.

Sources
-------
Magician binary protocol:
  https://www.littlechip.co.nz/blog/communicating-with-the-dobot-magician-using-raw-protocol
  https://download.dobot.cc/development-protocol/dobot-magician/pdf/en/Dobot-Magician-API-Description-V1.2.2.pdf
  https://wiki.idiot.io/_media/dobot-magician-user-guide-v1.7.0.pdf
M1 Pro TCP/IP:
  https://download.dobot.cc/2024/04/TCP_IP%20Remote%20Control%20Interface%20Guide%20%284axis%29_20240419_en.pdf
"""

from __future__ import annotations

from armctl.templates import Commands, Properties


class Codes:
    """M1 Pro TCP/IP error and robot-state code tables."""

    COMMAND: dict[int, str] = {
        0: "No error: delivered successfully",
        5: "Robot in motion (immediate execution)",
        7: "Robot in motion (queued)",
        -1: "Failed to receive or execute",
        -10000: "Command does not exist",
        -20000: "Incorrect number of command parameters",
        -30001: "Parameter 1 type incorrect",
        -30002: "Parameter 2 type incorrect",
        -30003: "Parameter 3 type incorrect",
        -30004: "Parameter 4 type incorrect",
        -40001: "Parameter 1 out of range",
        -40002: "Parameter 2 out of range",
        -40003: "Parameter 3 out of range",
        -40004: "Parameter 4 out of range",
    }

    STATE: dict[int, str] = {
        1: "ROBOT_MODE_INIT – initialized",
        2: "ROBOT_MODE_BRAKE_OPEN – brake open",
        3: "ROBOT_MODE_POWER_STATUS – powered off",
        4: "ROBOT_MODE_DISABLED – disabled",
        5: "ROBOT_MODE_ENABLE – enabled and idle",
        6: "ROBOT_MODE_BACKDRIVE – drag mode",
        7: "ROBOT_MODE_RUNNING – executing motion",
        8: "ROBOT_MODE_RECORDING – trajectory recording",
        9: "ROBOT_MODE_ERROR – uncleared alarms",
        10: "ROBOT_MODE_PAUSE – paused",
        11: "ROBOT_MODE_JOG – jogging",
    }

    @classmethod
    def get_cmd_message(cls, code: int) -> str:
        return cls.COMMAND.get(code, f"Unknown command code: {code}")

    @classmethod
    def get_state_message(cls, code: int) -> str:
        return cls.STATE.get(code, f"Unknown state code: {code}")


class Dobot(Commands, Properties):
    """Dobot manufacturer base class."""
