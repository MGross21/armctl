# Agent Notes: Adding a New Robot

This file is intentionally brief. For implementation details, rely on existing project docs and code.

## Where to start

- Read [CONTRIBUTING.md](CONTRIBUTING.md) for project conventions, control flow expectations, and unit standards.
- Read [README.md](README.md) for the public API style and usage patterns expected by users.

## Main code locations to inspect

- Template starting point: [armctl/_blank/robot.py](armctl/_blank/robot.py)
- Existing robot implementations.
- Shared interfaces/helpers: [armctl/templates](armctl/templates)
- Validation and utility helpers: [armctl/utils](armctl/utils)

## Practical workflow (high-level)

1. Use the blank robot template as your structural baseline.
2. Choose the correct communication layer from templates (socket, serial, or PLC).
3. Match method names and behavior to existing robot modules so API usage remains consistent.
4. Keep conversions and checks aligned with project-wide conventions from the contributing guide.
5. Add/update tests in [tests](tests) for any new integration behavior.

## Dependency preference

- Prefer official first-party robot dependencies/SDKs when they are available, stable, and compatible with this project.
- If no suitable first-party dependency exists, or if it cannot support required behavior safely/reliably, implement the integration directly with a custom protocol/client as appropriate.
- Keep any dependency choice minimal.