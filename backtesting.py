"""
backtesting.py

Purpose:
--------
Implements walk-forward (rolling window) backtesting for the
Drawdown-Minimization Portfolio Optimizer.

Key Features:
-------------
- Time-aware rolling window optimization
- No look-ahead bias
- Periodic portfolio rebalancing
- Drawdown-aware performance evaluation
- Robust failure handling

Design Philosophy:
------------------
Backtesting must mimic real-world portfolio deployment exactly.

Author:
-------
Drawdown-Minimization Portfolio Optimizer
"""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from optimizer import PortfolioOptimizer
from risk_metrics import RiskMetrics


class BacktestError(Exception):
    """Custom exception for backtesting failures."""
    pass


class WalkForwardBacktester:
    """
    Walk-forward backtesting engine.
    """

    def __init__(
        self,
        window_size: int = 252,
        rebalance_frequency: int = 21,
        cvar_alpha: float = 0.05
    ):
        """
        Parameters
        ----------
        window_size : int
            Lookback window size (training period)
        rebalance_frequency : int
            Rebalancing interval (trading days)
        cvar_alpha : float
            CVaR confidence level
        """

        if window_size <= 0:
            raise ValueError("window_size must be positive.")

        if rebalance_frequency <= 0:
            raise ValueError("rebalance_frequency must be positive.")

        self.window_size = window_size
        self.rebalance_frequency = rebalance_frequency
        self.risk_engine = RiskMetrics(cvar_alpha=cvar_alpha)

    # ------------------------------------------------------------------
    # INTERNAL VALIDATION
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_inputs(returns: pd.DataFrame):
        """
        Validate backtesting inputs.
        """

        if returns is None or returns.empty:
            raise BacktestError("Return matrix is empty or None.")

        if not isinstance(returns.index, pd.DatetimeIndex):
            raise BacktestError("Returns must have DatetimeIndex.")

        # Clean NaNs and Infs
        if np.isnan(returns.values).any() or np.isinf(returns.values).any():
             returns.replace([np.inf, -np.inf], np.nan, inplace=True)
             returns.dropna(inplace=True)
        
        if returns.empty:
            raise BacktestError("Returns empty after cleaning NaNs.")

    # ------------------------------------------------------------------
    # WALK-FORWARD BACKTEST
    # ------------------------------------------------------------------

    def run_backtest(
        self,
        returns: pd.DataFrame,
        optimizer: PortfolioOptimizer,
        min_expected_return: Optional[float] = None
    ) -> Dict[str, object]:
        """
        Execute walk-forward backtest.

        Parameters
        ----------
        returns : pd.DataFrame
            Asset return matrix (T x N)
        optimizer : PortfolioOptimizer
            Optimization engine
        min_expected_return : float or None
            Minimum acceptable portfolio return

        Returns
        -------
        dict
            Backtest results and performance metrics
        """

        self._validate_inputs(returns)

        T, N = returns.shape

        if T <= self.window_size:
            raise BacktestError("Insufficient data for backtesting.")

        portfolio_returns: List[float] = []
        rebalance_dates: List[pd.Timestamp] = []
        weight_history: List[Dict[str, float]] = []

        t = self.window_size

        while t < T:
            train_start = t - self.window_size
            train_end = t
            test_end = min(t + self.rebalance_frequency, T)

            train_data = returns.iloc[train_start:train_end]
            test_data = returns.iloc[t:test_end]

            # -------------------------------
            # Optimize on training window
            # -------------------------------
            weights = optimizer.optimize(
                train_data,
                min_expected_return=min_expected_return
            )

            weight_history.append(weights)
            rebalance_dates.append(returns.index[t])

            # -------------------------------
            # Apply weights to test window
            # -------------------------------
            w_vec = np.array([weights[col] for col in returns.columns])
            period_returns = test_data.values @ w_vec

            portfolio_returns.extend(period_returns.tolist())

            t += self.rebalance_frequency

        portfolio_returns = pd.Series(
            portfolio_returns,
            index=returns.index[self.window_size:self.window_size + len(portfolio_returns)]
        )

        # -------------------------------
        # Risk & Performance Metrics
        # -------------------------------
        results = {
            "portfolio_returns": portfolio_returns,
            "rebalance_dates": rebalance_dates,
            "weight_history": weight_history,
            "max_drawdown": self.risk_engine.max_drawdown(portfolio_returns),
            "CVaR": self.risk_engine.conditional_value_at_risk(portfolio_returns),
            "calmar_ratio": self.risk_engine.calmar_ratio(portfolio_returns),
            "total_return": float((1 + portfolio_returns).prod() - 1),
            "annualized_return": float(portfolio_returns.mean() * 252),
            "volatility": float(portfolio_returns.std() * np.sqrt(252))
        }

        return results


# ----------------------------------------------------------------------
# BASIC SELF-TEST
# ----------------------------------------------------------------------

if __name__ == "__main__":
    import numpy as np
    import pandas as pd

    from optimizer import PortfolioOptimizer

    np.random.seed(7)

    dates = pd.date_range("2017-01-01", periods=800)
    returns = pd.DataFrame(
        np.random.normal(0.0004, 0.01, size=(800, 4)),
        index=dates,
        columns=["A", "B", "C", "D"]
    )

    optimizer = PortfolioOptimizer(
        cvar_alpha=0.05,
        long_only=True,
        weight_bounds=(0.0, 0.6)
    )

    backtester = WalkForwardBacktester(
        window_size=252,
        rebalance_frequency=21
    )

    try:
        results = backtester.run_backtest(
            returns,
            optimizer,
            min_expected_return=0.0001
        )

        print("Backtest Completed Successfully")
        print("Max Drawdown:", results["max_drawdown"])
        print("CVaR:", results["CVaR"])
        print("Calmar Ratio:", results["calmar_ratio"])
        print("Total Return:", results["total_return"])

    except Exception as e:
        print(f"Backtesting failed: {e}")
