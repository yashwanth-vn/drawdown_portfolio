"""
optimizer.py (SHIM)

Redirects to src.optimizer.PortfolioOptimizer
for backward compatibility with tools in root.
"""
import sys
import os

# Ensure src is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.optimizer import PortfolioOptimizer
    
    # Define OptimizerError alias if needed, or re-export if added to src/optimizer
    class OptimizerError(Exception):
        pass

except ImportError:
    # If src is not found (unlikely), try relative
    from optimizer import PortfolioOptimizer # Loop? No, this file is optimizer.py
    # This block might fail if src is missing.
    raise
