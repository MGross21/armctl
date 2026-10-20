"""Tests for RTDE packet structure and wire-format correctness."""

import ctypes
import socket
import struct

import pytest

from armctl.universal_robots.protocols.config import (
    AnalogOutputInput,
    DigitalOutputInput,
    OutputData,
    SpeedSliderInput,
    TorqueOutputData,
)
from armctl.universal_robots.protocols.rtde_core import Command, RTDEClient


class TestStructSizes:
    def test_output_data_size(self):
        assert ctypes.sizeof(OutputData) == 629

    def test_torque_output_data_appends_torque(self):
        assert ctypes.sizeof(TorqueOutputData) == 677
        assert TorqueOutputData.names == (*OutputData.names, "actual_current_as_torque")

    def test_input_data_sizes(self):
        assert ctypes.sizeof(SpeedSliderInput) == 13
        assert ctypes.sizeof(DigitalOutputInput) == 3
        assert ctypes.sizeof(AnalogOutputInput) == 19


class TestFieldNames:
    def test_output_names_count(self):
        assert len(OutputData.names) == 30

    def test_output_names_order(self):
        assert list(OutputData.names[:10]) == [
            "actual_q",
            "actual_qd",
            "actual_current",
            "actual_TCP_pose",
            "actual_TCP_speed",
            "actual_TCP_force",
            "target_q",
            "target_qd",
            "target_TCP_pose",
            "target_TCP_speed",
        ]

    def test_input_names_order(self):
        assert list(SpeedSliderInput.names) == ["speed_slider_mask", "speed_slider_fraction"]
        assert list(DigitalOutputInput.names) == [
            "standard_digital_output_mask",
            "standard_digital_output",
        ]
        assert list(AnalogOutputInput.names) == [
            "standard_analog_output_mask",
            "standard_analog_output_type",
            "standard_analog_output_0",
            "standard_analog_output_1",
        ]


class TestOutputDataRoundtrip:
    def test_from_buffer_copy_zero(self):
        payload = bytes(ctypes.sizeof(OutputData))
        data = OutputData.from_buffer_copy(payload)
        assert data.recipe_id == 0
        assert list(data.actual_q) == [0.0] * 6
        assert data.robot_mode == 0

    def test_recipe_id_preserved(self):
        raw = bytearray(ctypes.sizeof(OutputData))
        raw[0] = 42
        data = OutputData.from_buffer_copy(bytes(raw))
        assert data.recipe_id == 42

    def test_double_vector_roundtrip(self):
        raw = bytearray(ctypes.sizeof(OutputData))
        raw[0] = 1
        joints = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
        struct.pack_into(">6d", raw, 1, *joints)
        data = OutputData.from_buffer_copy(bytes(raw))
        assert [round(v, 9) for v in data.actual_q] == [round(v, 9) for v in joints]

    def test_int32_field_roundtrip(self):
        raw = bytearray(ctypes.sizeof(OutputData))
        # robot_mode is at offset 1 + 10*6*8 = 481
        struct.pack_into(">i", raw, 481, -7)
        data = OutputData.from_buffer_copy(bytes(raw))
        assert data.robot_mode == -7

    def test_uint32_field_roundtrip(self):
        raw = bytearray(ctypes.sizeof(OutputData))
        # safety_status_bits at offset 481 + 4 + 4 + 4 + 4 = 497
        struct.pack_into(">I", raw, 497, 0b10110)
        data = OutputData.from_buffer_copy(bytes(raw))
        assert data.safety_status_bits == 0b10110


class TestInputDataRoundtrip:
    def test_recipe_id_in_first_byte(self):
        inp = SpeedSliderInput()
        inp.recipe_id = 3
        raw = bytes(inp)
        assert raw[0] == 3

    def test_speed_slider_mask_big_endian(self):
        inp = SpeedSliderInput()
        inp.recipe_id = 1
        inp.speed_slider_mask = 0x12345678
        raw = bytes(inp)
        assert raw[1:5] == b"\x12\x34\x56\x78"

    def test_speed_slider_fraction_big_endian(self):
        inp = SpeedSliderInput()
        inp.recipe_id = 1
        inp.speed_slider_fraction = 0.5
        raw = bytes(inp)
        expected = struct.pack(">d", 0.5)
        assert raw[5:13] == expected

    def test_roundtrip_via_from_buffer_copy(self):
        inp = SpeedSliderInput()
        inp.recipe_id = 7
        inp.speed_slider_mask = 1
        inp.speed_slider_fraction = 0.75
        raw = bytes(inp)
        out = SpeedSliderInput.from_buffer_copy(raw)
        assert out.recipe_id == 7
        assert out.speed_slider_mask == 1
        assert abs(out.speed_slider_fraction - 0.75) < 1e-12


