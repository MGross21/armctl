<div align="center">
    <h1><img src="assets/logo/armctl_logo_orange.png" alt="armctl" width="300px"></h1>
</div>

A unified Python interface for controlling a variety of industrial and hobbyist robots from different manufacturers.

## Supported Manufacturers & Series

### [Elephant Robotics](https://www.elephantrobotics.com/en/)

- **Models:** myCobot Pro600  
  <img src="https://raw.githubusercontent.com/MGross21/armctl/main/assets/gifs/elephant_pro600.gif" alt="Elephant myCobot Pro600" width="400">

### [Universal Robotics](https://www.universal-robots.com)

- **Models:** UR5, UR5e

### [Vention](https://vention.io)

- **Models:** 7th Axis Plate  
  <img src="https://raw.githubusercontent.com/MGross21/armctl/main/assets/gifs/ur5_vention.gif" alt="UR5 on Vention Plate" width="400">

## Quick Start

### Installation

```text
pip install git+https://github.com/MGross21/armctl.git
```

#### Adding to Project Dependencies

*`requirements.txt`*

```text
git+https://github.com/MGross21/armctl.git
```

*`pyproject.toml`*

```toml
armctl = {git = "https://github.com/MGross21/armctl.git"}
```

### Importing the Library

> [!NOTE]  
> For improved runtime performance and clarity, you may import specific manufacturers and robot series directly.

```python
from armctl import *
```

### Simple Example with Manufacturer Defaults

```python
with Manufacturer("ROBOT_IP_ADDRESS") as robot:
    robot.move_joints([...])
    robot.get_joint_positions()
    robot.move_cartesian([...])
    robot.get_cartesian_position(...)
    robot.sleep(...)
    robot.get_robot_state()
```

### Simple Example with Specific Robot Series

```python
with RobotSeries("ROBOT_IP_ADDRESS") as robot:
    robot.home()
    robot.move_joints([...])
    robot.get_joint_positions()
    robot.move_cartesian([...])
    robot.get_cartesian_position()
    robot.sleep(...)
    robot.get_robot_state()
```

### Multi-Robot Control

```python
with (
  Robot1("ROBOT1_IP_ADDRESS") as r1,
  Robot2("ROBOT2_IP_ADDRESS") as r2,
):
    r1.home()
    r2.home()

    r1.move_joints([...])
    r2.move_joints([...])
```

> [!TIP]  
> For more precise and synchronous control of two or more robots, it is recommended to manage each robot within its own thread or process.

#### Multithread Control

Replicating the prior example,

```python
import threading

def control_robot(robot, ip):
  with robot(ip) as r:
    r.home()
    r.move_joints([0] * r.DOF)

threads = [
  threading.Thread(target=control_robot, args=(Robot1, "ROBOT1_IP")),
  threading.Thread(target=control_robot, args=(Robot2, "ROBOT2_IP"))
]

for t in threads:
  t.start()
for t in threads:
  t.join()
```

## API Reference

> [!NOTE]  
> The API has been designed for maximum compatibility across supported robots. Additional commands, such as gripper controls and other advanced features, are planned for future releases to further expand functionality.

### Control Template

The following methods are available to users of the library to control various supported robots.

| Method Name                  | Description                                                                 |
|------------------------------|-----------------------------------------------------------------------------|
| `move_joints(pos)` | Move the robot to specified joint positions.             |
| `get_joint_positions()` | Retrieve the current joint positions of the robot.                |
| `move_cartesian(pose)` | Move the robot to a specified Cartesian pose.              |
| `get_cartesian_position()` | Retrieve the current Cartesian position of the robot.          |
| `stop_motion()`              | Stop all robot motion immediately.                                          |
| `get_robot_state()`          | Retrieve the current state of the robot.                                    |
| `sleep(seconds)`             | Pause execution for a specified number of seconds.                          |
| `home()` <br> <sub>*(Available only for specific robot series, not for generic manufacturer control)*</sub> | Move the robot to its home position. |

#### Standard Units

All inputs and outputs use these standard units:

| Type                   | Unit                     |
| ---------------------- | ------------------------ |
| **Joint Angle**        | radians                  |
| **Cartesian Position** | meters (`[x, y, z]`)     |
| **Cartesian Rotation** | radians (`[rx, ry, rz]`) |

### Connection Template

The following methods facilitate explicit connection management and low-level command execution. These are primarily intended for advanced scenarios, such as when not using Python's `with/as` context manager or when sending custom commands outside the standard API. *Use with caution*.

| Method Name                  | Description                                                      |
|------------------------------|------------------------------------------------------------------|
| `connect()`                  | Establish a connection to the robot controller.                  |
| `disconnect()`               | Close the connection to the robot controller.                    |
| `send_command(cmd)` | Send a low-level command to the robot controller.    |

### Graphical Overview

Below is a high-level diagram illustrating the architecture of the `armctl` library. This design emphasizes the careful templatization of connection and control APIs, ensuring a consistent and extensible interface across different manufacturers and robot series.

```mermaid
flowchart TD
    CommTemplate["Communication Template"] --> SocketController["Socket Controller"] & PLCController["PLC Controller"] & SerialController["Serial Controller"]
    CtrlTemplate["Control Template"] --> Manufacturer1["Manufacturer (Socket-based)"] & Manufacturer2["Manufacturer (PLC-based)"] & Manufacturer3["Manufacturer (Serial-based)"]
    SocketController --> Manufacturer1
    PLCController --> Manufacturer2
    SerialController --> Manufacturer3
    Manufacturer2 --> Series2["Robot Series"]
    Manufacturer3 --> Series3["Robot Series"]
    Manufacturer1 --> n3["Robot Series"]
    style CommTemplate color:#D50000
    style SocketController stroke:#000000
    style PLCController stroke:#000000
    style SerialController stroke:#000000
    style CtrlTemplate color:#D50000
    style Manufacturer2 stroke:#000000
    style Manufacturer3 stroke:#000000
```

## Under Development

- [JAKA](https://www.jaka.com/en)
  - **Models:** Zu 5
- [Dobot](https://www.dobot-robots.com)
  - **Models:** Magician Lite

## Future Development

- [FANUC](https://www.fanucamerica.com)
  - **Models:** LR Mate 200iD Series
- **More manufacturers and robot series will be supported in future releases.**

> **Contributors wanted!**  
> Interested in robotics or Python? Join the project and help expand `armctl`!

## Contributing

Please feel free to submit a pull request or open an issue for any enhancements or bug fixes. See [CONTRIBUTING](https://github.com/MGross21/armctl/blob/main/CONTRIBUTING.md) for more details.

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/MGross21/armctl/blob/main/LICENSE) file for more details.
