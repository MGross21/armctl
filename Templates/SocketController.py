import asyncio
import socket
import json
import logging
from abc import ABC, abstractmethod

# Define custom logging levels
SEND_LEVEL = logging.INFO + 1
RECIEVE_LEVEL = logging.INFO + 2

logging.addLevelName(SEND_LEVEL, "SEND")
logging.addLevelName(RECIEVE_LEVEL, "RECV")

def send(self, message, *args, **kws):
    if self.isEnabledFor(SEND_LEVEL):
        self._log(SEND_LEVEL, message, args, **kws)

def recieve(self, message, *args, **kws):
    if self.isEnabledFor(RECIEVE_LEVEL):
        self._log(RECIEVE_LEVEL, message, args, **kws)

logging.Logger.send = send
logging.Logger.recieve = recieve

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

class SocketControllerTemplate(ABC):
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.disconnect()

    def __format__(self, format_spec):
        if format_spec == "f":
            return f"{self.__class__.__name__}({self.ip}:{self.port})"
        else:
            return super().__format__(format_spec)

    def __init__(self, ip, port):
        self.ip, self.port, self.socket = ip, port, None
        self.isConnected = False

    async def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            await asyncio.get_event_loop().sock_connect(self.socket, (self.ip, self.port))
            logger.info(f"Connected to {self:f}")
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise ConnectionError(f"Failed to connect to {self:f}")
        self.isConnected = True

    async def disconnect(self):
        if self.socket:
            self.socket.close()
            self.socket = None
            logger.info("Disconnected from robot")
        self.isConnected = False

    async def send_command(self, command, timeout=5.0):
        if not self.socket:
            raise ConnectionError(f"Not connected to {self:f}")
        
        try:
            logger.send(f"{self:f}: \t{command}")
            
            if isinstance(command, dict):
                command = json.dumps(command).encode('utf-8')
                response_format = 'dict'
            elif isinstance(command, str):
                command = command.encode('utf-8')
                response_format = 'str'
            elif isinstance(command, bytes):
                response_format = 'bytes'
            else:
                raise TypeError("Unsupported command type")
            
            await asyncio.wait_for(self._send(command), timeout=timeout)
            response = await asyncio.wait_for(self._receive(), timeout=timeout)
            
            if response_format == 'dict':
                decoded_response = json.loads(response.decode('utf-8'))
            elif response_format == 'str':
                decoded_response = response.decode('utf-8')
            elif response_format == 'bytes':
                decoded_response = response
            else:
                raise ValueError("Unsupported response format")
            
            logger.recieve(f"{self:f}: \t{decoded_response}")
            return decoded_response
    
        except asyncio.TimeoutError:
            logger.error("Command timed out")
            raise TimeoutError("Command timed out")
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            raise ConnectionError("Failed to send command to the robot")
        finally:
            print()

    async def _send(self, data):
        await asyncio.get_event_loop().sock_sendall(self.socket, data)

    async def _receive(self, buffer_size=1024):
        return await asyncio.get_event_loop().sock_recv(self.socket, buffer_size)
    
    @abstractmethod
    async def sleep(self, seconds): pass

    @abstractmethod
    async def home(self): pass

    @abstractmethod
    async def move_joints(self, joint_positions,*args, **kwargs): pass

    @abstractmethod
    async def get_joint_positions(self): pass

    @abstractmethod
    async def move_cartesian(self, robot_pose, *args, **kwargs): pass

    @abstractmethod
    async def get_cartesian_position(self): pass

    @abstractmethod
    async def stop_motion(self): pass

    @abstractmethod
    async def get_robot_state(self): pass

    async def custom_command(self, command):
        return await self.send_command(command)