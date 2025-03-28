import asyncio
from . import (
    Dobot, 
    ElephantRobotics, Pro600, 
    UniversalRobotics, UR5, 
    Fanuc, 
    Vention
)

async def vention_ur5():

    async with Vention() as vention, UR5() as ur5:
        await vention.get_robot_state()
        await ur5.get_robot_state()
        
        await vention.home()
        await ur5.home()

        await vention.move_joints(100)
        await vention.home()

async def mycobot():
    async with Pro600() as pro600:
        await pro600.get_robot_state()
        await pro600.home()
        await pro600.move_cartesian([-132,-500,-70 ,0,0,0])
        

if __name__ == "__main__":
    try:
        asyncio.run(vention_ur5())
    except KeyboardInterrupt:
        print("Program terminated by user")
    except Exception as e:
        print(e)

    # print(AgnosticController.supported_manufacturers())


    # (ElephantRobotics,"192.168.1.159", 5001)
    # async with AgnosticController(UR5,"192.168.1.111", 30_002) as robot:
    # async with UR5("192.168.1.111", 30_002) as robot:
    #     # await robot.home()
    #     await robot.move_cartesian([-132,-500,-70 ,0,0,0])