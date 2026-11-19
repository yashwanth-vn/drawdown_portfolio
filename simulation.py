"""
simulation.py

Purpose:
--------
Implements Monte Carlo simulation for stress testing portfolio
performance under simulated market conditions.

Core Functions:
---------------
- Bootstrap-based return simulation (distribution-free)
- Portfolio path generation
- Drawdown and tail-risk evaluation
- Worst-case risk aggregation

Design Principles:
------------------
- No parametric assumptions unless explicitly chosen
- Compatible with rolling optimization
- Stress-test oriented (not prediction oriented)

Author:
-------
Drawdown-Minimization Portfolio Optimizer
"""

from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd

from risk_metrics import RiskMetrics


class SimulationError(Exception):
    """Custom exception for simulation failures."""
    pass


class MonteCarloSimulator:
    """
    Monte Carlo simulation engine for portfolio stress testing.
    """

    def __init__(
        self,
        n_simulations: int = 1000,
        horizon: int = 252,
        random_seed: Optional[int] = None
    ):
        """
        Parameters
        ----------
        n_simulations : int
            Number of Monte Carlo paths
        horizon : int
            Length of each simulation path (trading days)
        random_seed : int or None
            Seed for reproducibility
        """

        if n_simulations <= 0:
            raise ValueError("n_simulations must be positive.")

        if horizon <= 0:
            raise ValueError("horizon must be positive.")

        self.n_simulations = n_simulations
        self.horizon = horizon
        self.random_seed = random_seed

        if random_seed is not None:
            np.random.seed(random_seed)

        self.risk_engine = RiskMetrics()

    # ------------------------------------------------------------------
    # INTERNAL VALIDATION
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_inputs(
        returns: pd.DataFrame,
        weights: Dict[str, float]
    ):
        """
        Validate simulation inputs.
        """

        if returns is None or returns.empty:
            raise SimulationError("Return matrix is empty or None.")

        if not isinstance(returns, pd.DataFrame):
            raise SimulationError("Returns must be a pandas DataFrame.")

        # Clean NaNs and Infs
        if np.isnan(returns.values).any() or np.isinf(returns.values).any():
             returns.replace([np.inf, -np.inf], np.nan, inplace=True)
             returns.dropna(inplace=True)
        
        if returns.empty:
            raise SimulationError("Returns empty after cleaning NaNs.")

        if not weights:
            raise SimulationError("Weights dictionary is empty.")

        if set(weights.keys()) != set(returns.columns):
            raise SimulationError("Weights and return columns do not match.")

        if not np.isclose(sum(weights.values()), 1.0):
            raise SimulationError("Portfolio weights must sum to 1.")

    # ------------------------------------------------------------------
    # RETURN PATH SIMULATION
    # ------------------------------------------------------------------

    def simulate_return_paths(
        self,
        returns: pd.DataFrame
    ) -> np.ndarray:
        """
        Generate simulated asset return paths using bootstrapping.

        Returns
        -------
        np.ndarray
            Shape: (n_simulations, horizon, n_assets)
        """

        T, N = returns.shape

        if self.horizon > T:
            raise SimulationError(
                "Simulation horizon exceeds available return history."
            )

        sampled_indices = np.random.randint(
            low=0,
            high=T,
            size=(self.n_simulations, self.horizon)
        )

        simulated_paths = returns.values[sampled_indices]

        return simulated_paths

    # ------------------------------------------------------------------
    # PORTFOLIO PATH AGGREGATION
    # ------------------------------------------------------------------

    def compute_portfolio_paths(
        self,
        simulated_returns: np.ndarray,
        weights: Dict[str, float],
        asset_order: list
    ) -> np.ndarray:
        """
        Aggregate asset paths into portfolio return paths.

        Returns
        -------
        np.ndarray
            Shape: (n_simulations, horizon)
        """

        weight_vector = np.array([weights[a] for a in asset_order])

        portfolio_paths = simulated_returns @ weight_vector

        return portfolio_paths

    # ------------------------------------------------------------------
    # DRAWDOWN ANALYSIS
    # ------------------------------------------------------------------

    def compute_simulated_drawdowns(
        self,
        portfolio_paths: np.ndarray
    ) -> np.ndarray:
        """
        Compute maximum drawdown for each simulated path.

        Returns
        -------
        np.ndarray
            Max drawdown per simulation
        """

        max_drawdowns = []

        for path in portfolio_paths:
            series = pd.Series(path)
            mdd = self.risk_engine.max_drawdown(series)
            max_drawdowns.append(mdd)

        return np.array(max_drawdowns)

    # ------------------------------------------------------------------
    # FULL MONTE CARLO STRESS TEST
    # ------------------------------------------------------------------

    def run_stress_test(
        self,
        returns: pd.DataFrame,
        weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Run full Monte Carlo stress test.

        Returns
        -------
        dict
            Stress-test risk summary
        """

        self._validate_inputs(returns, weights)

        asset_order = list(returns.columns)

        simulated_asset_paths = self.simulate_return_paths(returns)

        portfolio_paths = self.compute_portfolio_paths(
            simulated_asset_paths,
            weights,
            asset_order
        )

        drawdowns = self.compute_simulated_drawdowns(portfolio_paths)

        results = {
            "worst_case_drawdown": float(drawdowns.min()),
            "average_drawdown": float(drawdowns.mean()),
            "95_percentile_drawdown": float(
                np.quantile(drawdowns, 0.05)
            ),
            "median_drawdown": float(np.median(drawdowns)),
            "simulations": self.n_simulations,
            "horizon": self.horizon
        }

        return results


# ----------------------------------------------------------------------
# BASIC SELF-TEST
# ----------------------------------------------------------------------

if __name__ == "__main__":
    import numpy as np
    import pandas as pd

    np.random.seed(42)

    dates = pd.date_range("2018-01-01", periods=500)
    returns = pd.DataFrame(
        np.random.normal(0.0004, 0.01, size=(500, 4)),
        index=dates,
        columns=["A", "B", "C", "D"]
    )

    weights = {
        "A": 0.25,
        "B": 0.25,
        "C": 0.25,
        "D": 0.25
    }

    simulator = MonteCarloSimulator(
        n_simulations=1000,
        horizon=252,
        random_seed=123
    )

    try:
        stress_results = simulator.run_stress_test(returns, weights)
        print("Monte Carlo Stress Test Results:")
        for k, v in stress_results.items():
            print(f"{k}: {v}")

    except Exception as e:
        print(f"Simulation failed: {e}")
