import cvxpy as cp
import numpy as np
from .base_optimizer import BaseOptimizer

class MeanVarianceOptimizer(BaseOptimizer):
    def __init__(self, min_expected_return=0.0, **kwargs):
        self.min_return = min_expected_return

    def optimize(self, returns):
        mu = returns.mean().values
        cov = returns.cov().values
        n = len(mu)

        w = cp.Variable(n)
        objective = cp.Minimize(cp.quad_form(w, cov))
        constraints = [
            cp.sum(w) == 1,
            w >= 0
        ]
        
        # Add return constraint only if feasible
        # We try with constraint first
        try:
            prob = cp.Problem(objective, constraints + [mu @ w >= self.min_return])
            prob.solve()
        except:
            prob = None

        # Fallback 1: Relax return constraint
        if prob is None or prob.status not in [cp.OPTIMAL, cp.OPTIMAL_INACCURATE] or w.value is None:
            print("   [Optimizer] Mean-Variance constrained optimization failed. Relaxing return constraint...")
            try:
                prob = cp.Problem(objective, constraints)
                prob.solve()
            except Exception as e:
                print(f"   [Optimizer] Optimization failed completely: {e}")
                w.value = None

        # Fallback 2: Equal Weights
        if w.value is None:
            print("   [Optimizer] Solver failed. Defaulting to Equal Weights (1/N).")
            w_val = np.ones(n) / n
        else:
            w_val = w.value
            
        # Clean small weights
        w_val[w_val < 1e-4] = 0.0
        w_val = w_val / w_val.sum()
            
        return dict(zip(returns.columns, w_val))
