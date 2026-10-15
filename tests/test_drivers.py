import ast
import math
from unittest.mock import MagicMock

import pytest

from armctl import Jaka, UniversalRobots, Vention, Zaber

HOME = [0.0, -1.57, 1.57, 0.0, 0.0, 0.0]


@pytest.fixture
def ur():
    robot = UniversalRobots("10.0.0.1")
    robot.send_command = MagicMock(return_value="")
    robot.rtde = MagicMock()
    return robot


@pytest.fixture
def jaka():
    robot = Jaka("10.0.0.1")
    robot.send_command = MagicMock()
    return robot


def jaka_reply(robot, cmd_name, **fields):
    robot.send_command.return_value = str({"errorCode": "0", "cmdName": cmd_name, **fields})


@pytest.fixture
def vention(monkeypatch):
    monkeypatch.setattr("armctl.vention.vention.time.sleep", lambda _: None)
    robot = Vention()
    robot.send_command = MagicMock()
    return robot


def test_ur_move_joints_script(ur):
    ur.move_joints(HOME, speed=0.5, acceleration=0.2)
    ur.send_command.assert_called_once()
    assert ur.send_command.call_args.args[0] == (
        "write_output_integer_register(0,0)\n"
        "movej([0.0,-1.57,1.57,0.0,0.0,0.0], a=0.2, v=0.5, t=0.0, r=0.0)\n"
        "write_output_integer_register(0,1)\n"
    )
    ur.rtde.wait_until_stopped.assert_called_once_with(timeout=120.0)


def test_ur_blended_move_does_not_block(ur):
    ur.move_joints(HOME, radius=0.05)
    ur.rtde.wait_until_stopped.assert_not_called()


def test_ur_movep_omits_time(ur):
    ur.move_cartesian([0.1, 0.2, 0.3, 0.0, 3.14, 0.0], move_type="movep")
    script = ur.send_command.call_args.args[0]
    assert "movep(p[0.1,0.2,0.3,0.0,3.14,0.0], a=0.1, v=0.1, r=0.0)" in script
    assert "t=" not in script


def test_ur_rejects_unknown_move_type(ur):
    with pytest.raises(ValueError, match="Unsupported move type"):
        ur.move_cartesian([0.0] * 6, move_type="movec")
    ur.send_command.assert_not_called()


@pytest.mark.parametrize(
    "pos, kwargs, error",
    [
        (HOME[:5], {}, ValueError),
        ([7.0, 0, 0, 0, 0, 0], {}, ValueError),
        (HOME, {"speed": 5.0}, ValueError),
        (HOME, {"acceleration": 50.0}, ValueError),
        (tuple(HOME), {}, TypeError),
        (["0", 0, 0, 0, 0, 0], {}, TypeError),
    ],
)
def test_ur_validates_before_sending(ur, pos, kwargs, error):
    with pytest.raises(error):
        ur.move_joints(pos, **kwargs)
    ur.send_command.assert_not_called()


def test_jaka_move_joints_sends_degrees(jaka):
    jaka_reply(jaka, "joint_move")
    jaka.move_joints([math.pi / 2, 0, 0, 0, 0, 0], speed=math.pi, acceleration=math.pi / 2)
    sent = ast.literal_eval(jaka.send_command.call_args.args[0])
    assert sent["jointPosition"] == pytest.approx([90, 0, 0, 0, 0, 0])
    assert sent["speed"] == pytest.approx(180)
    assert sent["accel"] == pytest.approx(90)


def test_jaka_get_joint_positions_returns_radians(jaka):
    jaka_reply(jaka, "get_joint_pos", joint_pos=[90, 0, -90, 0, 180, 0])
    assert jaka.get_joint_positions() == pytest.approx(
        [math.pi / 2, 0, -math.pi / 2, 0, math.pi, 0]
    )


def test_jaka_get_cartesian_position_converts_orientation(jaka):
    jaka_reply(jaka, "get_tcp_pos", tcp_pos=[100, 200, 300, 90, 0, 180])
    assert jaka.get_cartesian_position() == pytest.approx([100, 200, 300, math.pi / 2, 0, math.pi])


@pytest.mark.parametrize(
    "reply",
    [
        str({"errorCode": "2", "cmdName": "get_joint_pos", "errorMsg": "not enabled"}),
        str({"errorCode": "0", "cmdName": "other_cmd"}),
        "not a dict literal",
    ],
)
def test_jaka_rejects_bad_replies(jaka, reply):
    jaka.send_command.return_value = reply
    with pytest.raises(RuntimeError):
        jaka.get_joint_positions()


def test_vention_move_converts_to_mm_and_waits(vention):
    vention.send_command.side_effect = ["Ack", "Ack", "Ack", "Ack", "Ack", "false", "true"]
    vention.move_joints([0.1, 0.25, 1.0], speed=1.0, acceleration=0.5)
    sent = [c.args[0] for c in vention.send_command.call_args_list]
    assert sent[:5] == [
        "SET speed/1.0/;",
        "SET acceleration/0.5/;",
        "SET im_move_abs_1/100.0/;",
        "SET im_move_abs_2/250.0/;",
        "SET im_move_abs_3/1000.0/;",
    ]
    assert sent[5:] == ["isMotionCompleted;", "isMotionCompleted;"]


def test_vention_move_fails_without_ack(vention):
    vention.send_command.side_effect = ["Ack", "Ack", "Nack"]
    with pytest.raises(RuntimeError, match="axis 1"):
        vention.move_joints([0.1, 0.1, 0.1])


@pytest.mark.parametrize(
    "reply, expected",
    [("(125.5)", 0.1255), ("(undefined)", 0.0)],
)
def test_vention_parses_axis_position(vention, reply, expected):
    vention.send_command.return_value = reply
    assert vention.get_joint_positions(axis=1) == pytest.approx(expected)


@pytest.mark.parametrize("reply", ["(-1)", "(garbage)"])
def test_vention_rejects_bad_axis_position(vention, reply):
    vention.send_command.return_value = reply
    with pytest.raises(RuntimeError):
        vention.get_joint_positions(axis=1)


@pytest.fixture
def zaber():
    pytest.importorskip("zaber_motion")
    robot = Zaber("10.0.0.1", num_axes=2)
    robot.axes = [MagicMock(), MagicMock()]
    return robot


def test_zaber_move_joints_moves_each_axis(zaber):
    zaber.move_joints([0.1, 0.2])
    for axis, target in zip(zaber.axes, [0.1, 0.2]):
        axis.move_absolute.assert_called_once_with(target, unit=zaber.units)
        axis.wait_until_idle.assert_called_once()


def test_zaber_rejects_out_of_range(zaber):
    with pytest.raises(ValueError):
        zaber.move_joints([0.1, 0.5])
    zaber.axes[0].move_absolute.assert_not_called()
