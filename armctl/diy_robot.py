"""
This module provides the DIYRobot factory class for creating custom robotic platforms
with pick-and-choose communication systems.

The DIYRobot class allows users to:
1. Create a blank factory instance: Robot = DIYRobot()
2. Configure communication dynamically: Robot(SocketController, "192.168.1.1", 8080)
3. Access basic communication methods: connect(), disconnect(), send_command()
"""

from typing import Union, Any, Type
from .templates.communication import Communication


class DIYRobot:
    """
    A factory class for creating custom robotic platforms with flexible communication.
    
    This class provides a blank factory that can be configured with any communication
    method via the __call__ function. It does not inherit from Communication or Commands
    initially, but provides the basic communication interface after configuration.
    
    Example Usage:
    -------------
    from armctl import DIYRobot
    from armctl.templates import SocketController
    
    # Create blank factory
    robot = DIYRobot()
    
    # Configure communication
    robot(SocketController, "192.168.1.100", 8080)
    
    # Use basic communication methods
    robot.connect()
    response = robot.send_command("custom_command")
    robot.disconnect()
    """
    
    def __init__(self):
        """
        Initialize a blank DIY robot factory.
        
        No communication or command inheritance is established at this point.
        The robot must be configured using the __call__ method before use.
        """
        self._communication_instance = None
        self._is_configured = False
    
    def __call__(self, communication_class: Type[Communication], *args, **kwargs) -> None:
        """
        Configure the robot with a specific communication method and parameters.
        
        Parameters
        ----------
        communication_class : Type[Communication]
            A Communication subclass (e.g., SocketController, SerialController)
        *args
            Positional arguments to pass to the communication class constructor
        **kwargs
            Keyword arguments to pass to the communication class constructor
            
        Example:
        --------
        robot(SocketController, "192.168.1.100", 8080)
        robot(SerialController, "/dev/ttyUSB0", baudrate=115200)
        """
        if not issubclass(communication_class, Communication):
            raise TypeError(f"communication_class must be a subclass of Communication, got {communication_class}")
        
        # Create instance of the communication class with provided arguments
        self._communication_instance = communication_class(*args, **kwargs)
        self._is_configured = True
    
    def _ensure_configured(self):
        """Ensure the robot has been configured with a communication method."""
        if not self._is_configured or self._communication_instance is None:
            raise RuntimeError("DIYRobot must be configured with a communication method first. "
                             "Use robot(CommunicationClass, *args, **kwargs) to configure.")
    
    def connect(self) -> None:
        """
        Connect to the robot using the configured communication method.
        
        Raises:
        -------
        RuntimeError
            If the robot has not been configured with a communication method.
        """
        self._ensure_configured()
        return self._communication_instance.connect()
    
    def disconnect(self) -> None:
        """
        Disconnect from the robot using the configured communication method.
        
        Raises:
        -------
        RuntimeError
            If the robot has not been configured with a communication method.
        """
        self._ensure_configured()
        return self._communication_instance.disconnect()
    
    def send_command(self, command: Union[str, dict], timeout: float = 5.0, **kwargs) -> Union[dict, str]:
        """
        Send a command to the robot using the configured communication method.
        
        This is the primary method for custom robot control. Engineers can use this
        to send any custom commands specific to their robotic platform.
        
        Parameters
        ----------
        command : Union[str, dict]
            The command to send to the robot
        timeout : float, optional
            Timeout for the command in seconds (default: 5.0)
        **kwargs
            Additional arguments to pass to the communication's send_command method
            
        Returns
        -------
        Union[dict, str]
            The response from the robot
            
        Raises:
        -------
        RuntimeError
            If the robot has not been configured with a communication method.
        """
        self._ensure_configured()
        return self._communication_instance.send_command(command, timeout, **kwargs)
    
    def __enter__(self):
        """Context manager support for automatic connection management."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure disconnection when leaving the context."""
        self.disconnect()
    
    @property
    def is_configured(self) -> bool:
        """Check if the robot has been configured with a communication method."""
        return self._is_configured
    
    @property
    def communication_type(self) -> str:
        """Get the type of communication method configured, if any."""
        if self._is_configured and self._communication_instance:
            return self._communication_instance.__class__.__name__
        return "Not configured"