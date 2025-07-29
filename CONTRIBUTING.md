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

1. Establish Python or network connection (**Super Connect**)
2. Power on the robot
3. Check and reset emergency stop status if needed
4. Enable robot drives
5. Perform any required initialization (e.g. homing, zeroing)

### Disconnect

Sequence to safely disconnect:

1. Stop any ongoing motion (preferably with a controlled deceleration)
2. Optionally disable robot drives (use with caution)
3. Optionally power off the robot (use with caution)
4. Close Python/network connection (**Super Disconnect**)

### Move Joints

#### Checks

* Ensure provided joint positions array matches robot DOF:  
    `len(joint_positions) == len(joint_min) == len(joint_max)`
* Confirm velocities and accelerations are within robot limits
* Validate joint limits:  
    `joint_min[i] <= joint_positions[i] <= joint_max[i]`

#### Execution

1. Format and send the command
2. Receive and parse response (if applicable)
3. Assert valid or expected response
4. Return response (or confirmation)

### Move Cartesian

#### Checks

* Ensure pose is a 6-element list or array:  
    `[x, y, z, rx, ry, rz]`
* Verify rotation values:  
    `abs(rx), abs(ry), abs(rz) <= 2π`
* Validate speed and acceleration constraints
* Ensure pose is within the robot's reachable workspace (via internal IK or explicit robot checks)

#### Execution

1. Format and send the Cartesian move command
2. Receive and parse response
3. Assert validity
4. Return response

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

#### If Robot Supports Native Sleep:

1. Send sleep command (e.g. to enter idle or low-power state)
2. Parse acknowledgement
3. Return confirmation

#### If Not Supported:

* Use Python's `time.sleep(seconds)` to pause execution.

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
poetry run black . \
poetry run isort . \
poetry run ruff . \
poetry run mypy armctl
```

> All code must be properly formatted and pass type checks. Please resolve any issues reported by these tools prior to opening a pull request.
