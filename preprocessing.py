"""
preprocessing.py

Purpose:
--------
Responsible for preprocessing cleaned return data for downstream
risk modeling, drawdown computation, optimization, and backtesting.

Key Responsibilities:
---------------------
- Data integrity validation
- Stationarity-safe transformations
- Outlier handling (optional)
- Rolling window segmentation
- Train / test splitting
- Numerical stability enforcement

Design Philosophy:
------------------
Fail fast, validate aggressively, and never leak future information.

Author:
-------
Drawdown Optimization Project
"""

from typing import Tuple, Iterator, Optional
import pandas as pd
import numpy as np


class PreprocessingError(Exception):
    """Custom exception for preprocessing failures."""
    pass


class Preprocessor:
    """
    Preprocessing engine for financial return series.
    """

    def __init__(
        self,
        min_obs: int = 50,
        max_missing_ratio: float = 0.0
    ):
        """
        Parameters
        ----------
        min_obs : int
            Minimum observations required for modeling
        max_missing_ratio : float
            Maximum allowed ratio of missing values per asset
        """

        self.min_obs = min_obs
        self.max_missing_ratio = max_missing_ratio

    # ------------------------------------------------------------------
    # STEP 1: BASIC VALIDATION
    # ------------------------------------------------------------------

    def validate_returns(self, returns: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and clean return matrix integrity.

        Test cases handled:
        -------------------
        - Empty DataFrame
        - Non-datetime index
        - NaNs or infinities (dropped)
        - Insufficient observations
        """

        if returns is None or returns.empty:
            raise PreprocessingError("Return DataFrame is empty or None.")

        if not isinstance(returns.index, pd.DatetimeIndex):
            raise PreprocessingError("Return index must be DatetimeIndex.")

        # Replace Inf with NaN and drop rows with NaN
        returns = returns.replace([np.inf, -np.inf], np.nan)
        initial_rows = len(returns)
        returns = returns.dropna()
        dropped_rows = initial_rows - len(returns)
        if dropped_rows > 0:
            print(f"   [Preprocessor] Dropped {dropped_rows} rows with NaN/Inf values.")

        if len(returns) < self.min_obs:
            raise PreprocessingError(
                f"Insufficient observations after cleaning: {len(returns)} < {self.min_obs}"
            )

        return returns

    # ------------------------------------------------------------------
    # STEP 2: OPTIONAL STANDARDIZATION
    # ------------------------------------------------------------------

    def standardize_returns(
        self,
        returns: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Standardize returns (z-score normalization).

        Used for:
        ---------
        - Distance-based methods
        - Stability in simulations

        NOTE:
        -----
        Not used for final portfolio return calculation.
        """

        std = returns.std()
        if (std == 0).any():
            raise PreprocessingError("Zero variance detected in returns.")

        standardized = (returns - returns.mean()) / std
        return standardized

    # ------------------------------------------------------------------
    # STEP 3: DOWNSIDE-FOCUSED TRANSFORMATIONS
    # ------------------------------------------------------------------

    def extract_downside_returns(
        self,
        returns: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Extract downside-only returns (negative returns).

        Used for:
        ---------
        - CVaR
        - Tail risk modeling
        """

        downside = returns.copy()
        downside[downside > 0] = 0.0
        return downside

    # ------------------------------------------------------------------
    # STEP 4: ROLLING WINDOW GENERATION
    # ------------------------------------------------------------------

    def generate_rolling_windows(
        self,
        returns: pd.DataFrame,
        window_size: int,
        step_size: int = 1
    ) -> Iterator[pd.DataFrame]:
        """
        Generate rolling windows for walk-forward optimization.

        Test cases handled:
        -------------------
        - Window size larger than dataset
        - Step size <= 0
        """

        if window_size <= 0:
            raise PreprocessingError("Window size must be positive.")

        if step_size <= 0:
            raise PreprocessingError("Step size must be positive.")

        if window_size > len(returns):
            raise PreprocessingError("Window size exceeds data length.")

        for start in range(0, len(returns) - window_size + 1, step_size):
            yield returns.iloc[start:start + window_size]

    # ------------------------------------------------------------------
    # STEP 5: TRAIN / TEST SPLIT (TIME-AWARE)
    # ------------------------------------------------------------------

    def train_test_split(
        self,
        returns: pd.DataFrame,
        train_ratio: float = 0.7
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Time-aware train-test split.

        Ensures:
        --------
        - No shuffling
        - No look-ahead bias
        """

        if not (0.0 < train_ratio < 1.0):
            raise PreprocessingError("train_ratio must be between 0 and 1.")

        split_idx = int(len(returns) * train_ratio)

        if split_idx < self.min_obs:
            raise PreprocessingError("Training set too small.")

        train = returns.iloc[:split_idx]
        test = returns.iloc[split_idx:]

        return train, test

    # ------------------------------------------------------------------
    # STEP 6: NUMERICAL STABILITY ENFORCEMENT
    # ------------------------------------------------------------------

    def clip_extreme_values(
        self,
        returns: pd.DataFrame,
        max_abs_return: float = 0.5
    ) -> pd.DataFrame:
        """
        Hard clip extreme return values.

        Used only when:
        ----------------
        - Data quality is poor
        - Prevents optimizer explosion
        """

        if max_abs_return <= 0:
            raise PreprocessingError("max_abs_return must be positive.")

        clipped = returns.clip(
            lower=-max_abs_return,
            upper=max_abs_return
        )
        return clipped

    # ------------------------------------------------------------------
    # STEP 7: FULL PREPROCESSING PIPELINE
    # ------------------------------------------------------------------

    def preprocess(
        self,
        returns: pd.DataFrame,
        standardize: bool = False,
        downside_only: bool = False,
        clip_extremes: bool = False
    ) -> pd.DataFrame:
        """
        Execute full preprocessing pipeline.

        Returns
        -------
        pd.DataFrame
            Preprocessed returns ready for modeling
        """

        processed = self.validate_returns(returns)

        if clip_extremes:
            processed = self.clip_extreme_values(processed)

        if downside_only:
            processed = self.extract_downside_returns(processed)

        if standardize:
            processed = self.standardize_returns(processed)

        return processed


# ----------------------------------------------------------------------
# BASIC SELF-TEST
# ----------------------------------------------------------------------

if __name__ == "__main__":
    import pandas as pd
    import numpy as np

    dates = pd.date_range("2020-01-01", periods=300)
    data = pd.DataFrame(
        np.random.normal(0, 0.01, size=(300, 4)),
        index=dates,
        columns=["A", "B", "C", "D"]
    )

    processor = Preprocessor(min_obs=100)

    try:
        clean = processor.preprocess(
            data,
            standardize=False,
            downside_only=False,
            clip_extremes=True
        )

        train, test = processor.train_test_split(clean)
        windows = list(processor.generate_rolling_windows(train, window_size=120))

        print("Preprocessing successful.")
        print(f"Train shape: {train.shape}")
        print(f"Test shape: {test.shape}")
        print(f"Rolling windows: {len(windows)}")

    except Exception as e:
        print(f"Preprocessing failed: {e}")
