from .optimizers.mean_variance import MeanVarianceOptimizer
from .optimizers.cvar_optimizer import CVaROptimizer
from .optimizers.risk_parity import RiskParityOptimizer
from .optimizers.tracking_error import TrackingErrorOptimizer
from .optimizers.information_ratio import InformationRatioOptimizer
from .optimizers.kelly import KellyOptimizer
from .optimizers.sortino import SortinoOptimizer
from .optimizers.omega import OmegaOptimizer
# from .optimizers.max_drawdown_milp import MaxDrawdownOptimizer # Optional research mode

class PortfolioOptimizer:
    def __init__(self, method="cvar", **kwargs):
        self.method = method
        self.kwargs = kwargs

    def optimize(self, returns, benchmark=None, **kwargs):
        # Merge init kwargs with runtime kwargs (runtime overrides init)
        run_kwargs = {**self.kwargs, **kwargs}
        
        if self.method == "mean_variance":
            return MeanVarianceOptimizer(**run_kwargs).optimize(returns)
        if self.method == "cvar":
            return CVaROptimizer(**run_kwargs).optimize(returns)
        if self.method == "risk_parity":
            return RiskParityOptimizer(**run_kwargs).optimize(returns)
        if self.method == "tracking_error":
            return TrackingErrorOptimizer(benchmark, **run_kwargs).optimize(returns)
        if self.method == "information_ratio":
            return InformationRatioOptimizer(benchmark, **run_kwargs).optimize(returns)
        if self.method == "kelly":
            return KellyOptimizer(**run_kwargs).optimize(returns)
        if self.method == "sortino":
            return SortinoOptimizer(**run_kwargs).optimize(returns)
        if self.method == "omega":
            return OmegaOptimizer(**run_kwargs).optimize(returns)
        if self.method == "max_drawdown":
             from .optimizers.max_drawdown_milp import MaxDrawdownOptimizer
             return MaxDrawdownOptimizer(**run_kwargs).optimize(returns)

        raise ValueError(f"Unsupported optimization method: {self.method}")
