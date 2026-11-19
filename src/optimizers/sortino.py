import numpy as np
from scipy.optimize import minimize
from .base_optimizer import BaseOptimizer

class SortinoOptimizer(BaseOptimizer):
    def __init__(self, mar=0.0, **kwargs):
        self.mar = mar

    def optimize(self, returns):
        # Maximize Sortino Ratio: (R - MAR) / DownsideDev
        R = returns.values
        n = R.shape[1]
        
        def objective(w):
            rp = R @ w
            mean_ret = np.mean(rp)
            
            # Downside Deviation
            downside = np.minimum(0, rp - self.mar)
            downside_dev = np.sqrt(np.mean(downside**2))
            
            if downside_dev < 1e-6:
                return 1e6 # Minimize negative large number
                
            sortino = (mean_ret - self.mar) / downside_dev
            return -sortino

        constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
        bounds = [(0, 1)] * n
        w0 = np.ones(n) / n

        res = minimize(objective, w0, bounds=bounds, constraints=constraints)
        return dict(zip(returns.columns, res.x))
