#!/usr/bin/env python3
"""
armctl - Agnostic Robotic Manipulation Controller
Minimal CLI for controlling robotic arms across multiple vendors.
"""

import sys
import signal
import atexit
from typing import Optional, List
from enum import Enum

import typer
from . import Logger, __version__, __all__
from .utils import NetworkScanner

# Global state
_robot = None
app = typer.Typer(help="Agnostic Robotic Manipulation Controller")


class RobotType(str, Enum):
    """Dynamically populated robot types."""
    pass


def get_robot_types():
    """Get available robot types dynamically."""
    import armctl
    types = {}
    for name in __all__:
        try:
            cls = getattr(armctl, name)
            key = name.lower()
            types[key] = cls
            # Add aliases
            if 'universal' in key or key.startswith('ur'):
                if key == 'universalrobots':
                    types['ur'] = cls
            elif 'elephant' in key:
                types['elephant'] = cls
        except (AttributeError, ImportError):
            continue
    return types


def setup_robot_enum():
    """Dynamically create robot type enum."""
    types = list(get_robot_types().keys())
    return Enum('RobotType', {t.upper(): t for t in types}, type=str)


# Create dynamic enum
RobotType = setup_robot_enum()


def cleanup():
    """Cleanup on exit."""
    global _robot
    if _robot:
        try:
            _robot.disconnect()
        except Exception:
            pass


def signal_handler(signum, frame):
    """Handle signals."""
    global _robot
    if _robot:
        try:
            _robot.stop_motion()
            _robot.disconnect()
        except Exception:
            pass
    sys.exit(0)


# Setup signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
atexit.register(cleanup)


