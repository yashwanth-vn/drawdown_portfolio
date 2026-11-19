import os
import ssl
import certifi
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
from typing import List, Optional

# Fix SSL certificate issues
ssl._create_default_https_context = ssl._create_unverified_context


class DataLoaderError(Exception):
    pass


class DataLoader:
    """
    Dynamic market data loader for live simulations.

    Supports:
    - Live market data ingestion (yfinance)
    - Equities, ETFs, indices, crypto, FX
    - Automatic alignment and validation
    - Safe fallback to cached/static data
    """

    def __init__(
        self,
        tickers: List[str],
        start_date: str,
        end_date: Optional[str] = None,
        data_dir: str = "data/raw",
        min_history_ratio: float = 0.8,
        frequency: str = "1d",
        auto_update: bool = True
    ):
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date or datetime.today().strftime("%Y-%m-%d")
        self.data_dir = data_dir
        self.min_history_ratio = min_history_ratio
        self.frequency = frequency
        self.auto_update = auto_update

        os.makedirs(self.data_dir, exist_ok=True)

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------
    def load_and_process(self, winsorize: bool = False) -> pd.DataFrame:
        """
        Main entry point used by the pipeline.
        """
        prices = self._fetch_live_prices()
        returns = self._compute_returns(prices)

        if winsorize:
            returns = self._winsorize_returns(returns)

        self._validate_returns(returns)
        return returns

    # --------------------------------------------------
    # Live Market Fetching
    # --------------------------------------------------
    def _fetch_live_prices(self) -> pd.DataFrame:
        """
        Fetch latest available market data dynamically.
        Falls back to cached data if live fetch fails.
        """
        try:
            data = yf.download(
                tickers=self.tickers,
                start=self.start_date,
                end=self.end_date,
                interval=self.frequency,
                auto_adjust=True,
                progress=False,
                threads=True
            )
            
            # Check if download succeeded
            if data.empty or (hasattr(data, 'shape') and data.shape[0] == 0):
                print("   [DataLoader] Live fetch returned empty data, trying cached...")
                return self._load_cached_prices()
            
            # Handle single vs multi-asset structure
            if isinstance(data.columns, pd.MultiIndex):
                prices = data["Close"]
            else:
                prices = data.to_frame(name=self.tickers[0])

            prices = prices.dropna(how="all")
            
            if prices.empty:
                print("   [DataLoader] Processed data empty, trying cached...")
                return self._load_cached_prices()

            self._persist_prices(prices)
            return prices
            
        except Exception as e:
            print(f"   [DataLoader] Live fetch failed ({e}), trying cached...")
            return self._load_cached_prices()

    def _load_cached_prices(self) -> pd.DataFrame:
        """Load the most recent cached price file."""
        import glob
        
        cache_pattern = os.path.join(self.data_dir, "live_prices_*.csv")
        cache_files = sorted(glob.glob(cache_pattern), reverse=True)
        
        if not cache_files:
            raise DataLoaderError("No cached price data available and live fetch failed.")
        
        latest_cache = cache_files[0]
        print(f"   [DataLoader] Using cached data: {os.path.basename(latest_cache)}")
        
        prices = pd.read_csv(latest_cache, index_col=0, parse_dates=True)
        
        # Filter to requested tickers if they exist in cache
        available_tickers = [t for t in self.tickers if t in prices.columns]
        if not available_tickers:
            # Use whatever is available
            available_tickers = prices.columns.tolist()
            print(f"   [DataLoader] Requested tickers not in cache, using: {available_tickers}")
        else:
            prices = prices[available_tickers]
        
        return prices


    # --------------------------------------------------
    # Return Engineering
    # --------------------------------------------------
    def _compute_returns(self, prices: pd.DataFrame) -> pd.DataFrame:
        """
        Compute log returns for simulation stability.
        """
        # Forward-fill missing prices to handle gaps in data
        prices = prices.ffill()
        
        returns = np.log(prices / prices.shift(1))
        returns = returns.dropna(how="all")
        return returns

    # --------------------------------------------------
    # Optional Outlier Control
    # --------------------------------------------------
    def _winsorize_returns(
        self,
        returns: pd.DataFrame,
        lower_q: float = 0.01,
        upper_q: float = 0.99
    ) -> pd.DataFrame:
        """
        Clip extreme returns while preserving tail risk structure.
        """
        lower = returns.quantile(lower_q)
        upper = returns.quantile(upper_q)
        return returns.clip(lower=lower, upper=upper, axis=1)

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------
    def _validate_returns(self, returns: pd.DataFrame):
        """
        Enforce numerical and historical validity.
        Handle NaN and Inf gracefully by dropping affected rows.
        """
        # Replace Inf values with NaN first
        returns.replace([np.inf, -np.inf], np.nan, inplace=True)
        
        # Drop rows with any NaN values
        initial_rows = len(returns)
        returns.dropna(inplace=True)
        dropped_rows = initial_rows - len(returns)
        if dropped_rows > 0:
            print(f"   [DataLoader] Dropped {dropped_rows} rows with NaN/Inf values.")

        if returns.empty:
            raise DataLoaderError("All returns are NaN - no valid data available.")

        min_required = int(self.min_history_ratio * len(returns))
        valid_assets = returns.count() >= min_required
        invalid_cols = returns.columns[~valid_assets].tolist()
        if invalid_cols:
            print(f"   [DataLoader] Removed assets with insufficient history: {invalid_cols}")
        returns.drop(columns=invalid_cols, inplace=True)

        if returns.empty:
            raise DataLoaderError("No assets meet minimum history requirement.")

    # --------------------------------------------------
    # Persistence (for reproducibility & debugging)
    # --------------------------------------------------
    def _persist_prices(self, prices: pd.DataFrame):
        """
        Save fetched prices for reproducibility.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(
            self.data_dir,
            f"live_prices_{timestamp}.csv"
        )
        prices.to_csv(file_path)
