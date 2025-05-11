# Robot Agnostic Controller

## Control Template

| Method Name                  | Description                                                                 |
|------------------------------|-----------------------------------------------------------------------------|
| `connect`                    | Establish a connection to the robot.                                       |
| `disconnect`                 | Disconnect from the robot.                                                 |
| `sleep(seconds)`             | Pause execution for a specified number of seconds.                         |
| `move_joints(joint_positions, *args, **kwargs)` | Move the robot to specified joint positions.                                |
| `get_joint_positions(*args, **kwargs)` | Retrieve the current joint positions of the robot.                          |
| `move_cartesian(robot_pose, *args, **kwargs)` | Move the robot to a specified Cartesian pose.                               |
| `get_cartesian_position(*args, **kwargs)` | Retrieve the current Cartesian position of the robot.                      |
| `stop_motion()`              | Stop all robot motion immediately.                                         |
| `get_robot_state()`          | Retrieve the current state of the robot.                                   |

## Supported Manufacturers & Series

- [Elephant Robotics](https://www.elephantrobotics.com/en/)
  - myCobot Pro600
- [Universal Robotics](https://www.universal-robots.com)
  - UR5
  - UR5e

## Installation

```
pip install git+https://github.com/MGross21/agnostic-controller.git#egg=agnostic-controller
```

## Usage

*Example*

```python
from agnostic_controller import *

with UR5("ROBOT_IP_ADDRESS") as ur5:
    ur5.home()
    ur5.move_joints([0,0,0,0,0,0])

```

## Future Development

- [Dobot](https://www.dobot-robots.com)
  - Magician Lite
- [FANUC](https://www.fanucamerica.com)
  - LR Mate 200iD Series

## Contributing

Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/MGross21/agnostic-controller/blob/main/LICENSE) file for more details.