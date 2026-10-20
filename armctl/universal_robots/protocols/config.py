from __future__ import annotations

import ctypes
from enum import Enum


class RTDEType(Enum):
    BOOL = ctypes.c_bool
    UINT8 = ctypes.c_uint8
    UINT32 = ctypes.c_uint32
    UINT64 = ctypes.c_uint64
    INT32 = ctypes.c_int32
    DOUBLE = ctypes.c_double
    VECTOR3D = ctypes.c_double * 3
    VECTOR6D = ctypes.c_double * 6
    VECTOR6INT32 = ctypes.c_int32 * 6
    VECTOR6UINT32 = ctypes.c_uint32 * 6


class Recipe(ctypes.BigEndianStructure):
    """RTDE data package: recipe id followed by the recipe's fields in order."""

    _pack_ = 1
    _layout_ = "ms"
    _fields_ = [("recipe_id", ctypes.c_uint8)]
    names: tuple[str, ...] = ()
    rtde_types: tuple[str, ...] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        own = cls.__dict__.get("_fields_", ())
        cls.names = (*cls.names, *(name for name, _ in own))
        cls.rtde_types = (*cls.rtde_types, *(RTDEType(ctype).name for _, ctype in own))

    def __init__(self, **values):
        unknown = values.keys() - {"recipe_id", *self.names}
        if unknown:
            raise TypeError(f"{type(self).__name__} has no fields {sorted(unknown)}")
        super().__init__(**values)

    @classmethod
    def parse_setup(cls, payload: bytes) -> int | None:
        """Return the recipe id from a setup reply; None if any field is IN_USE."""
        types = tuple(payload[1:].decode().split(","))
        if "IN_USE" in types:
            return None
        if types != cls.rtde_types:
            bad = [f"{n}: {a}" for n, e, a in zip(cls.names, cls.rtde_types, types) if a != e]
            raise RuntimeError(f"RTDE {cls.__name__} mismatch (name: controller type): {bad}")
        return payload[0]


class OutputData(Recipe):
    _fields_ = [
        ("actual_q", ctypes.c_double * 6),
        ("actual_qd", ctypes.c_double * 6),
        ("actual_current", ctypes.c_double * 6),
        ("actual_TCP_pose", ctypes.c_double * 6),
        ("actual_TCP_speed", ctypes.c_double * 6),
        ("actual_TCP_force", ctypes.c_double * 6),
        ("target_q", ctypes.c_double * 6),
        ("target_qd", ctypes.c_double * 6),
        ("target_TCP_pose", ctypes.c_double * 6),
        ("target_TCP_speed", ctypes.c_double * 6),
        ("robot_mode", ctypes.c_int32),
        ("safety_mode", ctypes.c_int32),
        ("runtime_state", ctypes.c_uint32),
        ("robot_status_bits", ctypes.c_uint32),
        ("safety_status_bits", ctypes.c_uint32),
        ("speed_scaling", ctypes.c_double),
        ("payload", ctypes.c_double),
        ("payload_cog", ctypes.c_double * 3),
        ("standard_analog_input0", ctypes.c_double),
        ("standard_analog_input1", ctypes.c_double),
        ("standard_analog_output0", ctypes.c_double),
        ("standard_analog_output1", ctypes.c_double),
        ("actual_digital_input_bits", ctypes.c_uint64),
        ("actual_digital_output_bits", ctypes.c_uint64),
        ("output_int_register_0", ctypes.c_int32),
        ("tool_analog_input0", ctypes.c_double),
        ("tool_analog_input1", ctypes.c_double),
        ("tool_output_voltage", ctypes.c_int32),
        ("tool_output_current", ctypes.c_double),
        ("tool_temperature", ctypes.c_double),
    ]


class TorqueOutputData(OutputData):
    """OutputData plus fields that require controller >= 5.23."""

    _fields_ = [("actual_current_as_torque", ctypes.c_double * 6)]


class SpeedSliderInput(Recipe):
    _fields_ = [
        ("speed_slider_mask", ctypes.c_uint32),
        ("speed_slider_fraction", ctypes.c_double),
    ]


class DigitalOutputInput(Recipe):
    _fields_ = [
        ("standard_digital_output_mask", ctypes.c_uint8),
        ("standard_digital_output", ctypes.c_uint8),
    ]


class AnalogOutputInput(Recipe):
    _fields_ = [
        ("standard_analog_output_mask", ctypes.c_uint8),
        ("standard_analog_output_type", ctypes.c_uint8),
        ("standard_analog_output_0", ctypes.c_double),
        ("standard_analog_output_1", ctypes.c_double),
    ]
