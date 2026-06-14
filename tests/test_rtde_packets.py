"""Tests for RTDE packet structure and wire-format correctness."""

import ctypes
import struct

import pytest

from armctl.universal_robots.protocols.config import (
    INPUT_NAMES,
    INPUT_SIZE,
    OUTPUT_NAMES,
    OUTPUT_SIZE,
    InputData,
    OutputData,
)
from armctl.universal_robots.protocols.rtde_core import Command


class TestCommand:
    def test_command_values_match_spec(self):
        assert Command.REQUEST_PROTOCOL_VERSION == ord("V")
        assert Command.GET_URCONTROL_VERSION == ord("v")
        assert Command.TEXT_MESSAGE == ord("M")
        assert Command.DATA_PACKAGE == ord("U")
        assert Command.SETUP_OUTPUTS == ord("O")
        assert Command.SETUP_INPUTS == ord("I")
        assert Command.START == ord("S")

    def test_command_packet_structure(self):
        payload = struct.pack(">H", 2)
        packet = struct.pack(">HB", len(payload) + 3, int(Command.REQUEST_PROTOCOL_VERSION)) + payload
        size, cmd = struct.unpack_from(">HB", packet, 0)
        assert size == 5
        assert cmd == ord("V")


class TestStructSizes:
    def test_output_data_size(self):
        assert ctypes.sizeof(OutputData) == 669

    def test_input_data_size(self):
        assert ctypes.sizeof(InputData) == 45

    def test_output_size_constant(self):
        assert OUTPUT_SIZE == 669

    def test_input_size_constant(self):
        assert INPUT_SIZE == 45


class TestFieldNames:
    def test_output_names_count(self):
        assert len(OUTPUT_NAMES) == 31

    def test_output_names_order(self):
        assert OUTPUT_NAMES[:11] == [
            "actual_q",
            "actual_qd",
            "actual_current",
            "actual_current_as_torque",
            "actual_TCP_pose",
            "actual_TCP_speed",
            "actual_TCP_force",
            "target_q",
            "target_qd",
            "target_TCP_pose",
            "target_TCP_speed",
        ]

    def test_input_names_order(self):
        assert INPUT_NAMES == [
            "speed_slider_mask",
            "speed_slider_fraction",
            "standard_digital_output_mask",
            "standard_digital_output",
            "standard_analog_output_mask",
            "standard_analog_output_type",
            "standard_analog_output_0",
            "standard_analog_output_1",
        ]


class TestOutputDataRoundtrip:
    def test_from_buffer_copy_zero(self):
        payload = bytes(669)
        data = OutputData.from_buffer_copy(payload)
        assert data.recipe_id == 0
        assert list(data.actual_q) == [0.0] * 6
        assert data.robot_mode == 0

    def test_recipe_id_preserved(self):
        raw = bytearray(669)
        raw[0] = 42
        data = OutputData.from_buffer_copy(bytes(raw))
        assert data.recipe_id == 42

    def test_double_vector_roundtrip(self):
        raw = bytearray(669)
        raw[0] = 1
        joints = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
        struct.pack_into(">6d", raw, 1, *joints)
        data = OutputData.from_buffer_copy(bytes(raw))
        assert [round(v, 9) for v in data.actual_q] == [round(v, 9) for v in joints]

    def test_int32_field_roundtrip(self):
        raw = bytearray(669)
        # robot_mode is at offset 1 + 11*6*8 = 529
        struct.pack_into(">i", raw, 529, -7)
        data = OutputData.from_buffer_copy(bytes(raw))
        assert data.robot_mode == -7

    def test_uint32_field_roundtrip(self):
        raw = bytearray(669)
        # safety_status_bits at offset 529 + 4 + 4 + 4 + 4 = 545
        struct.pack_into(">I", raw, 545, 0b10110)
        data = OutputData.from_buffer_copy(bytes(raw))
        assert data.safety_status_bits == 0b10110


class TestInputDataRoundtrip:
    def test_bytes_output_size(self):
        inp = InputData()
        assert len(bytes(inp)) == 45

    def test_recipe_id_in_first_byte(self):
        inp = InputData()
        inp.recipe_id = 3
        raw = bytes(inp)
        assert raw[0] == 3

    def test_speed_slider_mask_big_endian(self):
        inp = InputData()
        inp.recipe_id = 1
        inp.speed_slider_mask = 0x12345678
        raw = bytes(inp)
        assert raw[1:5] == b"\x12\x34\x56\x78"

    def test_speed_slider_fraction_big_endian(self):
        inp = InputData()
        inp.recipe_id = 1
        inp.speed_slider_fraction = 0.5
        raw = bytes(inp)
        expected = struct.pack(">d", 0.5)
        assert raw[5:13] == expected

    def test_roundtrip_via_from_buffer_copy(self):
        inp = InputData()
        inp.recipe_id = 7
        inp.speed_slider_mask = 1
        inp.speed_slider_fraction = 0.75
        inp.standard_digital_output_mask = 0xFF
        raw = bytes(inp)
        out = InputData.from_buffer_copy(raw)
        assert out.recipe_id == 7
        assert out.speed_slider_mask == 1
        assert abs(out.speed_slider_fraction - 0.75) < 1e-12
        assert out.standard_digital_output_mask == 0xFF


class TestEndianness:
    def test_output_command_packet_big_endian(self):
        packet = struct.pack(">HB", 5, int(Command.DATA_PACKAGE))
        assert packet[0] == 0
        assert packet[1] == 5
        assert packet[2] == ord("U")

    def test_input_data_is_big_endian(self):
        inp = InputData()
        inp.speed_slider_mask = 1
        raw = bytes(inp)
        # uint32 value 1 in big-endian = 0x00 0x00 0x00 0x01
        assert raw[1:5] == b"\x00\x00\x00\x01"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
