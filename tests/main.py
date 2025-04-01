import time
import sys
from pathlib import Path

# Add the parent directory of the current script to the system path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agnostic_controller import (
    Dobot, 
    ElephantRobotics, Pro600, 
    UniversalRobotics, UR5, 
    Fanuc, 
    Vention
)

def vention_ur5():

    with Vention() as vention:
        vention.home()
        # time.sleep()
        # vention.reset()
        # vention.move_joints(200, speed=2_500, acceleration=500, move_type='abs') # 2500/500 is decent speed
        # # vention.reset()


        
        # # ur5.get_robot_state()
        
        # # await vention.home()
        # # # await ur5.home()


def mycobot():
    with Pro600() as pro600:
        pro600.get_cartesian_position()
        pro600.home()
        pro600.move_cartesian([-132,-500,-70 ,0,0,0],speed=750)
        

if __name__ == "__main__":
    vention_ur5()