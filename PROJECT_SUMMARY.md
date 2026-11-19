# Drawdown-Minimization Portfolio Optimizer

## 🎯 Project Overview

This project implements a comprehensive **risk-first portfolio optimization framework** that prioritizes drawdown minimization and tail-risk control over return maximization. The system executes a sophisticated backend pipeline for institutional-grade portfolio construction and risk analysis.

## 🏗️ Architecture

### Backend Pipeline (Python)
- **Risk-First Optimization**: CVaR-based portfolio construction
- **Walk-Forward Backtesting**: No look-ahead bias validation
- **Monte Carlo Stress Testing**: 1,000+ scenario simulations
- **Institutional-Grade**: Professional risk management framework

## 📊 Key Features

### ✅ **Complete Pipeline Execution**
1. **Data Ingestion** - Historical market data loading
2. **Preprocessing** - Data cleaning and validation
3. **Optimization** - CVaR-based portfolio construction
4. **Backtesting** - Walk-forward validation
5. **Monte Carlo** - Stress testing simulation
6. **Evaluation** - Performance analysis

### ✅ **Risk-First Framework**
- **CVaR Optimization**: Convex proxy for drawdown control
- **Tail Risk Focus**: 95% confidence level risk metrics
- **Stress Testing**: Monte Carlo worst-case scenarios
- **Drawdown Control**: Maximum drawdown minimization
- **Capital Preservation**: Risk-first over return-first

## 🚀 Quick Start

### Run the Pipeline
```bash
# Install dependencies
pip install -r requirements.txt

# Run the optimization pipeline
python __main__.py
```

## 🛠️ Technical Stack

### Backend
- **Python 3.8+**: Core language
- **NumPy/Pandas**: Data processing
- **CVXPY**: Convex optimization
- **yfinance**: Market data
- **PyYAML**: Configuration

## 📁 Project Structure

```
Drawdown_Portfolio_Optimizer_COE/
├── 🐍 Backend Pipeline
│   ├── __main__.py              # Main execution entry
│   ├── data_loader.py           # Market data ingestion
│   ├── preprocessing.py         # Data cleaning
│   ├── optimizer.py             # CVaR optimization
│   ├── backtesting.py           # Walk-forward testing
│   ├── simulation.py            # Monte Carlo
│   ├── evaluation.py            # Performance analysis
│   └── risk_metrics.py          # Risk calculations
│
├── ⚙️ Configuration
│   └── configs/
│       └── parameters.yaml      # All parameters
│
└── 📊 Data & Results
    ├── data/                    # Market data
    ├── results/                 # Execution results
    └── logs/                    # Execution logs
```

## 🎯 Usage Scenarios

### 1. **Quantitative Researcher**
- Experiment with different parameters
- Analyze walk-forward performance
- Study optimization convergence
- Research risk factor exposure

### 2. **Portfolio Manager**
- Run optimization with custom parameters
- Analyze risk-adjusted returns
- Stress test under various scenarios

### 3. **Risk Analyst**
- Monitor drawdown patterns
- Evaluate tail risk exposure
- Compare Monte Carlo scenarios

## 📚 Documentation

- **configs/parameters.yaml**: All configuration options
- **Code Comments**: Comprehensive inline documentation