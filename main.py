import asyncio
from dobot import Dobot
from elephant_robotics import ElephantRobotics, Pro600
from universal_robotics import UniversalRobotics, UR5
from fanuc import Fanuc
from AgnosticController import AgnosticController

async def main():
    # (ElephantRobotics,"192.168.1.159", 5001)
    # async with AgnosticController(UR5,"192.168.1.111", 30_002) as robot:
    async with UR5("192.168.1.111", 30_002) as robot:
        # await robot.home()
        await robot.move_cartesian([-132,-500,-70 ,0,0,0])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program terminated by user")
    except Exception as e:
        print(e)
        print("An error occurred")

    # print(AgnosticController.supported_manufacturers())