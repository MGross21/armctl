import pytest

from tests._mock_robot import TEST_STRING_PREFIX, MockSocketRobot


@pytest.fixture
def echo_robot():
    with MockSocketRobot() as robot:
        yield robot


@pytest.mark.parametrize(
    "method, args, expected",
    [
        ("move_joints", ([1, 2, 3],), "MOVE_JOINTS: [1, 2, 3]"),
        ("move_cartesian", ([0.1, 0.2, 0.3],), "MOVE_CARTESIAN: [0.1, 0.2, 0.3]"),
        ("get_joint_positions", (), "GET_JOINT_POSITIONS"),
        ("get_cartesian_position", (), "GET_CARTESIAN_POSITION"),
        ("stop_motion", (), "STOP_MOTION"),
        ("get_robot_state", (), "GET_ROBOT_STATE"),
    ],
)
def test_command_round_trips_over_socket(echo_robot, method, args, expected):
    assert getattr(echo_robot, method)(*args) == f"{TEST_STRING_PREFIX} {expected}"


def test_reconnect_after_disconnect(echo_robot):
    echo_robot.disconnect()
    echo_robot.connect()
    assert echo_robot.stop_motion() == f"{TEST_STRING_PREFIX} STOP_MOTION"
