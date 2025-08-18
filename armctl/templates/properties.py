from abc import ABC
from typing import List, ClassVar


class Properties(ABC):
    """Base class for robot properties."""
    
    JOINT_LIMITS: ClassVar[List[float]]
    
    @property
    def DOF(self) -> int:
        """Degrees of freedom of the robot."""
        return len(self.JOINT_LIMITS)

