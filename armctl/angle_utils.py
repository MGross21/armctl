import math


class AngleUtils:
    @staticmethod
    def to_degrees_joint(joint_positions):
        return [math.degrees(j) for j in joint_positions]

    @staticmethod
    def to_radians_joint(joint_positions):
        return [math.radians(j) for j in joint_positions]

    @staticmethod
    def to_degrees_cartesian(pose):
        return pose[:3] + [math.degrees(a) for a in pose[3:]]

    @staticmethod
    def to_radians_cartesian(pose):
        return pose[:3] + [math.radians(a) for a in pose[3:]]
