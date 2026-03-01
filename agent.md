# Agent Notes: Adding a New Robot

This file is intentionally brief. For detailed implementation info, see existing project docs and code.

## Before You Start

Read these first for required context:

- [CONTRIBUTING.md](CONTRIBUTING.md) — Project conventions, control flow, unit standards
- [README.md](README.md) — Public API style and usage patterns

## Implementation Steps

1. Use the blank robot template (`armctl/_blank/robot.py`) as your structural baseline
2. Choose communication layer: SocketController, SerialController, or PLCController from the templates directory
3. Ensure all abstract methods and properties from inherited base classes (Commands, Properties, and communication layer) are fully implemented
4. Study existing robot implementations in the `armctl/` directory for API consistency patterns
5. Keep conversions and checks aligned with project-wide conventions from CONTRIBUTING.md
6. Add/update tests for your integration

## Key Decisions

**Dependencies:** Prefer official first-party robot SDKs when available and stable. Use custom implementation if no suitable first-party option exists.

**Documentation:** As you discover manufacturer documentation/specs/resources, add links to the robot's folder README or inline code comments. Keep it minimal—only include links directly relevant to implementation and maintenance.