class TestRecipeTypes:
    def test_input_types_match_spec(self):
        assert list(SpeedSliderInput.rtde_types) == ["UINT32", "DOUBLE"]
        assert list(DigitalOutputInput.rtde_types) == ["UINT8", "UINT8"]
        assert list(AnalogOutputInput.rtde_types) == ["UINT8", "UINT8", "DOUBLE", "DOUBLE"]

    def test_torque_output_types_include_inherited_fields(self):
        types = TorqueOutputData.rtde_types
        assert len(types) == 31
        assert types[0] == types[-1] == "VECTOR6D"

    def test_parse_setup_returns_recipe_id(self):
        payload = b"\x04" + ",".join(DigitalOutputInput.rtde_types).encode()
        assert DigitalOutputInput.parse_setup(payload) == 4

    def test_parse_setup_returns_none_when_in_use(self):
        assert DigitalOutputInput.parse_setup(b"\x00IN_USE,UINT8") is None

    @pytest.mark.parametrize("bad", ["NOT_FOUND", "UINT32"])
    def test_parse_setup_rejects_mismatched_types(self, bad):
        payload = b"\x00" + f"{bad},UINT8".encode()
        with pytest.raises(RuntimeError, match="standard_digital_output_mask"):
            DigitalOutputInput.parse_setup(payload)


class TestRecipeInit:
    def test_keyword_fields(self):
        data = DigitalOutputInput(recipe_id=3, standard_digital_output_mask=2)
        assert bytes(data) == b"\x03\x02\x00"

    def test_rejects_unknown_field(self):
        with pytest.raises(TypeError, match="standard_digital_ouput"):
            DigitalOutputInput(recipe_id=1, standard_digital_ouput=1)

    def test_accepts_inherited_field(self):
        assert TorqueOutputData(robot_mode=7).robot_mode == 7


class TestReceive:
    @staticmethod
    def packet(command: Command, payload: bytes) -> bytes:
        return struct.pack(">HB", len(payload) + 3, command) + payload

    @classmethod
    def data_package(cls, robot_mode: int) -> bytes:
        data = OutputData(recipe_id=1)
        data.robot_mode = robot_mode
        return cls.packet(Command.DATA_PACKAGE, bytes(data))

    @pytest.fixture
    def pair(self):
        client = RTDEClient("unused")
        client._sock, server = socket.socketpair()
        client._sock.settimeout(1.0)
        yield client, server
        client.disconnect()
        server.close()

    def test_returns_newest_package_and_skips_text(self, pair):
        client, server = pair
        server.sendall(
            self.data_package(1)
            + self.packet(Command.TEXT_MESSAGE, b"hi")
            + self.data_package(2)
            + self.data_package(3)
        )
        assert client.receive().robot_mode == 3
        server.sendall(self.data_package(4))
        assert client.receive().robot_mode == 4

    def test_rejects_unexpected_command(self, pair):
        client, server = pair
        server.sendall(self.packet(Command.START, b"\x01"))
        with pytest.raises(RuntimeError, match="Unexpected RTDE command"):
            client.receive()

    def test_input_setup_returns_none_when_in_use(self, pair):
        client, server = pair
        server.sendall(self.packet(Command.SETUP_INPUTS, b"\x00IN_USE,DOUBLE"))
        assert client.send_input_setup(SpeedSliderInput) is None

    def test_input_setup_returns_recipe_id(self, pair):
        client, server = pair
        server.sendall(self.packet(Command.SETUP_INPUTS, b"\x02UINT8,UINT8"))
        assert client.send_input_setup(DigitalOutputInput) == 2

    def test_receive_uses_torque_recipe(self, pair):
        client, server = pair
        types = ",".join(TorqueOutputData.rtde_types).encode()
        server.sendall(self.packet(Command.SETUP_OUTPUTS, b"\x01" + types))
        client.send_output_setup(TorqueOutputData)
        data = TorqueOutputData(recipe_id=1)
        data.actual_current_as_torque[5] = 1.5
        server.sendall(self.packet(Command.DATA_PACKAGE, bytes(data)))
        assert client.receive().actual_current_as_torque[5] == 1.5

    def test_disconnect_raises(self, pair):
        client, server = pair
        server.close()
        with pytest.raises(ConnectionError):
            client.receive()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
