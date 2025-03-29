import numpy as np
from scipy.interpolate import BarycentricInterpolator
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class IKSolver:
    def __init__(self, robot, lambda_factor=0.01, max_iter=1000, epsilon=1e-6):
        self.robot = robot
        self.lambda_factor = lambda_factor
        self.max_iter = max_iter
        self.epsilon = epsilon

    def jacobian(self, joint_angles):
        num_joints = len(joint_angles)
        jacobian = np.zeros((6, num_joints))
        for i in range(num_joints):
            delta_angle = np.zeros_like(joint_angles)
            delta_angle[i] = 1e-6
            fwd_kin_current = self.robot.forward_kinematics(joint_angles)
            fwd_kin_delta = self.robot.forward_kinematics(joint_angles + delta_angle)

            delta_position = fwd_kin_delta[:3] - fwd_kin_current[:3]
            delta_orientation = fwd_kin_delta[3:] - fwd_kin_current[3:]

            jacobian[:3, i] = delta_position / 1e-6
            jacobian[3:, i] = delta_orientation / 1e-6

        return jacobian

    def error_function(self, joint_angles, target_pose):
        target_position = target_pose[:3]  # [x, y, z]
        target_orientation = target_pose[3:]  # [roll, pitch, yaw]
        current_pose = self.robot.forward_kinematics(joint_angles)  # Returns [x, y, z, roll, pitch, yaw]
        
        # Unpack current pose
        current_position = current_pose[:3]  # [x, y, z]
        current_orientation = current_pose[3:]  # [roll, pitch, yaw]
        
        position_error = target_position - current_position
        orientation_error = target_orientation - current_orientation

        # Calculate total error as the sum of position and orientation errors
        total_error = np.linalg.norm(position_error) + np.linalg.norm(orientation_error)
        return total_error


    def solve(self, target_pose, initial_joint_angles):
        result = minimize(
            self.error_function, 
            initial_joint_angles, 
            args=(target_pose,), 
            method='BFGS',  
            options={'disp': False, 'maxiter': self.max_iter}
        )

        if result.success:
            return result.x
        else:
            raise RuntimeError("IK solver failed to converge")

class PathPlanner:
    def __init__(self, ik_solver, resolution=25):
        self.ik_solver = ik_solver
        self.resolution = resolution  # Number of waypoints in the path

    def plan_path(self, start_pose, end_pose):
        """
        Plan a smooth path using B-splines.
        
        :param start_pose: The start pose [x, y, z, roll, pitch, yaw]
        :param end_pose: The target pose [x, y, z, roll, pitch, yaw]
        :return: Joint space trajectory
        """
        # Generate intermediate target positions (waypoints)
        positions = np.linspace(start_pose[:3], end_pose[:3], self.resolution)
        orientations = np.linspace(start_pose[3:], end_pose[3:], self.resolution)

        # Solve IK for each waypoint
        joint_trajectory = []
        for i in range(self.resolution):
            target_pose = np.concatenate([positions[i], orientations[i]])
            joint_angles = self.ik_solver.solve(target_pose, np.zeros(self.ik_solver.robot.num_dof))
            joint_trajectory.append(joint_angles)

        # Smooth the trajectory with a B-spline
        joint_trajectory = np.array(joint_trajectory)
        smoothed_trajectory = self.smooth_trajectory(joint_trajectory)

        return smoothed_trajectory

    def smooth_trajectory(self, trajectory):
        """
        Apply a B-spline or cubic spline to smooth the trajectory.
        
        :param trajectory: Joint space trajectory
        :return: Smoothed joint space trajectory
        """
        smoothed_trajectory = np.zeros_like(trajectory)
        num_joints = trajectory.shape[1]

        for j in range(num_joints):
            interpolator = BarycentricInterpolator(np.arange(self.resolution), trajectory[:, j])
            smoothed_trajectory[:, j] = interpolator(np.linspace(0, self.resolution - 1, self.resolution))

        return smoothed_trajectory

    def plot_3d_trajectory(self, smoothed_trajectory):
        """
        Plot the 3D trajectory of the robot's end-effector.

        :param smoothed_trajectory: Joint space trajectory after smoothing
        """
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        # Simulate the end-effector position for visualization purposes
        x = smoothed_trajectory[:, 0]  # Example of joint positions (x-axis)
        y = smoothed_trajectory[:, 1]  # Example of joint positions (y-axis)
        z = smoothed_trajectory[:, 2]  # Example of joint positions (z-axis)

        ax.plot(x, y, z, label='End-Effector Path')
        ax.set_xlabel('X Position')
        ax.set_ylabel('Y Position')
        ax.set_zlabel('Z Position')

        ax.legend()
        plt.show()


# Example robot class with basic forward kinematics (dummy)
class Robot:
    def __init__(self, num_dof=6):
        self.num_dof = num_dof
    
    def forward_kinematics(self, joint_angles):
        x = np.sum(np.cos(joint_angles))  # Dummy position calculation
        y = np.sum(np.sin(joint_angles))  # Dummy position calculation
        z = np.sum(joint_angles)  # Just for illustration
        roll = pitch = yaw = 0  # Dummy orientation (could be calculated if needed)
        return np.array([x, y, z, roll, pitch, yaw])


# Example usage for a robot with arbitrary DOF:
robot = Robot(num_dof=10)  # Can be changed to any number of DOF
ik_solver = IKSolver(robot)
path_planner = PathPlanner(ik_solver)

# Define the start and end positions and orientations (dummy values)
start_pose = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])  # [x, y, z, roll, pitch, yaw]
end_pose = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0])  # [x, y, z, roll, pitch, yaw]

# Plan the path
smoothed_trajectory = path_planner.plan_path(start_pose, end_pose)

# Optionally, plot the 3D trajectory
path_planner.plot_3d_trajectory(smoothed_trajectory)

print("Smoothed trajectory:", smoothed_trajectory)
