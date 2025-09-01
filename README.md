# 🚀 Advanced Options Trading Calculator

> **Professional-grade options analysis system with earnings volatility strategies, risk management, and automated decision-making**

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-Educational-green.svg)](#license)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](#features)

## ✨ Overview

The **Advanced Options Trading Calculator** is a modular, production-ready system designed for sophisticated options analysis with a focus on **earnings volatility strategies**. Built for traders, researchers, and educational institutions who need comprehensive options analysis with professional-grade risk management.

### 🎯 Core Philosophy
- **Evidence-Based Analysis**: All recommendations backed by quantifiable metrics
- **Risk-First Approach**: Comprehensive risk management and position sizing
- **Educational Focus**: Designed for learning and research, not financial advice
- **Professional Output**: Publication-ready reports and analysis

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Advanced Options Calculator                 │
├─────────────────────────────────────────────────────────────┤
│  📊 Earnings Calendar & Timing Analysis                    │
│  🔧 Trade Construction & P&L Modeling                      │
│  💰 Position Sizing & Risk Management                      │
│  🚀 Automated Trading Decision Engine                      │
├─────────────────────────────────────────────────────────────┤
│  🎨 Professional CLI + Markdown Reports                    │
│  🌐 Multi-Provider Data Engine (Yahoo, Alpha Vantage+)     │
│  ⚡ Graceful Degradation & Fallback Systems               │
└─────────────────────────────────────────────────────────────┘
```

## ✅ Key Features

### 📊 **Earnings Calendar & Timing Analysis**
- **Precise Trading Windows**: 15-minute entry/exit windows around earnings announcements
- **Multi-Provider Data Integration**: Alpha Vantage, Yahoo Finance, Finnhub, Tradier with intelligent fallbacks
- **Timezone Intelligence**: Automatic timezone detection with Eastern market fallback
- **BMO/AMC Detection**: Before Market Open vs After Market Close timing analysis
- **Weekend & Holiday Validation**: Automatic conflict detection and warnings

### 🔧 **Advanced Trade Construction**
- **Calendar Spreads**: Automated ATM calendar spread construction and optimization
- **Alternative Strategies**: Short ATM straddle analysis and comparison
- **Greeks Analysis**: Real-time Delta, Gamma, Theta, Vega exposure calculations
- **P&L Scenario Modeling**: Monte Carlo simulations with IV crush modeling
- **Trade Quality Scoring**: Comprehensive quality assessment with win rate predictions

### 💰 **Intelligent Position Sizing**
- **Kelly Criterion Calculator**: Signal-strength adjusted position sizing with fractional Kelly
- **Risk Management Engine**: Portfolio-level risk validation and compliance monitoring  
- **Account Parameter Integration**: Configurable account size, risk tolerance, and position limits
- **Greek Exposure Tracking**: Portfolio-wide delta, theta exposure monitoring
- **Practical Position Constraints**: Realistic contract limits and capital requirements

### 🚀 **Automated Decision Making**
- **Multi-Framework Analysis**: Original strategy, enhanced analytics, and hybrid approaches
- **Signal Validation**: 3-factor signal system (Term Structure, IV/RV Ratio, Volume)
- **Confidence Scoring**: Probabilistic confidence ratings for all recommendations
- **Risk/Reward Analysis**: Comprehensive metrics including expected returns and drawdown
- **Configurable Thresholds**: Customizable parameters for different trading styles

### 🎨 **Professional Reporting System**
- **Dual Output Format**: Real-time console display + professional markdown reports  
- **Smart Text Formatting**: Intelligent text wrapping - no truncated sentences
- **Unicode Table Design**: Professional bordered tables with intelligent column sizing
- **Rich Markdown Reports**: Tables, alerts, blockquotes with proper typography
- **Timestamped Analysis Logs**: Complete analysis history with searchable logs

## 📦 Installation

### Prerequisites
- **Python 3.13+** (recommended) or Python 3.9+
- Virtual environment (recommended)

### Quick Start
```bash
# Clone the repository
git clone https://github.com/akgoparaju/iv-crush-options-calculator.git
cd iv-crush-options-calculator

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
python3 test_modular.py
python3 main.py --version
```

### Dependencies
```
FreeSimpleGUI           # GUI framework
yfinance                # Primary financial data
requests                # HTTP client for API calls
pandas                  # Data manipulation
numpy                   # Numerical computing
scipy                   # Scientific computing
pytz                    # Timezone calculations
```

## 🚀 Usage

### Command Line Interface
```bash
# Basic analysis
python3 main.py --symbol AAPL

# Complete analysis with all modules
python3 main.py --symbol AAPL --earnings --trade-construction --position-sizing --trading-decision

# Demo mode (no API keys required)
python3 main.py --demo --earnings --symbol AAPL

# Custom parameters
python3 main.py --symbol AAPL --earnings --expirations 3 --account-size 50000 --risk-per-trade 0.02
```

### GUI Mode
```bash
# Launch GUI (when dependencies available)
python3 main.py
```

### Programmatic API
```python
from options_trader import analyze_symbol

# Basic analysis
result = analyze_symbol("AAPL", expirations_to_check=2)

# Complete analysis
result = analyze_symbol(
    symbol="AAPL",
    expirations_to_check=2,
    include_earnings=True,
    include_trade_construction=True,
    include_position_sizing=True,
    include_trading_decision=True,
    account_size=100000,
    risk_per_trade=0.01
)
```

## 📊 Strategy Implementation

### Core Strategy: Earnings IV Crush Calendar Spreads

The system implements a sophisticated **earnings volatility strategy** based on:

1. **Term Structure Analysis**: Backwardated volatility curve (slope ≤ -0.00406)
2. **IV/RV Ratio**: Implied volatility overpricing (ratio ≥ 1.25)  
3. **Liquidity Filter**: Adequate volume for execution (≥ 1.5M average)

### Signal Aggregation
- **3/3 Signals**: RECOMMENDED (high confidence)
- **2/3 with Term Structure**: CONSIDER (moderate confidence)
- **Missing Term Structure**: AVOID (no trade)

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Primary data provider
ALPHA_VANTAGE_API_KEY=your_key_here

# Optional fallback providers  
FINNHUB_API_KEY=optional_key
TRADIER_TOKEN=optional_token
TRADIER_BASE=https://sandbox.tradier.com

# Decision framework
DECISION_FRAMEWORK=original              # original|enhanced|hybrid
ENHANCED_METRICS_ENABLED=true
STRICT_ORIGINAL_MODE=true
```

### Account Configuration
```bash
# Position sizing defaults
DEFAULT_ACCOUNT_SIZE=100000
DEFAULT_RISK_PER_TRADE=0.01
MAX_CONTRACTS_PER_TRADE=10000
MIN_CONTRACTS_THRESHOLD=1
```

## 📄 Output Examples

### Console Output
```
================================================================================
====================== ADVANCED OPTIONS TRADING ANALYSIS =======================
================================================================================
┌─ Analysis Overview ───────────────────────────────────────┐
│ Symbol: AAPL                                              │
│ Current Price: $185.25 (yahoo.fast_info)                  │
│ Analysis Mode: LIVE DATA                                  │
│ Expirations: 2                                            │
│ Timestamp: 2025-08-31 22:30:15                            │
└──────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Strategy Signal Analysis                     │
├─────────────────────────────────────────────────────────────────┤
│ Signal Component│ Actual Value │ Threshold   │ Status │ Weight   │
├────────────────┼──────────────┼─────────────┼────────┼──────────┤
│ Term Structure │ -0.008921    │ ≤ -0.00406  │ ✅ PASS │ Critical │
│ Slope          │              │             │        │          │
│ IV/RV Ratio    │ 1.845        │ ≥ 1.25      │ ✅ PASS │ High     │
│ 30-Day Avg     │ 4,250,000    │ ≥ 1,500,000 │ ✅ PASS │ Medium   │
│ Volume         │              │             │        │          │
└──────────────────────────────────────────────────────────────────┘

📄 Markdown report saved: logs/analysis_AAPL_20250831_223015.md
```

### Markdown Report Preview
```markdown
# Advanced Options Trading Analysis - AAPL

**Generated:** 2025-08-31 22:30:15

### Analysis Overview
> **Symbol:** AAPL  
> **Current Price:** $185.25 (yahoo.fast_info)  
> **Analysis Mode:** LIVE DATA  
> **Expirations:** 2  

### Strategy Signal Analysis
| Signal Component | Actual Value | Threshold | Status | Weight |
|---|---|---|---|---|
| Term Structure Slope | -0.008921 | ≤ -0.00406 | ✅ PASS | Critical |
| IV/RV Ratio | 1.845 | ≥ 1.25 | ✅ PASS | High |
| 30-Day Avg Volume | 4,250,000 | ≥ 1,500,000 | ✅ PASS | Medium |

### Trading Decision
> **Decision:** 🚀 RECOMMENDED  
> **Confidence:** 🟢 95.0% (High)  
> **Expected Return:** 287.5%  
```

## 🧪 Testing

```bash
# Run comprehensive test suite
python3 test_modular.py

# Test with demo data (no API required)
python3 main.py --demo --earnings --symbol AAPL

# Test specific modules
python3 main.py --demo --earnings --trade-construction --symbol LULU
```

## 📚 Documentation

- **[Strategy Guide](earnings_iv_crush_strategy_complete_playbook.md)**: Complete earnings IV crush strategy documentation
- **[API Reference](options_trader/)**: Code documentation and examples
- **[Test Suite](test_modular.py)**: Comprehensive testing and validation examples

## 🛣️ Roadmap

### Current Status: ✅ Production Ready
- ✅ **Earnings Analysis**: Complete calendar integration and timing windows
- ✅ **Trade Construction**: Calendar spreads, straddles, and P&L modeling  
- ✅ **Risk Management**: Position sizing with Kelly criterion and portfolio tracking
- ✅ **Decision Engine**: Automated analysis with configurable strategies
- ✅ **Professional Output**: Dual CLI + Markdown reporting system
- ✅ **Testing & Validation**: Comprehensive test suite with edge case coverage

### Future Enhancements
- [ ] **Web Interface**: Modern web-based dashboard
- [ ] **Backtesting Engine**: Historical strategy validation
- [ ] **Alert System**: Real-time opportunity notifications
- [ ] **Portfolio Manager**: Multi-position portfolio tracking
- [ ] **Advanced Strategies**: Iron Condors, Butterflies, etc.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:

- Code style and conventions
- Testing requirements  
- Pull request process
- Development setup

### Development Setup
```bash
# Clone and setup development environment
git clone https://github.com/your-username/trade-calculator.git
cd trade-calculator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Additional dev tools

# Run development tests
python3 -m pytest tests/
python3 test_modular.py
```

## ⚠️ Disclaimer

**IMPORTANT: This software is provided solely for educational and research purposes.**

- ⚠️ **Not Financial Advice**: This software does not provide investment advice
- 📚 **Educational Use Only**: Designed for learning and research purposes
- 🚫 **No Trading Recommendations**: All analysis is for educational demonstration
- 👨‍💼 **Consult Professionals**: Always consult a qualified financial advisor
- 📊 **Verify Data**: Always verify analysis with independent sources
- ⚖️ **Risk Awareness**: Options trading involves substantial risk of loss

The developers accept no responsibility for any financial decisions or losses resulting from the use of this software.

## 📄 License

This project is licensed under the **Educational Use License** - see the [LICENSE](LICENSE) file for details.

**Key Points:**
- ✅ Educational and research use permitted
- ✅ Modification and study encouraged  
- ✅ Non-commercial use allowed
- ❌ Commercial use prohibited without permission
- ❌ No warranty or financial advice provided

## 🙏 Acknowledgments

- **Strategy Foundation**: Based on earnings volatility research and proven options strategies
- **Data Providers**: Yahoo Finance, Alpha Vantage, Finnhub, Tradier APIs
- **Python Ecosystem**: Built with pandas, numpy, scipy, and other excellent libraries
- **Community**: Thanks to all contributors and users providing feedback

---

<div align="center">

**🚀 Ready to analyze? Get started with:**
```bash
python3 main.py --demo --earnings --symbol AAPL
```

**📖 Need help?** Check out the [Strategy Guide](earnings_iv_crush_strategy_complete_playbook.md) for comprehensive documentation

**⭐ Found this useful?** Please star this repository!

</div>