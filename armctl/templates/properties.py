from abc import ABC
from typing import List, ClassVar, Tuple


class Properties(ABC):
    """Base class for robot properties."""
    
    JOINT_RANGES: ClassVar[List[Tuple[float, float]]]
    """Joint position limits for each joint."""

    
    @property
    def DOF(self) -> int:
        """Degrees of freedom derived from joint ranges."""
        return len(self.JOINT_RANGES)

