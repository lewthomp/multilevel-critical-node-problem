from gurobipy import *
from Defend import Defend

def AP(Nodes, Edges, Phi, Lambda, target):
    # (rlxAP)

    A = Model("AttackDefend")
    A.setParam('OutputFlag',0)
    A.setParam("NonConvex", 2) # for McCormick evenelope
    # Variables
    y = {v: A.addVar(vtype=GRB.BINARY) for v in Nodes}
    h = {v: A.addVar(lb=0) for v in Nodes}
    q = {(u, v): A.addVar(lb=0) for (u, v) in Edges}
    p = A.addVar(lb=0)
    gamma = {v: A.addVar(lb=0) for v in Nodes}

    A.setObjective(Lambda * p + quicksum(gamma[v] for v in Nodes), GRB.MINIMIZE)

    # Constraints
    AttackBudget = A.addConstr(quicksum(y[v] for v in Nodes) <= Phi)
    Constr1 = {
        v: A.addConstr(
            h[v]
            + quicksum(q[u, v] for (u, v) in Edges)
            - quicksum(q[v, u] for (v, u) in Edges)
            >= 1)
        for v in Nodes}

    Constr2 = {
        v: A.addConstr(
            p - quicksum(q[u, v] for (u, v) in Edges) 
            >= 0) 
            for v in Nodes}

    Constr3 = {
        v: A.addConstr(
            gamma[v] + len(Nodes) * y[v] - h[v] 
            >= 0) 
            for v in Nodes}

    # Sign constraits
    A.addConstr(p >= 0)
    for v in Nodes:
        A.addConstr(h[v] >= 0)
        A.addConstr(gamma[v] >= 0)
    for (u, v) in Edges:
        A.addConstr(q[u, v] >= 0)

    ###### AP Subroutine ######
    best = len(Nodes)
    I_best = set()
    status = 0
    CutsAdded = 0
    X_best = []

    while True:
        A.optimize()
        if A.status == GRB.INFEASIBLE:
            break

        I = set(v for v in Nodes if y[v].x > 0.9)
        Saved, Defended = Defend(Nodes, Edges, Infected=I, Lambda=Lambda)
        value = A.objVal

        if value <= target - 1:
            return (I, "goal", [])
        if len(Saved) <= target - 1:
            return (I, "goal", Defended)
        if len(Saved) < best:
            best = len(Saved)
            I_best = I
            X_best = Defended

        # Add cut
        A.addConstr(quicksum(y[v] for v in Saved) >= 1)
        CutsAdded += 1

    return I_best, "optimal", X_best


