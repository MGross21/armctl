from templates import SocketController as SCT

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