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
        # pos = vention.get_joint_positions()
        # pos[0] += 500
        # vention.move_joints(pos[0], speed=500, move_type='rel')
        # print(pos)
        # # vention.reset()


        
        # # ur5.get_robot_state()
        
        # # await vention.home()
        # # # await ur5.home()

        # pos[0] += 2500
        # vention.move_joints(pos)
        print("Vention moved to position:", vention.get_joint_positions())
        # time.sleep(5)
        # del pos


def mycobot():
    with Pro600() as pro600:
        pro600.get_cartesian_position()
        pro600.home()
        pro600.move_cartesian([-132,-500,-70 ,0,0,0],speed=750)
        

if __name__ == "__main__":
    vention_ur5()