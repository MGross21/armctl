from templates import SocketController as SCT
import asyncio

class Vention(SCT):
    def __init__(self, ip:str="192.168.7.2", port:int=9999):
        super().__init__(ip, port)

    async def connect(self):
        await super().connect()
        assert await self.send_command("isReady") == "MachineMotion is Ready = true"
        return 
    
    async def sleep(self, seconds): 
        await asyncio.sleep(seconds)

    async def home(self): 
        command = ""
        return await self.send_command(command)

    async def move_joints(self, joint_positions:list[float],*args, **kwargs):
        """Sets the current position of an axis to a new value (mm)."""
        match(len(joint_positions)):
            case 1:
                joint_positions.extend([0,0])
            case 2:
                joint_positions.append(0)
            case 3:
                pass
            case _:
                raise ValueError("Joint positions be [1,2,3] in size")
        
        # lambda functions
        command = (lambda a: "SET im_set_controller_pos_axis_{}/0/".format(a))
        if axis:
            return await self.send_command(command(axis))
        else:
            # set all axis
            return [clean_response(await self.send_command(command(i))) for i in valid_axis]  
        

    async def get_joint_positions(self, *args, **kwargs):
        axis = kwargs.get("axis")
        valid_axis = [1,2,3]
        if axis not in valid_axis and axis is not None:
            raise ValueError("Axis must be [1,2,3,None]")
        
        # lambda functions
        clean_response = (lambda r: float(r.strip("(<>)")))
        command = (lambda a: "GET im_get_controller_pos_axis_{}".format(a))
        if axis:
            return clean_response(await self.send_command(command(axis)))
        else:
            # set all axis
            return [clean_response(await self.send_command(command(i))) for i in valid_axis] 

    async def move_cartesian(self, robot_pose, *args, **kwargs): 
        return ImportWarning("Not implemented")

    async def get_cartesian_position(self):
        return ImportWarning("Not implemented")

    async def stop_motion(self): pass

    async def get_robot_state(self): pass