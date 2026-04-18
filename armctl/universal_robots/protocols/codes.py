from __future__ import annotations

from enum import IntEnum


class RobotMode(IntEnum):
    NO_CONTROLLER = -1
    DISCONNECTED = 0
    CONFIRM_SAFETY = 1
    BOOTING = 2
    POWER_OFF = 3
    POWER_ON = 4
    IDLE = 5
    BACKDRIVE = 6
    RUNNING = 7
    UPDATING_FIRMWARE = 8


class SafetyMode(IntEnum):
    NORMAL = 1
    REDUCED = 2
    PROTECTIVE_STOP = 3
    RECOVERY = 4
    SAFEGUARD_STOP = 5
    SYSTEM_EMERGENCY_STOP = 6
    ROBOT_EMERGENCY_STOP = 7
    VIOLATION = 8
    FAULT = 9


class RuntimeState(IntEnum):
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2
    PAUSING = 3
    RESUMING = 4
