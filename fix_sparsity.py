import numpy as np


from sl1m.constants_and_tools import *
from numpy import array, asmatrix, matrix, zeros, ones
from numpy import array, dot, stack, vstack, hstack, asmatrix, identity, cross, concatenate
from numpy.linalg import norm

from scipy.spatial import ConvexHull
from hpp_bezier_com_traj import *

from random import random as rd
from random import randint as rdi
from numpy import squeeze, asarray
import qp


from sl1m import planner_l1 as pl1
from sl1m import planner    as pl


import mpl_toolkits.mplot3d as a3
import matplotlib.colors as colors
import scipy as sp



from numpy.random import randn
from numpy import eye, ones, zeros, array, identity

eps =0.000001

from time import clock

#LP contact planner using inequality formulation
np.set_printoptions(formatter={'float': lambda x: "{0:0.1f}".format(x)})

def solve(pb,surfaces, draw_scene = None, plot = True ):  
        
    t1 = clock()
    A, b, E, e = pl.convertProblemToLp(pb)    
    C = identity(A.shape[1])
    c = zeros(A.shape[1])
    t2 = clock()
    res = qp.quadprog_solve_qp(C, c,A,b,E,e)
    t3 = clock()
    
    print "time to set up problem" , timMs(t1,t2)
    print "time to solve problem"  , timMs(t2,t3)
    print "total time"             , timMs(t1,t3)
    
    coms, footpos, allfeetpos = pl.retrieve_points_from_res(pb, res)
    
    plot = plot and draw_scene is not None 
    if plot:
        ax = draw_scene(surfaces)
        pl.plotQPRes(pb, res, ax=ax, plot_constraints = False)
    
    return pb, coms, footpos, allfeetpos, res


import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def tovals(variables):
    return array([el.value for el in variables])

def solveMIP(pb, surfaces, MIP = True, draw_scene = None, plot = True):    
    import gurobipy
    import cvxpy as cp
    print "hello"
       
    A, b, E, e = pl1.convertProblemToLp(pb)   
    slackMatrix = pl1.slackSelectionMatrix(pb)
    
    rdim = A.shape[1]
    varReal = cp.Variable(rdim)
    constraints = []
    constraintNormalIneq = A * varReal <= b
    constraintNormalEq   = E * varReal == e
    
    constraints = [constraintNormalIneq, constraintNormalEq]
    #creating boolean vars
    
    
    slackIndices = [i for i,el in enumerate (slackMatrix) if el > 0]
    numSlackVariables = len([el for el in slackMatrix if el > 0])
    boolvars = cp.Variable(numSlackVariables, boolean=True)    
    obj = cp.Minimize(slackMatrix * varReal)
    
    if MIP:    
        constraints = constraints + [varReal[el] <= 100. * boolvars[i] for i, el in enumerate(slackIndices)]   
    
        currentSum = []
        previousL = 0
        for i, el in enumerate(slackIndices):
            if i!= 0 and el- previousL > 2.:
                assert len(currentSum) > 0
                constraints = constraints + [sum(currentSum) == len(currentSum) -1 ]
                currentSum = []
            elif el !=0:
                currentSum = currentSum + [boolvars[i]]
            previousL  = el
            obj = cp.Minimize(ones(numSlackVariables) * boolvars)
    prob = cp.Problem(obj, constraints)
    t1 = clock()
    res = prob.solve(solver=cp.GUROBI, verbose=True )
    t2 = clock()
    res = tovals(varReal)
    
    print "time to solve MIP ", timMs(t1,t2)
    
    #~ coms, footpos, allfeetpos = pl1.retrieve_points_from_res(pb, res)
    
    #~ plot = plot and draw_scene is not None 
    #~ if plot:
        #~ ax = draw_scene()
        #~ pl1.plotQPRes(pb, res, ax=ax, plot_constraints = False)
    
    #~ return pb, coms, footpos, allfeetpos, res

def solveL1(pb, surfaces, draw_scene = None, plot = True):     
    A, b, E, e = pl1.convertProblemToLp(pb)    
    C = identity(A.shape[1]) * 0.00001
    c = pl1.slackSelectionMatrix(pb)
        
    res = qp.quadprog_solve_qp(C, c,A,b,E,e)
    
    plot = plot and draw_scene is not None 
    if plot:
        ax = draw_scene(surfaces)
        pl1.plotQPRes(pb, res, ax=ax, plot_constraints = False)
    
    
    ok = pl1.isSparsityFixed(pb, res)
    solutionIndices = None
    solutionComb = None
    if not ok:
        pbs = pl1.generateAllFixedScenariosWithFixedSparsity(pb, res)
        #~ pbs.reverse()
        
        t3 = clock()
        
        
        #print "time to solve relaxed init ", timMs(t1,t2)
        
        for (pbComb, comb, indices) in pbs:
            A, b, E, e = pl1.convertProblemToLp(pbComb, convertSurfaces = False)
            C = identity(A.shape[1]) * 0.00001
            c = pl1.slackSelectionMatrix(pbComb)
            try:
                res = qp.quadprog_solve_qp(C, c,A,b,E,e)
                if pl1.isSparsityFixed(pbComb, res):
                    print "solved sparsity"                    
                    coms, footpos, allfeetpos = pl1.retrieve_points_from_res(pbComb, res)
                    pb = pbComb
                    ok = True
                    solutionIndices = indices[:]
                    #~ print "indices ", solutionIndices   
                    solutionComb = comb
                    if plot:
                        ax = draw_scene(surfaces)
                        pl1.plotQPRes(pb, res, ax=ax, plot_constraints = False)
                    break
            except:
                print "unfeasible problem"
                pass
            
        t4 = clock()      
        
        print "time to solve combinatorial ", timMs(t3,t4)
        #print "total time to solve relaxed ", timMs(t3,t4) + timMs(t1,t2)
    
    if ok:
        surfacesret, indices = pl1.bestSelectedSurfaces(pb, res)        
        for i, phase in enumerate(pb["phaseData"]): 
            phase["S"] = [surfaces[i][indices[i]]]
        if solutionIndices is not None:
            #print "surfaces = ",surfaces
            for i, idx in enumerate(solutionIndices):
                pb["phaseData"][idx]["S"] = [surfaces[idx][solutionComb[i]]]
        
        return solve(pb,surfaces, draw_scene = draw_scene, plot = plot )  