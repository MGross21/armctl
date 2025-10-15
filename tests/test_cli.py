#!/usr/bin/env python3
"""Comprehensive CLI tests for armctl."""

import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

import armctl
from armctl.__main__ import app, get_robot_types
from armctl.utils import NetworkScanner


@pytest.fixture(scope="session")
def runner():
    """Session-scoped CLI runner fixture."""
    return CliRunner(env={"NO_COLOR": "1"})


@pytest.fixture(scope="function")
def mock_network_scanner(monkeypatch):
    """Mock NetworkScanner for network scan tests."""
    def mock_scan_network():
        return ["192.168.1.10", "192.168.1.20"]

    def mock_scan_for_controllers():
        return [
            {"ip": "192.168.1.10", "ports": [502, 8080]},
            {"ip": "192.168.1.20", "ports": [30001, 30002]},
        ]

    monkeypatch.setattr(NetworkScanner, "scan_network", mock_scan_network)
    monkeypatch.setattr(NetworkScanner, "scan_for_controllers", mock_scan_for_controllers)


@pytest.fixture(scope="function")
def mock_robot(monkeypatch):
    """Mock robot classes dynamically from armctl.__all__."""
    class MockRobot:
        def __init__(self, ip=None, port=None):
            self.ip = ip
            self.port = port
            self.connect = MagicMock()
            self.disconnect = MagicMock()
            self.move_joints = MagicMock()
            self.move_cartesian = MagicMock()
            self.get_joint_positions = MagicMock(return_value=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
            self.get_cartesian_position = MagicMock(return_value=[0.5, 0.0, 0.3, 0.0, 1.57, 0.0])
            self.get_robot_state = MagicMock(return_value="RUNNING")

    mock_instance = None
    
    def mock_robot_factory(ip=None, port=None):
        nonlocal mock_instance
        mock_instance = MockRobot(ip, port)
        return mock_instance
    
    for robot_class_name in armctl.__all__:
        try:
            monkeypatch.setattr(f"armctl.{robot_class_name}", mock_robot_factory)
        except AttributeError:
            pass
    
    class MockRobotAccessor:
        def get_instance(self):
            return mock_instance
    
    return MockRobotAccessor()


class TestCLIHelp:
    """Test help functionality for all commands."""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_main_help(self):
        """Test main command help."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Agnostic Robotic Manipulation Controller" in result.stdout
        assert "connect" in result.stdout
        assert "disconnect" in result.stdout
        assert "move" in result.stdout
        assert "get" in result.stdout
        assert "control" in result.stdout
        assert "utils" in result.stdout
    
    def test_connect_help(self):
        """Test connect command help."""
        result = self.runner.invoke(app, ["connect", "--help"])
        assert result.exit_code == 0
        assert "Connect to robot" in result.stdout
        assert "--ip" in result.stdout
        assert "--robot-type" in result.stdout
        assert "--port" in result.stdout
    
    def test_move_help(self):
        """Test move command help."""
        result = self.runner.invoke(app, ["move", "--help"])
        assert result.exit_code == 0
        assert "Movement commands" in result.stdout
        assert "joints" in result.stdout
        assert "cartesian" in result.stdout
        assert "home" in result.stdout
    
    def test_get_help(self):
        """Test get command help."""
        result = self.runner.invoke(app, ["get", "--help"])
        assert result.exit_code == 0
        assert "Get robot information" in result.stdout
        assert "joints" in result.stdout
        assert "cartesian" in result.stdout
        assert "state" in result.stdout
    
    def test_control_help(self):
        """Test control command help."""
        result = self.runner.invoke(app, ["control", "--help"])
        assert result.exit_code == 0
        assert "Robot control" in result.stdout
        assert "stop" in result.stdout
        assert "sleep" in result.stdout
    
    def test_utils_help(self):
        """Test utils command help."""
        result = self.runner.invoke(app, ["utils", "--help"])
        assert result.exit_code == 0
        assert "Utility commands" in result.stdout
        assert "scan" in result.stdout
        assert "list" in result.stdout


class TestUtilsCommands:
    """Test utility commands."""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_utils_list(self):
        result = self.runner.invoke(app, ["utils", "list"])
        assert result.exit_code == 0
        robot_types = get_robot_types()
        for robot_type in robot_types:
            assert robot_type in result.stdout
    
    def test_utils_scan_basic(self, runner, mock_network_scanner):
        result = runner.invoke(app, ["utils", "scan", "--basic"])
        assert result.exit_code == 0
        assert "192.168.1.10" in result.stdout
        assert "192.168.1.20" in result.stdout
    
    def test_utils_scan_controllers(self, runner, mock_network_scanner):
        result = runner.invoke(app, ["utils", "scan"])
        assert result.exit_code == 0
        assert "192.168.1.10" in result.stdout
        assert ":502" in result.stdout
        assert ":8080" in result.stdout
        assert "192.168.1.20" in result.stdout
        assert ":30001" in result.stdout
        assert ":30002" in result.stdout
    
    def test_utils_scan_fallback(self, runner, mock_network_scanner, monkeypatch):
        def mock_scan_for_controllers_empty():
            return []

        monkeypatch.setattr(NetworkScanner, "scan_for_controllers", mock_scan_for_controllers_empty)
        result = runner.invoke(app, ["utils", "scan"])
        assert result.exit_code == 0
        assert "192.168.1.10" in result.stdout
        assert "192.168.1.20" in result.stdout


class TestConnectionCommands:
    """Test connection commands."""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_connect_missing_ip(self):
        result = self.runner.invoke(app, ["connect", "--robot-type", "ur5"])
        assert result.exit_code == 2
    
    def test_connect_missing_robot_type(self):
        result = self.runner.invoke(app, ["connect", "--ip", "192.168.1.10"])
        assert result.exit_code == 2
    
    def test_connect_invalid_robot_type(self):
        result = self.runner.invoke(app, ["connect", "--ip", "192.168.1.10", "--robot-type", "invalid_robot"])
        assert result.exit_code == 2
    
    def test_connect_success(self, runner, mock_robot):
        result = runner.invoke(app, ["connect", "--ip", "192.168.1.10", "--robot-type", "universalrobots"])
        assert result.exit_code == 0
        instance = mock_robot.get_instance()
        assert instance is not None
        instance.connect.assert_called_once()
    
    def test_connect_with_port(self, runner, mock_robot):
        result = runner.invoke(app, ["connect", "--ip", "192.168.1.10", "--robot-type", "universalrobots", "--port", "30001"])
        assert result.exit_code == 0
        instance = mock_robot.get_instance()
        assert instance is not None
        instance.connect.assert_called_once()
    
    def test_connect_failure(self, runner, mock_robot):
        class FailingRobot:
            def __init__(self, ip=None, port=None):
                self.ip = ip
                self.port = port
            
            def connect(self):
                raise Exception("Connection failed")
        
        def mock_get_robot_types_failing():
            types = get_robot_types()
            types['universalrobots'] = FailingRobot
            return types
        
        with patch('armctl.__main__.get_robot_types', mock_get_robot_types_failing):
            result = runner.invoke(app, ["connect", "--ip", "192.168.1.10", "--robot-type", "universalrobots"])
            assert result.exit_code == 1
            output = result.stderr if hasattr(result, 'stderr') else result.stdout
            assert "Connection failed" in output
    
    def test_disconnect_no_connection(self, runner):
        result = runner.invoke(app, ["disconnect"])
        assert result.exit_code in [0, 1]


class TestMovementCommands:
    """Test movement commands."""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_move_joints_no_connection(self):
        result = self.runner.invoke(app, ["move", "joints", "0", "0", "0", "0", "0", "0"])
        assert result.exit_code == 1
    
    def test_move_joints_wrong_count(self):
        result = self.runner.invoke(app, ["move", "joints", "0", "0", "0"])
        assert result.exit_code == 1
    
    def test_move_cartesian_no_connection(self):
        result = self.runner.invoke(app, ["move", "cartesian", "0", "0", "0", "0", "0", "0"])
        assert result.exit_code == 1
    
    def test_move_cartesian_wrong_count(self):
        result = self.runner.invoke(app, ["move", "cartesian", "0", "0", "0", "0", "0"])
        assert result.exit_code == 2
    
    def test_move_home_no_connection(self):
        result = self.runner.invoke(app, ["move", "home"])
        assert result.exit_code == 1


class TestGetCommands:
    """Test get commands."""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_get_joints_no_connection(self):
        result = self.runner.invoke(app, ["get", "joints"])
        assert result.exit_code == 1
    
    def test_get_cartesian_no_connection(self):
        result = self.runner.invoke(app, ["get", "cartesian"])
        assert result.exit_code == 1
    
    def test_get_state_no_connection(self):
        result = self.runner.invoke(app, ["get", "state"])
        assert result.exit_code == 1


class TestControlCommands:
    """Test control commands."""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_control_stop_no_connection(self):
        result = self.runner.invoke(app, ["control", "stop"])
        assert result.exit_code == 1
    
    def test_control_sleep_no_connection(self):
        result = self.runner.invoke(app, ["control", "sleep", "1.0"])
        assert result.exit_code == 1
    
    def test_control_sleep_invalid_duration(self):
        result = self.runner.invoke(app, ["control", "sleep", "invalid"])
        assert result.exit_code != 0


class TestIntegratedWorkflow:
    """Test integrated workflows."""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_full_workflow(self, runner, mock_robot, monkeypatch):
        result = runner.invoke(app, ["connect", "--ip", "192.168.1.10", "--robot-type", "universalrobots"])
        assert result.exit_code == 0
        
        instance = mock_robot.get_instance()
        assert instance is not None
        instance.connect.assert_called_once()

        result = runner.invoke(app, ["disconnect"])
        assert result.exit_code == 0


class TestRobotTypeHandling:
    """Test robot type handling."""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_get_robot_types(self):
        types = get_robot_types()
        assert isinstance(types, dict)
        assert len(types) > 0
        expected_types = ['universalrobots', 'ur', 'jaka', 'vention', 'elephant']
        for expected in expected_types:
            assert expected in types
    
    @pytest.mark.parametrize("robot_type", [
        "universalrobots", "ur", "ur5", "ur10", "ur3", "ur5e", "ur16",
        "jaka", "vention", "elephant", "elephantrobotics", "pro600"
    ])
    def test_all_robot_types_connect(self, robot_type, runner, mock_robot):
        result = runner.invoke(app, ["connect", "--ip", "192.168.1.10", "--robot-type", robot_type])
        assert result.exit_code in [0, 2]
        if result.exit_code == 2:
            pytest.skip(f"Robot type {robot_type} not in current enum")


class TestErrorHandling:
    """Test error handling."""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_invalid_command(self):
        result = self.runner.invoke(app, ["invalid_command"])
        assert result.exit_code != 0
    
    def test_missing_subcommand(self):
        result = self.runner.invoke(app, ["move"])
        assert result.exit_code != 0
        
        result = self.runner.invoke(app, ["get"])
        assert result.exit_code != 0
        
        result = self.runner.invoke(app, ["control"])
        assert result.exit_code != 0
        
        result = self.runner.invoke(app, ["utils"])
        assert result.exit_code != 0
    
    def test_robot_method_with_mock(self, runner, mock_robot):
        result = runner.invoke(app, ["connect", "--ip", "192.168.1.10", "--robot-type", "universalrobots"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["move", "joints", "0", "0", "0", "0", "0", "0"])
        assert result.exit_code == 0

    def test_home_not_supported(self, runner, mock_robot):
        result = runner.invoke(app, ["connect", "--ip", "192.168.1.10", "--robot-type", "universalrobots"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["move", "home"])
        assert result.exit_code == 1


class TestCLISubprocess:
    """Test CLI integration."""

    def test_cli_help(self, runner):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Agnostic Robotic Manipulation Controller" in result.stdout

    def test_cli_utils_list(self, runner):
        result = runner.invoke(app, ["utils", "list"])
        assert result.exit_code == 0
        assert "universalrobots" in result.stdout or "UniversalRobots" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])