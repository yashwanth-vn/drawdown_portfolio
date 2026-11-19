import numpy as np
from scipy.optimize import minimize
from .base_optimizer import BaseOptimizer

class RiskParityOptimizer(BaseOptimizer):

    def __init__(self, **kwargs):
        pass  # Accept and ignore extra config params

    def optimize(self, returns):
        cov = returns.cov().values
        n = cov.shape[0]

        def obj(w):
            risk = w @ cov @ w
            rc = w * (cov @ w) / np.sqrt(risk)
            return np.sum((rc - rc.mean()) ** 2)

        constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
        bounds = [(0, 1)] * n
        w0 = np.ones(n) / n

        res = minimize(obj, w0, bounds=bounds, constraints=constraints)
        return dict(zip(returns.columns, res.x))
