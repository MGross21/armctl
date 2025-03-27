from templates import SocketController as SCT, Commands
import asyncio
import numpy as np

class ElephantRobotics(SCT, Commands):
    def __init__(self, ip:str, port:int):
        super().__init__(ip, port)
        self.isConnected = False
    
        self.HOME_POSITION = [0,-90, 90,-90,-90,0]
        self.JOINT_RANGES = [
            (-180.00, 180.00),
            (-270.00, 90.00),
            (-150.00, 150.00),
            (-260.00, 80.00),
            (-168.00, 168.00),
            (-174.00, 174.00)
        ]
        self.DOF = len(self.JOINT_RANGES)

    async def connect(self):
        await super().connect() # Socket Connection

        assert await self.send_command("power_on()") == "power_on:[ok]" # Power on the robot
        assert await self.send_command("state_on()") == "state_on:[ok]" # enable the system
        self.isConnected = True
    
    async def disconnect(self):
        await self.stop_motion() # Stop any ongoing motion
        # assert await self.send_command("state_off()") == "state_off:[ok]" # Shut down the system, but the robot is still powered on
        # assert await self.send_command("power_off()") == "power_off:[ok]" # Power off the robot
        await super().disconnect() # Socket disconnection
        self.isConnected = False

    async def _waitforfinish(self):
        while True:
            if await self.send_command("wait_command_done()", timeout=60) == "wait_command_done:0":
                break
            await asyncio.sleep(0.25)
    
    async def sleep(self, seconds):
        await self.send_command(f"wait({seconds})")
        asyncio.sleep(seconds)

    async def home(self):
        await self.move_joints(ElephantRobotics.HOME_POSITION, speed=500)
    
    async def move_joints(self, joint_positions, *args, **kwargs):
        """
        Move the robot to the specified joint positions.
        
        Parameters
        ----------
        joint_positions : list of float
            Joint positions in degrees [j1, j2, j3, j4, j5, j6].
        speed : int, optional
            Speed of the movement, range 0 ~ 2000 (default: 200).
        DOF : int, optional
            Degrees of freedom (default: 6).
        """

        if type(joint_positions) != np.array:
            joint_positions = np.array(joint_positions)
        
        if len(joint_positions) != kwargs.get("DOF", 6):
            raise ValueError("Joint positions must have 6 elements")
    
        for i, (low, high) in enumerate(self.JOINT_RANGES):
            if not (low <= joint_positions[i] <= high):
                raise ValueError(f"Joint {i+1} angle out of range: {low} ~ {high}")

        speed = kwargs.get("speed", 200)
        if not (0 <= speed <= 2000):
            raise ValueError("Speed out of range: 0 ~ 2000")
        
        command = "set_angles"
        response =  await self.send_command(f"{command}({','.join(map(str, joint_positions))},{speed})")
        assert response == f"{command}:[ok]", f"Failed to move joints: {response}"


        while not np.allclose(await self.get_joint_positions(), joint_positions, atol=0.5):
            await asyncio.sleep(0.25)

    async def move_cartesian(self, robot_pose, *args, **kwargs)->None:
        if type(robot_pose) != np.array:
            robot_pose = np.array(robot_pose)

        speed = kwargs.get("speed", 200)
        if not (0 <= speed <= 2000):
            raise ValueError("Speed out of range: 0 ~ 2000")
        if len(robot_pose) != 6:
            raise ValueError("Robot pose must have 6 elements: [x, y, z, rx, ry, rz]")
        
        command = f"set_coords({','.join(map(str, robot_pose))},{speed})"
        
        assert await self.send_command(command) == "set_coords:[ok]"

        while not np.allclose(await self.get_cartesian_position(), robot_pose, atol=0.1):
            await asyncio.sleep(0.25)

    async def get_joint_positions(self):
        response = await self.send_command("get_angles()")
        if response == "[-1.0, -2.0, -3.0, -4.0, -1.0, -1.0]":
            raise ValueError("Invalid joint positions response from robot")
        joint_positions = list(map(float, response[response.index("[")+1:response.index("]")].split(","))) # From string list to float list
        return np.array(joint_positions).round(1)

    async def get_cartesian_position(self):
        response = await self.send_command("get_coords()") # [x, y, z, rx, ry, rz]
        if response == "[-1.0, -2.0, -3.0, -4.0, -1.0, -1.0]":
            raise ValueError("Invalid cartesian position response from robot")
        cartesian_position = list(map(float, response[response.index("[")+1:response.index("]")].split(","))) # From string list to float list
        return np.array(cartesian_position).round(2)

    async def stop_motion(self):
        command = "task_stop"
        response = await self.send_command(f"{command}()")

        if not response.startswith(f"{command}:"):
            raise SystemError(f"Unexpected response: {response}")

        result = response.split(":", 1)[1]

        if result != "[ok]":
            raise SystemError(result)
        return True

    async def get_robot_state(self):
        command = "check_running"
        response = await self.send_command(f"{command}()")

        if not response.startswith(f"{command}:"):
            raise SystemError(f"Unexpected response format: {response}")

        status = response.partition(":")[2]  # Get everything after the colon

        if status == "1":
            return True
        elif status == "0":
            return False
        else:
            raise ValueError(f"Unknown robot state: {status}")