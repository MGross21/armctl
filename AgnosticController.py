from .Templates import SocketControllerTemplate as SCT
from . import( ElephantRobotics, MyCobotPro600,
                                        Fanuc, 
                                        UniversalRobotics, 
                                        DobotRobotics)

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
    async with AgnosticController(ElephantRobotics,"192.168.1.159", 5001) as robot:
        # await robot.home()
        await robot.get_cartesian_position()


if __name__ == "__main__":
    # try:
    #     asyncio.run(main())
    # except KeyboardInterrupt:
    #     print("Program terminated by user")
    # except Exception as e:
    #     print(e)
    #     print("An error occurred")

    print(AgnosticController.supported_manufacturers())