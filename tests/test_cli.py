import re

import pytest

from armctl.__main__ import app, get_robot_types
from armctl.utils import NetworkScanner

EXPORTED_TYPES = sorted(get_robot_types())
ANSI = re.compile(r"\x1b\[[0-9;]*m")


@pytest.mark.parametrize(
    "args, expected",
    [
        ([], ["connect", "disconnect", "move", "get", "control", "utils"]),
        (["connect"], ["--ip", "--robot-type", "--port"]),
        (["move"], ["joints", "cartesian", "home"]),
        (["get"], ["joints", "cartesian", "state"]),
        (["control"], ["stop", "sleep"]),
        (["utils"], ["scan", "list"]),
    ],
)
def test_help_lists_subcommands(runner, args, expected):
    result = runner.invoke(app, [*args, "--help"])
    assert result.exit_code == 0
    output = ANSI.sub("", result.output)
    for word in expected:
        assert word in output


@pytest.mark.parametrize("group", ["move", "get", "control", "utils"])
def test_group_without_subcommand_shows_usage(runner, group):
    result = runner.invoke(app, [group])
    assert result.exit_code in (0, 2)  # click < 8.2 exits 0
    assert "Usage" in ANSI.sub("", result.output)


def test_unknown_command(runner):
    assert runner.invoke(app, ["invalid_command"]).exit_code == 2


def test_utils_list(runner):
    result = runner.invoke(app, ["utils", "list"])
    assert result.exit_code == 0
    for robot_type in EXPORTED_TYPES:
        assert robot_type in result.output


def test_utils_scan(runner, monkeypatch):
    monkeypatch.setattr(NetworkScanner, "scan_network", lambda: ["192.168.1.10", "192.168.1.20"])
    result = runner.invoke(app, ["utils", "scan"])
    assert result.exit_code == 0
    assert result.output.split() == ["192.168.1.10", "192.168.1.20"]


@pytest.mark.parametrize(
    "args",
    [
        ["connect", "--robot-type", "ur"],
        ["connect", "--ip", "10.0.0.1"],
        ["connect", "--ip", "10.0.0.1", "--robot-type", "invalid_robot"],
    ],
)
def test_connect_rejects_bad_options(runner, args):
    assert runner.invoke(app, args).exit_code == 2


@pytest.mark.parametrize("robot_type", EXPORTED_TYPES)
def test_connect_every_robot_type(runner, cli_robot, robot_type):
    result = runner.invoke(app, ["connect", "--ip", "10.0.0.1", "--robot-type", robot_type])
    assert result.exit_code == 0, result.output
    assert cli_robot.init_args == ("10.0.0.1",)
    cli_robot.connect.assert_called_once()


def test_connect_passes_port(runner, cli_robot):
    args = ["connect", "--ip", "10.0.0.1", "--robot-type", "ur", "--port", "30001"]
    assert runner.invoke(app, args).exit_code == 0
    assert cli_robot.init_args == ("10.0.0.1", 30001)


def test_connect_failure_reports_error(runner, cli_robot):
    cli_robot.connect.side_effect = ConnectionError("Connection failed")
    result = runner.invoke(app, ["connect", "--ip", "10.0.0.1", "--robot-type", "ur"])
    assert result.exit_code == 1
    assert "Connection failed" in result.output


def test_disconnect(runner, connected):
    assert runner.invoke(app, ["disconnect"]).exit_code == 0
    connected.disconnect.assert_called_once()
    assert runner.invoke(app, ["disconnect"]).exit_code == 1


@pytest.mark.parametrize(
    "args",
    [
        ["disconnect"],
        ["move", "joints", "0", "0", "0", "0", "0", "0"],
        ["move", "cartesian", "0", "0", "0", "0", "0", "0"],
        ["move", "home"],
        ["get", "joints"],
        ["get", "cartesian"],
        ["get", "state"],
        ["control", "stop"],
        ["control", "sleep", "1.0"],
    ],
)
def test_requires_connection(runner, args):
    result = runner.invoke(app, args)
    assert result.exit_code == 1
    assert "connect" in result.output.lower()


def test_move_joints_forwards_positions(runner, connected):
    result = runner.invoke(app, ["move", "joints", "1", "2", "3"])
    assert result.exit_code == 0
    connected.move_joints.assert_called_once_with([1.0, 2.0, 3.0])


def test_move_cartesian_forwards_pose(runner, connected):
    result = runner.invoke(app, ["move", "cartesian", "1", "2", "3", "4", "5", "6"])
    assert result.exit_code == 0
    connected.move_cartesian.assert_called_once_with([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])


def test_move_cartesian_requires_six_values(runner, connected):
    assert runner.invoke(app, ["move", "cartesian", "0", "0", "0", "0", "0"]).exit_code == 2
    connected.move_cartesian.assert_not_called()


def test_move_failure_reports_error(runner, connected):
    connected.move_joints.side_effect = ValueError("out of range")
    result = runner.invoke(app, ["move", "joints", "9"])
    assert result.exit_code == 1
    assert "out of range" in result.output


def test_move_home_unsupported(runner, connected):
    result = runner.invoke(app, ["move", "home"])
    assert result.exit_code == 1
    assert "not supported" in result.output


@pytest.mark.parametrize(
    "args, method",
    [
        (["get", "joints"], "get_joint_positions"),
        (["get", "cartesian"], "get_cartesian_position"),
    ],
)
def test_get_prints_positions(runner, connected, args, method):
    result = runner.invoke(app, args)
    assert result.exit_code == 0
    values = getattr(connected, method).return_value
    assert result.output.split() == [str(v) for v in values]


def test_get_state(runner, connected):
    result = runner.invoke(app, ["get", "state"])
    assert result.exit_code == 0
    assert result.output.strip() == "RUNNING"


def test_control_stop(runner, connected):
    assert runner.invoke(app, ["control", "stop"]).exit_code == 0
    connected.stop_motion.assert_called_once_with()


def test_control_sleep(runner, connected):
    assert runner.invoke(app, ["control", "sleep", "0.5"]).exit_code == 0
    connected.sleep.assert_called_once_with(0.5)


def test_control_sleep_rejects_non_number(runner, connected):
    assert runner.invoke(app, ["control", "sleep", "invalid"]).exit_code == 2
    connected.sleep.assert_not_called()


def test_get_robot_types_aliases():
    types = get_robot_types()
    assert types["ur"] is types["universalrobots"]
    assert types["elephant"] is types["elephantrobotics"]
