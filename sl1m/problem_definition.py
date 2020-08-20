from sl1m.constants_and_tools import default_transform_from_pos_normal, convert_surface_to_inequality
from sl1m.tools.obj_to_constraints import load_obj, as_inequalities, rotate_inequalities
import numpy as np

# General sl1m problem definition
#
# pb["n_effectors"]: number of effectors
# pb["p0"]:      initial feet positions
# pb["c0"]:      initial com positions
# pb["nphases"]: number of phases
# pb["phaseData"][i]["Moving"]: moving effector in phase i
# pb["phaseData"][i]["K"]: Com constraints for phase i, for each limb and each surface
# pb["phaseData"][i]["allRelativeK"]: Relative constraints for phase i for each limb and each surface
# pb["phaseData"][i]["rootOrientation"]: root orientation for phase i
# pb["phaseData"][i]["S"]: surfaces of phase i


def generate_problem(Robot, R, surfaces, gait, p0, c0):
    """
    Build a SL1M problem for the Mixed Integer formulation,
    with all the kinematics and foot relative position constraints required
    :param Robot: an rbprm robot
    :param R: a list of rotation matrix for the base of the robot (must be the same size as surfaces)
    :param surfaces: A list of surfaces candidates, with one set of surface candidates for each phase
    :param gait: The gait of the robot (list of id of the moving foot)
    :param p0: The initial positions of the limbs
    :param c0: The initial position of the com
    :return: a "res" dictionnary with the format required by SL1M
    """
    n_effectors = len(Robot.limbs_names)
    normals = [np.array([0, 0, 1]) for _ in range(n_effectors)]
    n_phases = len(surfaces)
    res = {"n_effectors": n_effectors, "p0": p0, "c0": c0, "n_phases": n_phases}
    res["phaseData"] = [{"Moving": gait[i % n_effectors],
                         "K": com_constraint(Robot, R[i], normals),
                         "allRelativeK": relative_constraint(Robot, R[i], normals),
                         "rootOrientation":R[i],
                         "S": [convert_surface_to_inequality(s, True) for s in surfaces[i]]} for i in range(n_phases)]
    return res


def com_constraint(Robot, rotation, normals):
    """
    Generate the constraints on the CoM position for all the effectors
    :param Robot:
    :param rotation: the rotation to apply to the constraints
    :param normals: the default contact normals of each effectors
    :return: a list of [A,b] inequalities, in the form Ax <= b
    """
    return [com_in_effector_frame_constraint(Robot, default_transform_from_pos_normal(np.zeros(3), normals[idx], rotation), idx) for idx in range(len(Robot.limbs_names))]


def com_in_effector_frame_constraint(Robot, transform, foot):
    """
    Generate the inequalities constraints for the CoM position given a contact position for one limb
    :param Robot:
    :param transform: Transformation to apply to the constraints
    :param foot: the Id of the limb used (see Robot.limbs_names list)
    :return: [A, b] the inequalities, in the form Ax <= b
    """
    limb_name = Robot.limbs_names[foot]
    filekin = Robot.kinematic_constraints_path + "/COM_constraints_in_" + \
        limb_name + "_effector_frame_quasi_static_reduced.obj"
    obj = load_obj(filekin)
    ine = rotate_inequalities(as_inequalities(obj), transform.copy())
    return ine.A, ine.b


def relative_constraint(Robot, rotation, normals):
    """
    Generate all the relative position constraints for all limbs
    :param Robot:
    :param rotation: the rotation to apply to the constraints
    :param normals: the default contact normals of each effectors
    :return: a list of [A,b] inequalities, in the form Ax <= b
    """
    transforms = [default_transform_from_pos_normal(np.zeros(3), normals[i], rotation)
                  for i in range(len(Robot.limbs_names))]
    res = []
    for foot, transform in enumerate(transforms):
        res += [[(other, foot_in_limb_effector_frame_constraint(Robot, transform, foot, other))
                 for other in range(len(Robot.limbs_names)) if other != foot]]
    return res


def foot_in_limb_effector_frame_constraint(Robot, transform, other, foot):
    """
    Generate the constraints for the position of a given effector, given another effector position
    :param Robot:
    :param transform: The transform to apply to the constraints
    :param other: the Id of the fixed limb (see Robot.limbs_names list)
    :param foot: the Id of the limb for which the constraint are build
    :return: [A, b] the inequalities, in the form Ax <= b
    """
    other_name = Robot.limbs_names[other]
    foot_name = Robot.dict_limb_joint[Robot.limbs_names[foot]]
    filekin = Robot.relative_feet_constraints_path + "/" + \
        foot_name + "_constraints_in_" + other_name + "_reduced.obj"
    obj = load_obj(filekin)
    ine = rotate_inequalities(as_inequalities(obj), transform.copy())
    return ine.A, ine.b
