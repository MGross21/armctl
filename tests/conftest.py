import logging
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

import armctl
import armctl.__main__ as cli

JOINTS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
POSE = [0.5, 0.0, 0.3, 0.0, 1.57, 0.0]


@pytest.fixture(autouse=True)
def _reset_global_state():
    yield
    cli._robot = None
    logging.disable(logging.NOTSET)


@pytest.fixture(scope="session")
def runner():
    return CliRunner(env={"NO_COLOR": "1"})


@pytest.fixture
def cli_robot(monkeypatch):
    """Replace every exported robot class with a factory returning one shared MagicMock."""
    robot = MagicMock()
    robot.get_joint_positions.return_value = JOINTS
    robot.get_cartesian_position.return_value = POSE
    robot.get_robot_state.return_value = "RUNNING"
    robot.init_args = None
    del robot.home

    def factory(*args):
        robot.init_args = args
        return robot

    for name in armctl.__all__:
        monkeypatch.setattr(armctl, name, factory)
    return robot


@pytest.fixture
def connected(runner, cli_robot):
    result = runner.invoke(cli.app, ["connect", "--ip", "10.0.0.1", "--robot-type", "ur"])
    assert result.exit_code == 0, result.output
    return cli_robot
