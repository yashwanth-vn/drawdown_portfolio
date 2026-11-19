import cvxpy as cp
import numpy as np
import pandas as pd
from .base_optimizer import BaseOptimizer

class TrackingErrorOptimizer(BaseOptimizer):
    def __init__(self, benchmark: pd.Series = None, **kwargs):
        self.benchmark = benchmark

    def optimize(self, returns):
        # If no benchmark is provided, use equal weight as simplistic proxy or average of universe
        if self.benchmark is None:
             # Create a synthetic benchmark (mean of all assets)
             benchmark_returns = returns.mean(axis=1).values
        else:
            # Align benchmark with returns index
            common_index = returns.index.intersection(self.benchmark.index)
            if len(common_index) < len(returns):
                 # reindex or warn? For now assume aligned or slice
                 benchmark_returns = self.benchmark.reindex(returns.index).fillna(0).values
            else:
                 benchmark_returns = self.benchmark.loc[returns.index].values

        T, N = returns.shape
        w = cp.Variable(N)
        
        # Portfolio returns
        rp = returns.values @ w
        
        # Tracking Error: Std Dev of (Rp - Rb)
        # Minimize sum of squared active returns
        active_returns = rp - benchmark_returns
        objective = cp.Minimize(cp.sum_squares(active_returns))
        
        constraints = [
            cp.sum(w) == 1,
            w >= 0
        ]
        
        cp.Problem(objective, constraints).solve()
        return dict(zip(returns.columns, w.value))