@app.command()
def connect(
    ip: str = typer.Option(..., help="Robot IP address"),
    robot_type: RobotType = typer.Option(..., help="Robot type"),
    port: Optional[int] = typer.Option(None, help="Robot port")
):
    """Connect to robot."""
    global _robot
    Logger.disable()
    
    types = get_robot_types()
    robot_class = types.get(robot_type.value)
    
    if not robot_class:
        typer.echo(f"Unknown robot type: {robot_type.value}", err=True)
        raise typer.Exit(1)
    
    try:
        _robot = robot_class(ip, port) if port else robot_class(ip)
        _robot.connect()
    except Exception as e:
        typer.echo(f"Connection failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def disconnect():
    """Disconnect from robot."""
    global _robot
    if not _robot:
        typer.echo("No active connection", err=True)
        raise typer.Exit(1)
    
    try:
        _robot.disconnect()
        _robot = None
    except Exception as e:
        typer.echo(f"Disconnect failed: {e}", err=True)
        raise typer.Exit(1)


# Movement commands
move_app = typer.Typer(help="Movement commands")
app.add_typer(move_app, name="move")


@move_app.command()
def joints(positions: List[float] = typer.Argument(..., help="6 joint positions in radians")):
    """Move to joint positions."""
    global _robot
    if not _robot:
        typer.echo("Not connected", err=True)
        raise typer.Exit(1)
    
    if len(positions) != 6:
        typer.echo("Exactly 6 joint positions required", err=True)
        raise typer.Exit(1)
    
    try:
        _robot.move_joints(positions)
    except Exception as e:
        typer.echo(f"Movement failed: {e}", err=True)
        raise typer.Exit(1)


@move_app.command()
def cartesian(pose: List[float] = typer.Argument(..., help="6DOF pose: x y z rx ry rz")):
    """Move to Cartesian pose."""
    global _robot
    if not _robot:
        typer.echo("Not connected", err=True)
        raise typer.Exit(1)
    
    if len(pose) != 6:
        typer.echo("Exactly 6 pose values required", err=True)
        raise typer.Exit(1)
    
    try:
        _robot.move_cartesian(pose)
    except Exception as e:
        typer.echo(f"Movement failed: {e}", err=True)
        raise typer.Exit(1)


@move_app.command()
def home():
    """Move to home position."""
    global _robot
    if not _robot:
        typer.echo("Not connected", err=True)
        raise typer.Exit(1)
    
    try:
        if hasattr(_robot, 'home'):
            _robot.home()
        else:
            typer.echo("Home not supported", err=True)
            raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Home failed: {e}", err=True)
        raise typer.Exit(1)


# Get commands
get_app = typer.Typer(help="Get robot information")
app.add_typer(get_app, name="get")


@get_app.command()
def joints():
    """Get current joint positions."""
    global _robot
    if not _robot:
        typer.echo("Not connected", err=True)
        raise typer.Exit(1)
    
    try:
        positions = _robot.get_joint_positions()
        for pos in positions:
            typer.echo(pos)
    except Exception as e:
        typer.echo(f"Failed: {e}", err=True)
        raise typer.Exit(1)


@get_app.command()
def cartesian():
    """Get current Cartesian position."""
    global _robot
    if not _robot:
        typer.echo("Not connected", err=True)
        raise typer.Exit(1)
    
    try:
        pose = _robot.get_cartesian_position()
        for p in pose:
            typer.echo(p)
    except Exception as e:
        typer.echo(f"Failed: {e}", err=True)
        raise typer.Exit(1)


@get_app.command()
def state():
    """Get robot state."""
    global _robot
    if not _robot:
        typer.echo("Not connected", err=True)
        raise typer.Exit(1)
    
    try:
        state = _robot.get_robot_state()
        typer.echo(state)
    except Exception as e:
        typer.echo(f"Failed: {e}", err=True)
        raise typer.Exit(1)


# Control commands
control_app = typer.Typer(help="Robot control")
app.add_typer(control_app, name="control")


@control_app.command()
def stop():
    """Stop robot motion."""
    global _robot
    if not _robot:
        typer.echo("Not connected", err=True)
        raise typer.Exit(1)
    
    try:
        _robot.stop_motion()
    except Exception as e:
        typer.echo(f"Stop failed: {e}", err=True)
        raise typer.Exit(1)


@control_app.command()
def sleep(duration: float = typer.Argument(..., help="Sleep duration in seconds")):
    """Pause execution."""
    global _robot
    if not _robot:
        typer.echo("Not connected", err=True)
        raise typer.Exit(1)
    
    try:
        _robot.sleep(duration)
    except Exception as e:
        typer.echo(f"Sleep failed: {e}", err=True)
        raise typer.Exit(1)


# Utils commands
utils_app = typer.Typer(help="Utility commands")
app.add_typer(utils_app, name="utils")


@utils_app.command()
def scan(
    basic: bool = typer.Option(False, "--basic", help="Basic network scan"),
    listen: bool = typer.Option(False, "--listen", help="Monitor network changes"),
    ports: bool = typer.Option(False, "--ports", help="Include port scanning")
):
    """Scan for devices/controllers."""
    if listen:
        def callback(new, removed):
            for device in new:
                typer.echo(f"+{device}")
                if ports:
                    device_ports = NetworkScanner.scan_ports(device, timeout=0.3)
                    for port in device_ports:
                        typer.echo(f"  :{port}")
            for device in removed:
                typer.echo(f"-{device}")
        
        NetworkScanner.monitor_network(callback=callback)
        
    elif basic:
        devices = NetworkScanner.scan_network()
        for device in devices:
            typer.echo(device)
    else:
        controllers = NetworkScanner.scan_for_controllers()
        if controllers:
            for controller in controllers:
                typer.echo(controller['ip'])
                for port in controller['ports']:
                    typer.echo(f"  :{port}")
        else:
            devices = NetworkScanner.scan_network()
            for device in devices:
                typer.echo(device)


@utils_app.command()
def list():
    """List available robot types."""
    types = get_robot_types()
    for robot_type, robot_class in sorted(types.items()):
        typer.echo(f"{robot_type:<20} -> {robot_class.__name__}")


def main():
    """Main entry point."""
    Logger.disable()
    app()


if __name__ == "__main__":
    main()
