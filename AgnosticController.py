from Templates import SocketControllerTemplate as SCT
from DobotRobotics import DobotRobotics
from ElephantRobotics import ElephantRobotics, MyCobotPro600
from UniversalRobotics import UniversalRobotics
from Fanuc import Fanuc

import asyncio 

class AgnosticController:
    controllers = {}
    for manufacturer in SCT.__subclasses__():
        controllers[manufacturer.__name__.lower()] = manufacturer

    def __init__(self, manufacturer, ip, port):
        if isinstance(manufacturer, str):
            manufacturer = manufacturer.strip().lower()
            if (manufacturer not in self.controllers):
                raise ValueError(f"Unsupported manufacturer: {manufacturer}")
            self.controller = self.controllers[manufacturer](ip, port)
        
        elif issubclass(manufacturer, SCT):
            self.controller = manufacturer(ip, port)

        else:
            raise ValueError(f"Invalid manufacturer type. Supported types: str, ControllerTemplate subclasses ({', '.join(self.controllers.keys())})")
        
    @staticmethod
    def supported_manufacturers():
        return list(AgnosticController.controllers.keys())

    async def __aenter__(self):
        await self.controller.connect()
        return self.controller

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.controller.disconnect()


async def main():
    # (ElephantRobotics,"192.168.1.159", 5001)
    async with AgnosticController(UniversalRobotics,"192.168.1.111", 30_002) as robot:
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