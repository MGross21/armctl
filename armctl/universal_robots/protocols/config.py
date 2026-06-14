import ctypes


class OutputData(ctypes.BigEndianStructure):
    _pack_ = 1
    _layout_ = "ms"
    _fields_ = [
        ("recipe_id", ctypes.c_uint8),
        ("actual_q", ctypes.c_double * 6),
        ("actual_qd", ctypes.c_double * 6),
        ("actual_current", ctypes.c_double * 6),
        ("actual_current_as_torque", ctypes.c_double * 6),
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
        ("standard_digital_input_bits", ctypes.c_uint32),
        ("standard_digital_output_bits", ctypes.c_uint32),
        ("output_int_registers_0", ctypes.c_int32),
        ("tool_analog_input0", ctypes.c_double),
        ("tool_analog_input1", ctypes.c_double),
        ("tool_output_voltage", ctypes.c_int32),
        ("tool_output_current", ctypes.c_double),
        ("tool_temperature", ctypes.c_double),
    ]


class InputData(ctypes.BigEndianStructure):
    _pack_ = 1
    _layout_ = "ms"
    _fields_ = [
        ("recipe_id", ctypes.c_uint8),
        ("speed_slider_mask", ctypes.c_uint32),
        ("speed_slider_fraction", ctypes.c_double),
        ("standard_digital_output_mask", ctypes.c_uint32),
        ("standard_digital_output", ctypes.c_uint32),
        ("standard_analog_output_mask", ctypes.c_uint32),
        ("standard_analog_output_type", ctypes.c_uint32),
        ("standard_analog_output_0", ctypes.c_double),
        ("standard_analog_output_1", ctypes.c_double),
    ]


OUTPUT_NAMES = [f[0] for f in OutputData._fields_[1:]]
INPUT_NAMES = [f[0] for f in InputData._fields_[1:]]

OUTPUT_SIZE = ctypes.sizeof(OutputData)
INPUT_SIZE = ctypes.sizeof(InputData)
