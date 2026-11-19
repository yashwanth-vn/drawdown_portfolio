"""
risk_metrics.py

Purpose:
--------
Provides robust risk metric computations for portfolio optimization,
including drawdown, Value at Risk (VaR), Conditional Value at Risk (CVaR),
and supporting analytics.

Design Principles:
------------------
- Numerical stability
- Deterministic outputs
- Explicit failure on invalid inputs
- Compatible with convex optimization pipelines

Author:
-------
Drawdown-Minimization Portfolio Optimizer
"""

from typing import Tuple
import numpy as np
import pandas as pd


class RiskMetricsError(Exception):
    """Custom exception for risk metric computation failures."""
    pass


class RiskMetrics:
    """
    Risk metric computation engine.
    """

    def __init__(self, cvar_alpha: float = 0.05):
        """
        Parameters
        ----------
        cvar_alpha : float
            Tail probability for VaR / CVaR (e.g., 0.05 for 95% confidence)
        """

        if not (0.0 < cvar_alpha < 1.0):
            raise ValueError("cvar_alpha must be between 0 and 1.")

        self.cvar_alpha = cvar_alpha

    # ------------------------------------------------------------------
    # INTERNAL VALIDATION
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_returns(returns: pd.Series) -> np.ndarray:
        """
        Validate portfolio return series.
        Automatically cleans NaNs and Infs.
        """

        if returns is None or len(returns) == 0:
            raise RiskMetricsError("Return series is empty or None.")

        # Convert to float array
        values = np.asarray(returns, dtype=float)

        # check for finite values
        mask = np.isfinite(values)
        if not mask.all():
            # Filter out non-finite values
            values = values[mask]
        
        if len(values) == 0:
             raise RiskMetricsError("Return series is empty after cleaning NaNs/Infs.")

        return values

    # ------------------------------------------------------------------
    # CUMULATIVE RETURN SERIES
    # ------------------------------------------------------------------

    def cumulative_returns(self, returns: pd.Series) -> np.ndarray:
        """
        Compute cumulative return (equity curve).

        Formula:
        --------
        C_t = Π (1 + R_t)
        """

        r = self._validate_returns(returns)

        cumulative = np.cumprod(1.0 + r)

        if (cumulative <= 0).any():
            raise RiskMetricsError("Non-positive cumulative values detected.")

        return cumulative

    # ------------------------------------------------------------------
    # DRAWDOWN SERIES
    # ------------------------------------------------------------------

    def drawdown_series(self, returns: pd.Series) -> pd.Series:
        """
        Compute drawdown time series.

        Formula:
        --------
        DD_t = (C_t - Peak_t) / Peak_t
        """

        cumulative = self.cumulative_returns(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max

        return pd.Series(drawdown, index=returns.index)

    # ------------------------------------------------------------------
    # MAXIMUM DRAWDOWN
    # ------------------------------------------------------------------

    def max_drawdown(self, returns: pd.Series) -> float:
        """
        Compute maximum drawdown (scalar).

        Output:
        -------
        Negative float (e.g., -0.32 for 32% drawdown)
        """

        dd = self.drawdown_series(returns)

        max_dd = dd.min()

        if max_dd > 0:
            raise RiskMetricsError("Invalid drawdown calculation.")

        return float(max_dd)

    # ------------------------------------------------------------------
    # VALUE AT RISK (VaR)
    # ------------------------------------------------------------------

    def value_at_risk(self, returns: pd.Series) -> float:
        """
        Compute historical Value at Risk (VaR).

        Definition:
        -----------
        VaR_alpha = quantile_alpha(returns)
        """

        r = self._validate_returns(returns)

        var = np.quantile(r, self.cvar_alpha)

        return float(var)

    # ------------------------------------------------------------------
    # CONDITIONAL VALUE AT RISK (CVaR)
    # ------------------------------------------------------------------

    def conditional_value_at_risk(self, returns: pd.Series) -> float:
        """
        Compute historical Conditional Value at Risk (CVaR).

        Definition:
        -----------
        CVaR_alpha = E[R | R <= VaR_alpha]
        """

        r = self._validate_returns(returns)

        var = np.quantile(r, self.cvar_alpha)
        tail_losses = r[r <= var]

        if len(tail_losses) == 0:
            raise RiskMetricsError("No tail losses found for CVaR.")

        cvar = tail_losses.mean()

        return float(cvar)

    # ------------------------------------------------------------------
    # CALMAR RATIO (DRAWNDOWN-AWARE PERFORMANCE)
    # ------------------------------------------------------------------

    def calmar_ratio(self, returns: pd.Series, periods_per_year: int = 252) -> float:
        """
        Compute Calmar Ratio.

        Formula:
        --------
        Annualized Return / |Max Drawdown|
        """

        r = self._validate_returns(returns)

        mean_return = np.mean(r)
        annualized_return = mean_return * periods_per_year
        max_dd = abs(self.max_drawdown(returns))

        if max_dd == 0:
            raise RiskMetricsError("Maximum drawdown is zero.")

        return float(annualized_return / max_dd)

    # ------------------------------------------------------------------
    # RISK METRIC SUMMARY
    # ------------------------------------------------------------------

    def risk_summary(self, returns: pd.Series) -> dict:
        """
        Compute all major risk metrics in one call.
        """

        return {
            "max_drawdown": self.max_drawdown(returns),
            "VaR": self.value_at_risk(returns),
            "CVaR": self.conditional_value_at_risk(returns),
            "calmar_ratio": self.calmar_ratio(returns)
        }


# ----------------------------------------------------------------------
# BASIC SELF-TEST
# ----------------------------------------------------------------------


class DrawdownDurationError(Exception):
    pass


def compute_drawdown_duration_series(
    returns: pd.Series
) -> pd.Series:
    """
    Compute drawdown duration series (time underwater).

    Parameters
    ----------
    returns : pd.Series
        Portfolio return series

    Returns
    -------
    pd.Series
        Drawdown duration at each time step
    """

    if returns is None or returns.empty:
        raise DrawdownDurationError("Returns series is empty.")

    # Fill NaNs with 0 (neutral return) instead of failing
    returns = returns.fillna(0.0)

    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()

    underwater = cumulative < running_max

    # Count consecutive periods underwater
    duration = underwater.groupby((~underwater).cumsum()).cumsum()

    duration[~underwater] = 0

    return duration


def extract_drawdown_durations(
    duration_series: pd.Series
) -> list:
    """
    Extract individual drawdown durations.

    Example:
    --------
    [3, 7, 2, 15, ...]

    Returns
    -------
    list
        List of drawdown durations
    """

    if duration_series is None or duration_series.empty:
        raise DrawdownDurationError("Duration series is empty.")

    durations = []
    current = 0

    for value in duration_series:
        if value > 0:
            current += 1
        elif current > 0:
            durations.append(current)
            current = 0

    if current > 0:
        durations.append(current)

    return durations


def drawdown_duration_metrics(
    returns: pd.Series,
    tail_quantile: float = 0.05
) -> dict:
    """
    Compute comprehensive drawdown duration metrics.

    Metrics:
    --------
    - Max drawdown duration
    - Average drawdown duration
    - Median drawdown duration
    - Tail drawdown duration (worst alpha%)
    - Number of drawdowns

    Returns
    -------
    dict
        Drawdown duration statistics
    """

    if not (0 < tail_quantile < 1):
        raise ValueError("tail_quantile must be between 0 and 1.")

    duration_series = compute_drawdown_duration_series(returns)
    durations = extract_drawdown_durations(duration_series)

    if len(durations) == 0:
        return {
            "max_drawdown_duration": 0,
            "avg_drawdown_duration": 0,
            "median_drawdown_duration": 0,
            "tail_drawdown_duration": 0,
            "num_drawdowns": 0
        }

    durations = np.array(durations)

    tail_threshold = np.quantile(durations, 1 - tail_quantile)

    return {
        "max_drawdown_duration": int(durations.max()),
        "avg_drawdown_duration": float(durations.mean()),
        "median_drawdown_duration": float(np.median(durations)),
        "tail_drawdown_duration": float(
            durations[durations >= tail_threshold].mean()
        ),
        "num_drawdowns": int(len(durations))
    }


if __name__ == "__main__":
    import pandas as pd
    np.random.seed(42)

    dates = pd.date_range("2020-01-01", periods=500)
    returns = pd.Series(
        np.random.normal(0.0005, 0.01, size=500),
        index=dates
    )

    risk = RiskMetrics(cvar_alpha=0.05)

    try:
        print("Max Drawdown:", risk.max_drawdown(returns))
        print("VaR:", risk.value_at_risk(returns))
        print("CVaR:", risk.conditional_value_at_risk(returns))
        print("Calmar Ratio:", risk.calmar_ratio(returns))
        print("Summary:", risk.risk_summary(returns))

    except Exception as e:
        print(f"Risk metric computation failed: {e}")
