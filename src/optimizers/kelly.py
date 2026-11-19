import cvxpy as cp
import numpy as np
from .base_optimizer import BaseOptimizer

class KellyOptimizer(BaseOptimizer):
    def __init__(self, **kwargs):
        pass  # Accept and ignore extra config params

    def optimize(self, returns):
        # maximize sum(log(1 + r_p))
        # Taylor expansion or direct convex optimization if supported
        # CVXPY has log_sum_exp? No, sum(log(1 + R @ w)) is concave. Maximize concave is convex problem.
        
        T, N = returns.shape
        w = cp.Variable(N)
        
        # Helper variable for returns
        # 1 + R@w  must be > 0
        
        # Create objective directly: Maximize Geometric Mean ~ maximize sum(log(1+r))
        # Need to handle case where 1+r <= 0. Constraint?
        
        R = returns.values
        objective = cp.Maximize(cp.sum(cp.log(1 + R @ w)))
        
        constraints = [
            cp.sum(w) == 1,
            w >= 0,
            1 + R @ w >= 1e-5 # prevent log(<=0)
        ]
        
        try:
             cp.Problem(objective, constraints).solve()
             w_val = w.value
        except:
             # Fallback to scipy if cvxpy fails on log
             from scipy.optimize import minimize
             def obj(wt):
                 rp = R @ wt
                 if np.any(rp <= -1):
                    return 1e6
                 return -np.sum(np.log(1 + rp))
             
             cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
             bnds = [(0, 1)] * N
             res = minimize(obj, np.ones(N)/N, bounds=bnds, constraints=cons)
             w_val = res.x
             
        if w_val is None:
             w_val = np.ones(N) / N # fail safe

        return dict(zip(returns.columns, w_val))
