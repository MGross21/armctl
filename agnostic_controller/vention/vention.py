from templates import SocketController as SCT
import asyncio

class Vention(SCT):
    def __init__(self, ip:str="192.168.7.2", port:int=9999):
        super().__init__(ip, port)

    async def connect(self):
        await super().connect()
        assert await self.send_command("isReady") == "MachineMotion is Ready = true"
        # Check E-Stop status
        if await self.send_command("estop/status") == "true":
            assert await self.send_command("estop/release/request") == "Ack estop/release/request", "Failed to release E-Stop"
    
    async def sleep(self, seconds): 
        await asyncio.sleep(seconds)

    async def home(self): 
        assert await self.send_command("im_home_axis_all", timeout=10) == "MachineMotion im_home_axis_all = completed", "Failed to home robot"

    async def move_joints(self, joint_positions:list[float],*args, **kwargs) -> None:
        """Sets the current position of an axis to a new value (mm)."""
        if isinstance(joint_positions, (int, float)):
            joint_positions = [joint_positions]
        
        if len(joint_positions) not in [1, 2, 3]:
            raise ValueError("Joint positions must be a list of 1-3 floats")
        
        # lambda functions
        command = (lambda ax,val: "SET im_set_controller_pos_axis_{}/{}/".format(ax, val))

        response = [await self.send_command(command(i, joint_positions[i])) for i in range(len(joint_positions))]

        assert all([r == "Ack" for r in response]), "Failed to move joints"

        while True:
            if await self.send_command("isMotionCompleted") == "MachineMotion isMotionCompleted = true":
                break
            await asyncio.sleep(0.1)
        

    async def get_joint_positions(self, axis=None)->list[float] | float:
        """Gets the current position of an axis or all axis."""
        valid_axes = [1, 2, 3]
        if axis and axis not in valid_axes:
            raise ValueError("Axis must be 1, 2, 3, or None for all axes")

        async def response(ax):
            return float((await self.send_command(f"GET im_get_controller_pos_axis_{ax}",timeout=10)).strip("(<>)"))

        return await response(axis) if axis else [await response(ax) for ax in valid_axes]

    async def move_cartesian(self, robot_pose, *args, **kwargs): 
        raise NotImplementedError()

    async def get_cartesian_position(self):
        raise NotImplementedError()

    async def stop_motion(self):
        assert await self.send_command("estop/trigger/request") == "Ack estop/trigger/request", "Failed to stop motion"
        assert await self.send_command("estop/systemreset/request") == "Ack estop/systemreset/request", "Failed to reset system"

    async def get_robot_state(self):
        raise NotImplementedError()