import numpy as np
from scipy.optimize import minimize
import pandas as pd
from .base_optimizer import BaseOptimizer

class InformationRatioOptimizer(BaseOptimizer):
    def __init__(self, benchmark: pd.Series = None, **kwargs):
        self.benchmark = benchmark

    def optimize(self, returns):
        if self.benchmark is None:
             benchmark_returns = returns.mean(axis=1).values
        else:
             benchmark_returns = self.benchmark.reindex(returns.index).fillna(0).values

        n = returns.shape[1]
        R = returns.values
        
        def objective(w):
            rp = R @ w
            active_returns = rp - benchmark_returns
            te = np.std(active_returns)
            active_return = np.mean(active_returns)
            
            if te < 1e-6:
                return 1e6 # Avoid division by zero
            
            # Minimize negative IR
            return -(active_return / te)

        constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
        bounds = [(0, 1)] * n
        w0 = np.ones(n) / n

        res = minimize(objective, w0, bounds=bounds, constraints=constraints)
        return dict(zip(returns.columns, res.x))
