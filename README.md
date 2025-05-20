<div align="center">
    <h1><img src="assets/logo/armctl_logo_orange.png" alt="armctl" width="300px"></h1>
</div>

## Overview

A unified Python interface for controlling a variety of industrial and collaborative robots from different manufacturers.

## Supported Manufacturers & Series

- [Elephant Robotics](https://www.elephantrobotics.com/en/)
  - myCobot Pro600
  <br>
  <img src="https://raw.githubusercontent.com/MGross21/agnostic-controller/main/assets/gifs/elephant_pro600.gif" alt="Elephant myCobot Pro600" width="400">

- [Universal Robotics](https://www.universal-robots.com)
  - UR5
  - UR5e

- [Vention](https://vention.io)
  - 7th Axis Plate
  <br>
  <img src="https://raw.githubusercontent.com/MGross21/agnostic-controller/main/assets/gifs/ur5_vention.gif" alt="UR5 on Vention Plate" width="400">

## Quick Start

### Installation

```text
pip install git+https://github.com/MGross21/agnostic-controller.git
```

#### Adding to Project Dependencies

*`requirements.txt`*

```text
git+https://github.com/MGross21/agnostic-controller.git
```

*`pyproject.toml`*

```toml
agnostic-controller = {git = "https://github.com/MGross21/agnostic-controller.git"}
```

### Importing the Library

> [!NOTE]  
> For improved runtime performance and clarity, you may import specific manufacturers and robot series directly.

```python
from agnostic_controller import *
```

### Basic Usage (Manufacturer Defaults)

```python
with Manufacturer("ROBOT_IP_ADDRESS") as robot:
    robot.home()
    robot.move_joints([0,0,0,0,0,0])
```

### Usage with Specific Robot Series

```python
with RobotSeries("ROBOT_IP_ADDRESS") as robot:
    robot.home()
    robot.move_joints([0,0,0,0,0,0])
```

### Multi-Robot Control

> [!TIP]  
> For more precise and synchronous control of two or more robots, it is recommended to manage each robot within its own thread or process.

```python
with Robot1("ROBOT1_IP_ADDRESS") as r1, Robot2("ROBOT2_IP_ADDRESS") as r2:
    r1.home()
    r2.home()

    r1.move_joints([0,0,0,0,0,0])
    r2.move_joints([0,0,0,0,0,0])
```

## API Reference

| Method Name                  | Description                                                                 |
|------------------------------|-----------------------------------------------------------------------------|
| `move_joints(joint_positions, *args, **kwargs)` | Move the robot to specified joint positions.             |
| `get_joint_positions(*args, **kwargs)` | Retrieve the current joint positions of the robot.                |
| `move_cartesian(robot_pose, *args, **kwargs)` | Move the robot to a specified Cartesian pose.              |
| `get_cartesian_position(*args, **kwargs)` | Retrieve the current Cartesian position of the robot.          |
| `stop_motion()`              | Stop all robot motion immediately.                                          |
| `get_robot_state()`          | Retrieve the current state of the robot.                                    |
| `sleep(seconds)`             | Pause execution for a specified number of seconds.                          |

## Future Development

- [Dobot](https://www.dobot-robots.com)
  - Magician Lite
- [FANUC](https://www.fanucamerica.com)
  - LR Mate 200iD Series
- [JAKA](https://www.jaka.com/en)
  - Zu 5

## Contributing

Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/MGross21/agnostic-controller/blob/main/LICENSE) file for more details.
