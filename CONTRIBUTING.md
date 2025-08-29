# Contributing Guide

Thank you for considering contributing!  
This document outlines the core conventions and control flow to maintain consistency across different robots and communication backends.

## Standard Units

To avoid confusion and unexpected behavior when interfacing with different robot models and manufacturers, **all user-facing inputs and outputs use the following standard units:**

| Type                   | Unit                     |
| ---------------------- | ------------------------ |
| **Joint Angle**        | radians                  |
| **Joint Velocity**     | radians/second           |
| **Joint Acceleration** | radians/second²          |
| **Cartesian Position** | meters (`[x, y, z]`)     |
| **Cartesian Rotation** | radians (`[rx, ry, rz]`) |

> 💡 Always convert incoming or outgoing data to these units at the API boundaries.

## Robot Control Commands

Each robot implementation should adhere to the following interface and checks to ensure predictable, safe operation across robot brands.

### Connect

Typical sequence to prepare a robot for motion:

1. Establish Python or network connection (`super().connect`)
2. Power on the robot
3. Check and reset emergency stop status if needed
4. Enable robot drives
5. Perform any required initialization (e.g. homing, zeroing)

### Disconnect

Sequence to safely disconnect:

1. Stop any ongoing motion (preferably with a controlled deceleration)
2. Optionally disable robot drives (use with caution)
3. Optionally power off the robot (use with caution)
4. Close Python/network connection (`super().disconnect`)

### Move Joints

1. Check validitiy of command (formatting and ranges)
2. Format and send the command
3. Receive and parse response (if applicable)
4. Assert valid or expected response
5. Return response (or confirmation)

### Move Cartesian

1. Check validitiy of command (formatting and ranges)
2. Format and send the Cartesian move command
3. Receive and parse response
4. Assert validity
5. Return response

### Get Joint Position

1. Send query command
2. Parse returned joint positions
3. Validate against expected format (array of floats, length matches DOF)
4. Return joint positions in radians

### Get Cartesian Position

1. Send query command
2. Parse returned Cartesian pose
3. Validate expected 6-element format
4. Return pose in meters/radians

### Get Robot State

1. Send status/state request
2. Parse response (e.g. motion state, errors, safety stops)
3. Assert format and expected contents
4. Return structured state data

### Stop Motion

1. Send stop command (with deceleration if supported)
2. Parse and validate acknowledgement
3. Return confirmation

### Sleep

#### If Robot Supports Native Sleep

1. Send sleep command (e.g. to enter idle or low-power state)
2. Parse acknowledgement
3. Return confirmation

#### If Not Supported

* Use Python's `time.sleep(seconds)` to pause execution.

## Adding a New Robot

To add support for a new robot, follow these steps:

1. **Start with the Template:**  
    Use the [`BlankRobot`](armctl/_blank/robot.py) class as a starting point. This template outlines the required interface and structure for robot integration.

2. **Implement Required Methods:**  
    Ensure your robot class implements all core methods described in the [Robot Control Commands](#robot-control-commands) section above. These include connection handling, motion commands, state queries, and safety checks.

3. **Unit Consistency:**  
    All inputs and outputs must use the standard units defined in this guide (radians for joints, meters/radians for Cartesian positions).

4. **Document Manufacturer-Specific Details:**  
    Add in-line comments and README documentation for any manufacturer-specific logic, quirks, or references to official documentation. This helps future contributors understand your implementation.

5. **Testing:**  
    Test your integration using virtual or low-power modes first. Validate all commands and error handling before submitting.

6. **Code Quality:**  
    Run formatting and type checks as described in the [Linting and Code Quality](#notes-for-contributors) section.

> For a minimal working example, see [`BlankRobot`](armctl/_blank/robot.py).  
> When adding a new robot, include links to relevant documentation and clearly comment any non-standard behavior.

## Notes for Contributors

✅ **Safety:**  
Always test new motion commands on virtual or low-power modes first.

✅ **Docs:**  
Update this guide or relevant docstrings if you change command interfaces. Additionally, when adding a new manufacturer integration, include links to relevant source documentation in in-line comments and/or the README inside the added manufacturer folder. This helps future contributors understand implementation details and reference official resources easily.

✅ **Linting and Code Quality:**

Please ensure your code adheres to the project's formatting and quality standards before submitting a pull request.

**Setup:**

```bash
python -m venv .venv
source .venv/bin/activate
pip install poetry
poetry install --with dev
```

**Formatting Code:**

To ensure consistency and code quality, run the following commands before submitting your changes:

```bash
uv run ruff format .
```

> All code must be properly formatted and pass type checks. Please resolve any issues reported by these tools prior to opening a pull request.

✅ **(Optional) Running Tests Locally:**

While CI/CD automation will run tests on your pull request, you can speed up debugging by running the test suite locally:

```bash
uv run pytest tests
```

This is optional, but helps catch issues before submitting your pull request.
