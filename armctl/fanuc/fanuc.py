from armctl.templates import PLCController as PLC, Commands

# Non-Operational (1/31/2025)
class Fanuc(PLC, Commands):
    def __init__(self, ip:str, port:int):
        super().__init__(ip, port)
        raise NotImplementedError(f"{self.__class__.__name__.upper()} is not yet supported.")

    async def move_joints(self, pos, speed=1.0):
        return await self.send_command({"type": "move_joints", "positions": pos, "speed": speed})

    async def move_cartesian(self, pose, speed=1.0):
        return await self.send_command({"type": "move_cartesian", "position": pose, "speed": speed})

    async def get_joint_positions(self):
        return await self.send_command({"type": "get_joint_positions"})

    async def get_cartesian_position(self):
        return await self.send_command({"type": "get_cartesian_position"})

    async def stop_motion(self):
        return await self.send_command({"type": "stop"})

    async def get_robot_state(self):
        return await self.send_command({"type": "get_state"})
