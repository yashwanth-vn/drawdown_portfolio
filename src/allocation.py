"""
allocation.py

Precise capital allocation utility.
Computes asset allocations from weights with deterministic residual adjustment
to ensure the sum EXACTLY equals the total investment.
"""

from typing import Dict
from decimal import Decimal, ROUND_HALF_UP


def compute_allocation(
    weights: Dict[str, float],
    total_investment: float,
    precision: int = 2
) -> Dict[str, float]:
    """
    Compute capital allocation from portfolio weights.
    
    Uses high-precision arithmetic and applies residual adjustment
    to the largest-weight asset to ensure exact total.
    
    Parameters
    ----------
    weights : Dict[str, float]
        Asset weights (should sum to ~1.0)
    total_investment : float
        Total investment amount
    precision : int
        Decimal places for currency display (default: 2)
        
    Returns
    -------
    Dict[str, float]
        Asset allocations that sum EXACTLY to total_investment
    """
    if not weights:
        return {}
    
    total_inv = Decimal(str(total_investment))
    
    # Step 1: Compute raw allocations with high precision
    raw_allocations = {}
    for asset, weight in weights.items():
        weight_dec = Decimal(str(weight))
        raw_allocations[asset] = total_inv * weight_dec
    
    # Step 2: Round to specified precision
    quantize_exp = Decimal(10) ** -precision
    rounded = {}
    for asset, amount in raw_allocations.items():
        rounded[asset] = amount.quantize(quantize_exp, rounding=ROUND_HALF_UP)
    
    # Step 3: Compute residual
    rounded_sum = sum(rounded.values())
    residual = total_inv.quantize(quantize_exp, rounding=ROUND_HALF_UP) - rounded_sum
    
    # Step 4: Apply residual to largest-weight asset
    if residual != 0:
        # Find asset with largest weight
        largest_asset = max(weights.keys(), key=lambda a: weights[a])
        rounded[largest_asset] += residual
    
    # Convert back to float for JSON serialization
    return {asset: float(amount) for asset, amount in rounded.items()}


def format_allocation_output(
    weights: Dict[str, float],
    allocations: Dict[str, float],
    total_investment: float
) -> str:
    """
    Format allocation output for console/parsing.
    
    Parameters
    ----------
    weights : Dict[str, float]
        Asset weights
    allocations : Dict[str, float]
        Computed allocations
    total_investment : float
        Total investment amount
        
    Returns
    -------
    str
        Formatted output string
    """
    lines = []
    lines.append(f"   Capital Allocation (Total: ${total_investment:,.2f}):")
    
    for asset in weights.keys():
        weight = weights[asset]
        alloc = allocations.get(asset, 0.0)
        lines.append(f"   Allocation: {asset}: {alloc:.2f}")
    
    # Verify sum
    total_allocated = sum(allocations.values())
    lines.append(f"   [Verification] Total Allocated: ${total_allocated:,.2f}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Self-test
    test_weights = {
        "AAPL": 0.1963,
        "MSFT": 0.3541,
        "GOOGL": 0.2248,
        "AMZN": 0.2248
    }
    test_total = 100000.0
    
    allocations = compute_allocation(test_weights, test_total)
    
    print("Test Allocation:")
    for asset, alloc in allocations.items():
        print(f"  {asset}: ${alloc:,.2f}")
    
    total = sum(allocations.values())
    print(f"\nTotal: ${total:,.2f}")
    print(f"Expected: ${test_total:,.2f}")
    print(f"Match: {abs(total - test_total) < 0.01}")
