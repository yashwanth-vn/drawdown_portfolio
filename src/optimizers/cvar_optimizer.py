import cvxpy as cp
import numpy as np
from .base_optimizer import BaseOptimizer

class CVaROptimizer(BaseOptimizer):
    def __init__(self, cvar_alpha=0.05, **kwargs):
        self.alpha = cvar_alpha

    def optimize(self, returns):
        T, N = returns.shape
        w = cp.Variable(N)
        z = cp.Variable()
        u = cp.Variable(T)

        port = returns.values @ w
        objective = cp.Minimize(z + (1 / (self.alpha * T)) * cp.sum(u))

        constraints = [
            u >= -port - z,
            u >= 0,
            cp.sum(w) == 1,
            w >= 0
        ]

        cp.Problem(objective, constraints).solve()
        return dict(zip(returns.columns, w.value))
