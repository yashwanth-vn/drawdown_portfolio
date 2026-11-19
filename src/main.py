"""
main.py

Purpose:
--------
End-to-end execution pipeline for the
Drawdown-Minimization Portfolio Optimizer.

This version reads all configuration parameters
directly from configs/parameters.yaml.

Author:
-------
Drawdown-Minimization Portfolio Optimizer
"""

import yaml
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Ensure we can import modules from current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports from src package (assuming running as module or from root with src in path)
# If running this file directly, we need to adjust imports or run as module
try:
    from .data_loader import DataLoader
    from .preprocessing import Preprocessor
    from .optimizer import PortfolioOptimizer
    from .simulation import MonteCarloSimulator
    from .backtesting import WalkForwardBacktester
    from .evaluation import PortfolioEvaluator
    from .allocation import compute_allocation
except ImportError:
    # Fallback if running from root without package structure
    from data_loader import DataLoader
    from preprocessing import Preprocessor
    from src.optimizer import PortfolioOptimizer # Use new optimizer
    from simulation import MonteCarloSimulator
    from backtesting import WalkForwardBacktester
    from evaluation import PortfolioEvaluator
    from src.allocation import compute_allocation

# ---------------------------------------------------------------------
# LOAD CONFIGURATION
# ---------------------------------------------------------------------

def load_config(config_path: str = "configs/parameters.yaml") -> dict:
    # Adjust path if running from src
    if not Path(config_path).exists():
        # Try finding it relative to root
        root_path = Path(__file__).parent.parent
        config_path = root_path / "configs" / "parameters.yaml"
        
    if not Path(config_path).exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------------------

def main():
    print("\n===== DRAWNDOWN-MINIMIZATION PORTFOLIO OPTIMIZER =====\n")

    try:
        # --------------------------------------------------
        # Load YAML Configuration
        # --------------------------------------------------
        config = load_config()

        data_cfg = config["data"]
        prep_cfg = config["preprocessing"]
        opt_cfg = config["optimization"]
        bt_cfg = config["backtesting"]
        sim_cfg = config["simulation"]
        eval_cfg = config["evaluation"]

        # --------------------------------------------------
        # 1. DATA LOADING
        # --------------------------------------------------
        print("1. Loading market data...")
        # Adjust data directory path if needed
        data_dir = data_cfg["data_directory"] 
        if not os.path.isabs(data_dir) and not os.path.exists(data_dir):
             # Try relative to root
             root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
             possible_path = os.path.join(root_dir, data_dir)
             if os.path.exists(possible_path):
                 data_dir = possible_path

        loader = DataLoader(
            tickers=data_cfg["tickers"],
            start_date=data_cfg["start_date"],
            end_date=data_cfg["end_date"],
            data_dir=data_dir,
            min_history_ratio=data_cfg["min_history_ratio"]
        )

        returns = loader.load_and_process(
            winsorize=data_cfg["winsorize_returns"]
        )

        print(f"   Data loaded: {returns.shape}")

        # --------------------------------------------------
        # 2. PREPROCESSING
        # --------------------------------------------------
        print("2. Preprocessing data...")
        preprocessor = Preprocessor(
            min_obs=prep_cfg["minimum_observations"],
            max_missing_ratio=prep_cfg["max_missing_ratio"]
        )

        clean_returns = preprocessor.preprocess(
            returns,
            standardize=prep_cfg["standardize_returns"],
            downside_only=prep_cfg["downside_only_returns"],
            clip_extremes=prep_cfg["clip_extreme_returns"]
        )

        print("   Preprocessing completed.")

        # --------------------------------------------------
        # 3. PORTFOLIO OPTIMIZATION (STATIC SAMPLE)
        # --------------------------------------------------
        print(f"3. Running portfolio optimization ({opt_cfg.get('method', 'cvar')})...")
        
        # Initialize Optimizer with config args
        # Pass all opt_cfg as kwargs
        optimizer = PortfolioOptimizer(**opt_cfg)

        optimal_weights = optimizer.optimize(
            clean_returns,
            # benchmark can be passed if we load it. For now None.
        )

        print("   Optimal Portfolio Weights:")
        for asset, weight in optimal_weights.items():
            print(f"   {asset}: {weight:.4f}")

        # --------------------------------------------------
        # 3.1 CAPITAL ALLOCATION (With Residual Adjustment)
        # --------------------------------------------------
        total_investment = config.get("capital", {}).get("total_investment", 100000.0)
        
        # Compute allocations with precise residual adjustment
        allocations = compute_allocation(optimal_weights, total_investment, precision=2)
        
        print(f"\n   Capital Allocation (Total: ${total_investment:,.2f}):")
        for asset in optimal_weights.keys():
            weight_pct = optimal_weights[asset] * 100
            alloc = allocations.get(asset, 0.0)
            print(f"   Allocation: {asset}: {alloc:.2f}")
        
        # Verification: Sum must equal total investment
        allocated_sum = sum(allocations.values())
        print(f"   [Verification] Allocated Sum: ${allocated_sum:,.2f} (Expected: ${total_investment:,.2f})")

        # --------------------------------------------------
        # 4. WALK-FORWARD BACKTESTING
        # --------------------------------------------------
        print("\n4. Running walk-forward backtest...")
        backtester = WalkForwardBacktester(
            window_size=bt_cfg["window_size"],
            rebalance_frequency=bt_cfg["rebalance_frequency"],
            cvar_alpha=opt_cfg["cvar_alpha"]
        )

        backtest_results = backtester.run_backtest(
            clean_returns,
            optimizer,
            min_expected_return=None  # Remove constraint for backtesting
        )

        print("   Backtesting completed.")
        print(f"   Max Drawdown: {backtest_results['max_drawdown']:.4f}")
        print(f"   CVaR: {backtest_results['CVaR']:.4f}")
        print(f"   Calmar Ratio: {backtest_results['calmar_ratio']:.4f}")

        # --------------------------------------------------
        # 5. MONTE CARLO SIMULATION
        # --------------------------------------------------
        if sim_cfg["enabled"]:
            print("\n5. Running Monte Carlo stress test...")
            simulator = MonteCarloSimulator(
                n_simulations=sim_cfg["number_of_simulations"],
                horizon=sim_cfg["simulation_horizon"],
                random_seed=sim_cfg["random_seed"]
            )

            simulation_results = simulator.run_stress_test(
                clean_returns,
                optimal_weights
            )

            print("   Monte Carlo Stress Test Results:")
            for k, v in simulation_results.items():
                print(f"   {k}: {v:.4f}")

        else:
            simulation_results = None
            print("\n5. Monte Carlo simulation disabled.")

        # --------------------------------------------------
        # 6. EVALUATION
        # --------------------------------------------------
        print("\n6. Evaluating portfolio performance...")
        evaluator = PortfolioEvaluator(
            cvar_alpha=opt_cfg["cvar_alpha"]
        )

        evaluation_report = evaluator.full_evaluation_report(
            backtest_results["portfolio_returns"]
        )

        print("\n   Final Portfolio Metrics:")
        for k, v in evaluation_report["portfolio_metrics"].items():
            print(f"   {k}: {v:.4f}")

        print("\n===== PIPELINE EXECUTION COMPLETED SUCCESSFULLY =====")

    except Exception as e:
        print("\n===== PIPELINE EXECUTION FAILED =====")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


# ---------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()
