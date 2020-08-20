from time import perf_counter as clock
from sl1m.generic_solver import solve_L1_combinatorial_biped
from sl1m.planner_scenarios.talos.problem_definition_talos import generate_problem
from talos_rbprm.talos import Robot as Talos
import sl1m.tools.plot_tools as plot
import numpy as np

COSTS = {"step_size": None, "final_com": None, "effector_positions": None, "coms": None, "posture": None}
GAIT = [0, 1]

### HARDCODED SURFACES, REPLACE IT WITH PATH PLANNING ####
floor = [[-0.30, 0.54, 0.], [-0.1,  0.54, 0.], [-0.1, -0.46, 0.], [-0.30, -0.46, 0.], ]
step1 = [[0.01, 0.54, 0.1], [0.31,  0.54, 0.1], [0.31, -0.46, 0.1], [0.01, -0.46, 0.1], ]
step2 = [[0.31, 0.54, 0.2], [0.61,  0.54, 0.2], [0.61, -0.46, 0.2], [0.31, -0.46, 0.2], ]
step3 = [[0.61, 0.54, 0.3], [0.91,  0.54, 0.3], [0.91, -0.46, 0.3], [0.61, -0.46, 0.3], ]
step4 = [[0.91, 0.54, 0.4], [1.21,  0.54, 0.4], [1.21, -0.46, 0.4], [0.91, -0.46, 0.4], ]
step5 = [[1.24, 0.54, 0.5], [1.51,  0.54, 0.5], [1.51, -0.46, 0.5], [1.24, -0.46, 0.5], ]
step6 = [[1.55, 0.54, 0.6], [1.81,  0.54, 0.6], [1.81, -0.46, 0.6], [1.55, -0.46, 0.6], ]
step7 = [[1.51, -0.46, 0.6], [1.81, -0.46, 0.6], [1.81, -0.76, 0.6], [1.51, -0.76, 0.6], ]
bridge = [[1.51, -0.46, 0.6], [1.51, -0.76, 0.6], [-1.49, -0.76, 0.6], [-1.49, -0.46, 0.6], ]
platfo = [[-1.49, -0.35, 0.6], [-1.49, -1.06, 0.6], [-2.49, -1.06, 0.6], [-2.49, -0.35, 0.6], ]
slope = [[-1.49, -0.06, 0.6], [-1.49, 1.5, 0.], [-2.49, 1.5, 0.], [-2.49, -0.06, 0.6], ]
rub2 = [[-2.11, 0.19, 0.05], [-2.45, 0.19, 0.05],  [-2.45, 0.53, 0.05], [-2.11, 0.53, 0.05], ]
rub3 = [[-1.91, -0.15, 0.1], [-2.25, -0.15, 0.1],  [-2.25, 0.15, 0.1], [-1.91, 0.15, 0.1], ]
rub4 = [[-1.69, 0.19, 0.15], [-2.03, 0.19, 0.15],  [-2.03, 0.53, 0.15], [-1.69, 0.53, 0.15], ]
rub5 = [[-1.49, -0.15, 0.2], [-1.83, -0.15, 0.2],  [-1.83, 0.18, 0.2], [-1.49, 0.18, 0.2], ]
rub6 = [[-1.29, 0.19, 0.2], [-1.63, 0.19, 0.2],  [-1.63, 0.53, 0.2], [-1.29, 0.53, 0.2], ]
rub7 = [[-1.09, -0.15, 0.15], [-1.43, -0.15, 0.15],  [-1.43, 0.18, 0.15], [-1.09, 0.18, 0.15], ]
rub75 = [[-0.89, 0.19, 0.1], [-1.23, 0.19, 0.1],  [-1.23, 0.53, 0.1], [-0.89, 0.53, 0.1], ]
rub8 = [[-0.89, -0.15, 0.025], [-1.02, -0.15, 0.025],  [-1.02, 0.18, 0.025], [-0.89, 0.18, 0.025], ]
rub9 = [[-0.35, -0.15, 0.025], [-0.86, -0.15, 0.025], [-0.86, 0.52, 0.025], [-0.35, 0.52, 0.025], ]
rub8 = [[-0.89, -0.15, 0.05], [-1.02, -0.15, 0.05],  [-1.02, 0.18, 0.05], [-0.89, 0.18, 0.05], ]
rub9 = [[-0.45, -0.15, 0.05], [-0.86, -0.15, 0.05], [-0.86, 0.52, 0.05], [-0.45, 0.52, 0.05], ]

all_surfaces = [floor, step1, step2, step3, step4, step5, step6, step7,
                bridge, platfo, rub8, rub9, rub7, rub75, rub6, rub5, rub4, rub3, rub2]

arub9 = np.array(rub9).T
arub8 = np.array(rub8).T
arub75 = np.array(rub75).T
arub7 = np.array(rub7).T
arub6 = np.array(rub6).T
arub5 = np.array(rub5).T
arub4 = np.array(rub4).T
arub3 = np.array(rub3).T
arub2 = np.array(rub2).T
afloor = np.array(floor).T
astep1 = np.array(step1).T
astep2 = np.array(step2).T
astep3 = np.array(step3).T
astep4 = np.array(step4).T
astep5 = np.array(step5).T
astep6 = np.array(step6).T
astep7 = np.array(step7).T
abridge = np.array(bridge).T
aplatfo = np.array(platfo).T
aslope = np.array(slope).T

allrub = [arub2, arub3, arub5, arub4, arub6, arub7, arub75, arub9]

surfaces = [[arub2, arub3], [arub3, arub2], [arub4, arub3, arub5], [arub5, arub4, arub3, arub6], [arub6], [arub7], [arub75], [
    arub9, afloor], [arub9, afloor], [afloor, arub9], [astep1], [astep2], [astep3], [astep4], [astep5], [astep6], [astep6]]
### END HARDCODED SURFACES ####

if __name__ == '__main__':
    t_init = clock()
    R = []
    for i in range(len(surfaces)):
        R.append(np.identity(3))
    t_1 = clock()

    initial_contacts = [np.array([-2.7805096486250154, 0.335, 0.]), np.array([-2.7805096486250154, 0.145, 0.])]
    t_2 = clock()

    talos = Talos()
    pb = generate_problem(talos, R, surfaces, GAIT, initial_contacts, eq_as_ineq=False)
    t_3 = clock()

    result = solve_L1_combinatorial_biped(pb, surfaces, costs=None)
    t_end = clock()

    print("Optimized number of steps:              ", pb["n_phases"])
    print("Total time is:                          ", 1000. * (t_end-t_init))
    print("Computing the surfaces takes            ", 1000. * (t_1 - t_init))
    print("Computing the initial contacts takes    ", 1000. * (t_2 - t_1))
    print("Generating the problem dictionary takes ", 1000. * (t_3 - t_2))
    print("Solving the problem takes               ", 1000. * (t_end - t_3))
    print("The LP and QP optimizations take        ", result.time)

    ax = plot.draw_scene(surfaces, GAIT)
    plot.plot_initial_contacts(initial_contacts, ax=ax)
    plot.plot_planner_result(result.coms, result.moving_foot_pos, result.all_feet_pos, ax, True)
