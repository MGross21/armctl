import time

import pytest

from tests._mock_robot import TEST_STRING_PREFIX, MockSocketRobot


@pytest.fixture
def mock_robot():
    with MockSocketRobot() as robot:
        yield robot


def test_move_joints(mock_robot):
    pos = [1, 2, 3]
    expected = f"{TEST_STRING_PREFIX} MOVE_JOINTS: {pos}"
    assert mock_robot.move_joints(pos) == expected


def test_move_cartesian(mock_robot):
    pose = [0.1, 0.2, 0.3]
    expected = f"{TEST_STRING_PREFIX} MOVE_CARTESIAN: {pose}"
    assert mock_robot.move_cartesian(pose) == expected


def test_get_joint_positions(mock_robot):
    expected = f"{TEST_STRING_PREFIX} GET_JOINT_POSITIONS"
    assert mock_robot.get_joint_positions() == expected


def test_get_cartesian_position(mock_robot):
    expected = f"{TEST_STRING_PREFIX} GET_CARTESIAN_POSITION"
    assert mock_robot.get_cartesian_position() == expected


def test_stop_motion(mock_robot):
    expected = f"{TEST_STRING_PREFIX} STOP_MOTION"
    assert mock_robot.stop_motion() == expected


def test_get_robot_state(mock_robot):
    expected = f"{TEST_STRING_PREFIX} GET_ROBOT_STATE"
    assert mock_robot.get_robot_state() == expected


def test_sleep_duration(mock_robot):
    sleep_seconds = 0.2
    start = time.time()
    mock_robot.sleep(sleep_seconds)
    elapsed = time.time() - start
    assert elapsed >= sleep_seconds
