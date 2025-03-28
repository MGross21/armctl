from templates import SocketController as SCT, Commands

# Non-Operational (1/31/2025)
class Fanuc(SCT, Commands):
    def __init__(self, ip:str, port:int):
        super().__init__(ip, port)

    async def move_joints(self, joint_positions, speed=1.0):
        return await self.send_command({"type": "move_joints", "positions": joint_positions, "speed": speed})

    async def move_cartesian(self, x, y, z, rx, ry, rz, speed=1.0):
        return await self.send_command({"type": "move_cartesian", "position": [x, y, z, rx, ry, rz], "speed": speed})

    async def get_joint_positions(self, *args, **kwargs):
        return await self.send_command({"type": "get_joint_positions"})

    async def get_cartesian_position(self, *args, **kwargs):
        return await self.send_command({"type": "get_cartesian_position"})

    async def stop_motion(self):
        return await self.send_command({"type": "stop"})

    async def get_robot_state(self):
        return await self.send_command({"type": "get_state"})
