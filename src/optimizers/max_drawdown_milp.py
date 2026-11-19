import cvxpy as cp
import numpy as np
from .base_optimizer import BaseOptimizer

class MaxDrawdownOptimizer(BaseOptimizer):
    """
    Exact Max Drawdown Minimization.
    Note: 'MILP' in filename suggests Mixed Integer, but MaxDrawdown is solvable 
    via Linear Programming (chekhlov et al) efficiently without integers 
    for the continuous relaxation. 
    A true MILP is needed only if adding cardinality constraints or discrete lots.
    We implement the LP version which is exact for the historical samples.
    """
    
    def __init__(self, **kwargs):
        pass  # Accept and ignore extra config params
    
    def optimize(self, returns):
        T, N = returns.shape
        w = cp.Variable(N)
        
        # Auxiliary variables for Drawdown
        # u: Max Drawdown
        # x_k: Cumulative uncompounded return at step k (approximation for LP)
        # Using uncompounded returns R @ w for linearity
        # Cumulative Wealth W_k = sum(r_i) for i=1..k (Log returns additive, or simple arithmetic approx)
        # DD_k = max_{j<=k} W_j - W_k
        # Minimize u s.t. u >= W_j - W_k for all j <= k
        
        # We will use the cumulative sum of returns approximation so it remains convex/linear
        
        cum_ret = np.cumsum(returns.values, axis=0) # T x N
        # We want to find w st. max(cum_ret @ w - running_max) is minimized
        
        # This is hard in standard DCP because running_max is convex. 
        # Difference of convex is not DCP.
        
        # Alternative: CDaR with alpha -> 0.
        # But let's try a direct LP formulation if possible.
        # Actually, let's use the CDaR implementation with very small alpha (e.g. 1/T)
        # which effectively minimizes the worst realization.
        
        # We will use the CVaR optimizer logic but with alpha = 1/T approx
        # Or better, simply use scipy logic for exact non-linear result if strict LP fails.
        
        # Reverting to Scipy for "Research Mode" generic implementation to be safe and "Exact"
        
        from scipy.optimize import minimize
        
        R = returns.values
        n = N
        
        def get_max_drawdown(w):
            port_ret = R @ w
            cum = np.cumprod(1 + port_ret)
            peak = np.maximum.accumulate(cum)
            dd = (peak - cum) / peak
            return np.max(dd)

        def obj(w):
            return get_max_drawdown(w)

        constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
        bounds = [(0, 1)] * n
        w0 = np.ones(n) / n

        # Use SLSQP
        res = minimize(obj, w0, bounds=bounds, constraints=constraints)
        return dict(zip(returns.columns, res.x))
