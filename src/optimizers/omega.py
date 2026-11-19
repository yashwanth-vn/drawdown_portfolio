import numpy as np
from scipy.optimize import minimize
from .base_optimizer import BaseOptimizer

class OmegaOptimizer(BaseOptimizer):
    def __init__(self, omega_threshold=0.0, **kwargs):
        self.threshold = omega_threshold

    def optimize(self, returns):
        # Maximize Omega Ratio
        # Sum(max(0, r - L)) / Sum(max(0, L - r))
        R = returns.values
        n = R.shape[1]
        
        def objective(w):
            rp = R @ w
            excess = rp - self.threshold
            
            gains = np.sum(np.maximum(0, excess))
            losses = np.sum(np.maximum(0, -excess))
            
            if losses < 1e-6:
                return -1000.0 # High value
                
            omega = gains / losses
            return -omega

        constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
        bounds = [(0, 1)] * n
        w0 = np.ones(n) / n

        res = minimize(objective, w0, bounds=bounds, constraints=constraints)
        return dict(zip(returns.columns, res.x))
