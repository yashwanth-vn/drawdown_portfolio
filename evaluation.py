"""
evaluation.py

Purpose:
--------
Provides comprehensive evaluation and comparison utilities for
portfolio optimization results.

Key Responsibilities:
---------------------
- Compute performance metrics
- Compare optimized portfolio vs benchmarks
- Validate robustness of results
- Produce evaluation-ready summaries

Design Principles:
------------------
- Drawdown-first evaluation
- No silent failures
- Benchmark-aware analytics
- Compatible with backtesting & simulation outputs

Author:
-------
Drawdown-Minimization Portfolio Optimizer
"""

from typing import Dict, Optional
import numpy as np
import pandas as pd

from risk_metrics import RiskMetrics


class EvaluationError(Exception):
    """Custom exception for evaluation failures."""
    pass


class PortfolioEvaluator:
    """
    Portfolio performance and risk evaluation engine.
    """

    def __init__(self, cvar_alpha: float = 0.05):
        """
        Parameters
        ----------
        cvar_alpha : float
            Tail probability for CVaR
        """

        self.risk_engine = RiskMetrics(cvar_alpha=cvar_alpha)

    # ------------------------------------------------------------------
    # INTERNAL VALIDATION
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_returns(returns: pd.Series):
        """
        Validate portfolio return series.
        """

        if returns is None or returns.empty:
            raise EvaluationError("Return series is empty or None.")

        if not isinstance(returns, pd.Series):
             returns = pd.Series(returns)

        # Clean NaNs and Infs
        if returns.isna().any() or np.isinf(returns.values).any():
             returns = returns.replace([np.inf, -np.inf], np.nan)
             returns = returns.dropna()
        
        if len(returns) == 0:
             raise EvaluationError("Return series is empty after cleaning NaNs.")

    # ------------------------------------------------------------------
    # CORE METRICS
    # ------------------------------------------------------------------

    def compute_metrics(
        self,
        returns: pd.Series,
        periods_per_year: int = 252
    ) -> Dict[str, float]:
        """
        Compute core risk and performance metrics.

        Returns
        -------
        dict
            Dictionary of metrics
        """

        self._validate_returns(returns)

        mean_return = returns.mean()
        annualized_return = mean_return * periods_per_year
        volatility = returns.std() * np.sqrt(periods_per_year)

        metrics = {
            "annualized_return": float(annualized_return),
            "volatility": float(volatility),
            "max_drawdown": self.risk_engine.max_drawdown(returns),
            "CVaR": self.risk_engine.conditional_value_at_risk(returns),
            "calmar_ratio": self.risk_engine.calmar_ratio(returns),
            "total_return": float((1 + returns).prod() - 1)
        }

        return metrics

    # ------------------------------------------------------------------
    # BENCHMARK COMPARISON
    # ------------------------------------------------------------------

    def compare_with_benchmark(
        self,
        portfolio_returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> pd.DataFrame:
        """
        Compare optimized portfolio with benchmark.

        Returns
        -------
        pd.DataFrame
            Metric comparison table
        """

        self._validate_returns(portfolio_returns)
        self._validate_returns(benchmark_returns)

        if not portfolio_returns.index.equals(benchmark_returns.index):
            raise EvaluationError("Portfolio and benchmark indices must match.")

        portfolio_metrics = self.compute_metrics(portfolio_returns)
        benchmark_metrics = self.compute_metrics(benchmark_returns)

        comparison = pd.DataFrame({
            "Portfolio": portfolio_metrics,
            "Benchmark": benchmark_metrics
        })

        comparison["Difference"] = (
            comparison["Portfolio"] - comparison["Benchmark"]
        )

        return comparison

    # ------------------------------------------------------------------
    # DRAWDOWN CONSISTENCY CHECK
    # ------------------------------------------------------------------

    def drawdown_consistency_test(
        self,
        returns: pd.Series,
        threshold: float = -0.3
    ) -> Dict[str, float]:
        """
        Evaluate how often drawdown exceeds a given threshold.

        Parameters
        ----------
        threshold : float
            Drawdown threshold (e.g., -0.3 = -30%)

        Returns
        -------
        dict
            Drawdown breach statistics
        """

        self._validate_returns(returns)

        drawdown_series = self.risk_engine.drawdown_series(returns)
        breaches = drawdown_series <= threshold

        return {
            "drawdown_threshold": threshold,
            "breach_frequency": float(breaches.mean()),
            "max_drawdown": self.risk_engine.max_drawdown(returns)
        }

    # ------------------------------------------------------------------
    # ROBUSTNESS SUMMARY (BACKTEST + SIMULATION)
    # ------------------------------------------------------------------

    def robustness_summary(
        self,
        backtest_results: Dict[str, object],
        simulation_results: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Combine backtest and Monte Carlo results into a single robustness view.

        Returns
        -------
        dict
            Robustness indicators
        """

        if "max_drawdown" not in backtest_results:
            raise EvaluationError("Backtest results missing max_drawdown.")

        if "worst_case_drawdown" not in simulation_results:
            raise EvaluationError("Simulation results missing worst_case_drawdown.")

        return {
            "historical_max_drawdown": backtest_results["max_drawdown"],
            "simulated_worst_case_drawdown": simulation_results["worst_case_drawdown"],
            "drawdown_gap": (
                backtest_results["max_drawdown"]
                - simulation_results["worst_case_drawdown"]
            ),
            "historical_calmar_ratio": backtest_results.get("calmar_ratio")
        }

    # ------------------------------------------------------------------
    # FINAL EVALUATION REPORT
    # ------------------------------------------------------------------

    def full_evaluation_report(
        self,
        portfolio_returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None
    ) -> Dict[str, object]:
        """
        Generate complete evaluation report.

        Returns
        -------
        dict
            Evaluation report
        """

        report = {
            "portfolio_metrics": self.compute_metrics(portfolio_returns),
            "drawdown_consistency": self.drawdown_consistency_test(portfolio_returns)
        }

        if benchmark_returns is not None:
            report["benchmark_comparison"] = self.compare_with_benchmark(
                portfolio_returns,
                benchmark_returns
            )

        return report


# ----------------------------------------------------------------------
# BASIC SELF-TEST
# ----------------------------------------------------------------------

if __name__ == "__main__":
    import numpy as np
    import pandas as pd

    np.random.seed(11)

    dates = pd.date_range("2019-01-01", periods=600)

    portfolio_returns = pd.Series(
        np.random.normal(0.0006, 0.01, size=600),
        index=dates
    )

    benchmark_returns = pd.Series(
        np.random.normal(0.0008, 0.012, size=600),
        index=dates
    )

    evaluator = PortfolioEvaluator(cvar_alpha=0.05)

    try:
        report = evaluator.full_evaluation_report(
            portfolio_returns,
            benchmark_returns
        )

        print("Evaluation Report Generated Successfully\n")

        print("Portfolio Metrics:")
        for k, v in report["portfolio_metrics"].items():
            print(f"{k}: {v}")

        print("\nBenchmark Comparison:")
        print(report["benchmark_comparison"])

    except Exception as e:
        print(f"Evaluation failed: {e}")
