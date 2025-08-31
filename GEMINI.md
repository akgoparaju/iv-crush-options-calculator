# Project Overview

This project is an advanced options trading calculator and calendar spread analyzer. It is a Python application with a graphical user interface (GUI) built using `FreeSimpleGUI`. The application fetches financial data from various sources, including Yahoo Finance, and performs a comprehensive analysis of options trading opportunities.

The application is built with a modular architecture, with the core logic organized into the following modules:

*   **Module 1: Earnings Calendar & Timing Engine**: This module provides precise trading windows for earnings events, with support for multiple data providers and timezones.
*   **Module 2: Trade Construction & P&L Engine**: This module constructs optimal calendar spread and ATM straddle trades, and simulates post-earnings P&L scenarios with configurable IV crush modeling.
*   **Module 3: Position Sizing & Risk Management**: This module calculates the optimal position size using the Fractional Kelly Criterion and assesses the risk of the trade.
*   **Module 4: Trading Decision Automation**: This module provides a trading decision (EXECUTE, PASS, or CONSIDER) based on the entire analysis.

The application can be run in either GUI mode or command-line mode.

# Building and Running

## Dependencies

The project's dependencies are listed in the `requirements.txt` file. To install them, run:

```bash
pip install -r requirements.txt
```

## Running the Application

### GUI Mode

To run the application in GUI mode, execute the `main.py` script without any arguments:

```bash
python main.py
```

### Command-Line Mode

The application can also be run from the command line to analyze a specific symbol. For example:

```bash
python main.py --symbol AAPL
```

You can also enable different analysis modules using command-line flags:

```bash
python main.py --symbol AAPL --earnings --trade-construction --position-sizing --trading-decision
```

For a full list of command-line options, run:

```bash
python main.py --help
```

### Programmatic API

The application can also be used as a library. Here are some examples:

```python
from options_trader import analyze_symbol

# Basic analysis
result = analyze_symbol("AAPL", expirations_to_check=2)

# With earnings analysis (Module 1)
result = analyze_symbol("AAPL", expirations_to_check=2, include_earnings=True)

# With complete analysis (Modules 1+2)
result = analyze_symbol("AAPL", expirations_to_check=2, include_earnings=True, include_trade_construction=True)

# With all modules (1+2+3)
result = analyze_symbol("AAPL", expirations_to_check=2, include_earnings=True,
                       include_trade_construction=True, include_position_sizing=True)

# With complete system (all modules 1+2+3+4)
result = analyze_symbol("AAPL", expirations_to_check=2, include_earnings=True,
                       include_trade_construction=True, include_position_sizing=True,
                       include_trading_decision=True)
```

# Development Conventions

*   **Modular Architecture:** The codebase is organized into modules with specific responsibilities (e.g., data fetching, analysis, GUI).
*   **Multi-Provider Architecture**: The application uses a multi-provider data sourcing strategy with fallback logic to ensure data availability.
*   **Conditional Imports**: The application uses conditional imports to gracefully degrade if some dependencies are not available.
*   **Configuration:** The application uses a `.env` file for configuration.
*   **Logging:** The application uses the `logging` module to log information to a timestamped file in the `logs` directory.
*   **Error Handling:** The code includes error handling to gracefully manage issues like failed API requests or missing data.
*   **Code Style:** The code follows standard Python conventions (PEP 8).
*   **Testing**: The project includes a test suite (`test_modular.py`) for validating the modular architecture.

# Configuration

The application can be configured using a `.env` file. Here are some of the available options:

```bash
# Primary provider (your API key)
ALPHA_VANTAGE_API_KEY=your_key_here

# Module 3: Position Sizing & Risk Management Settings
ACCOUNT_SIZE=100000.0
RISK_PER_TRADE=0.02
MARGIN_MULTIPLIER=2.0

# Risk Management Limits
MAX_POSITION_PCT=0.05
MAX_CONCENTRATION_PCT=0.20
MAX_DAILY_LOSS_PCT=0.02
MAX_PORTFOLIO_DELTA=0.10
MIN_BUYING_POWER_PCT=0.25

# Optional fallback providers
FINNHUB_API_KEY=optional_key
TRADIER_TOKEN=optional_token
TRADIER_BASE=https://sandbox.tradier.com  # or https://api.tradier.com
```

# Strategy

The trading strategy is based on selling earnings volatility. The core idea is that options markets typically overprice the potential move in a stock leading into an earnings announcement. By selling options before the announcement, the strategy aims to profit from the subsequent collapse in implied volatility (IV crush).

## Trade Structures

The strategy uses two main trade structures:

*   **Short ATM Straddle**: This involves selling one at-the-money (ATM) call and one ATM put with the same expiration date. This structure has high potential returns but also high tail risk.
*   **ATM Calendar Spread**: This involves selling a near-term ATM option and buying a longer-term ATM option at the same strike. This is a debit trade with a smoother profit and loss profile.

## Selection Signals

The strategy uses the following signals to identify trading opportunities:

1.  **Term-structure slope**: The front-month IV vs ~45 DTE IV should be negative (backwardated).
2.  **IV30 / RV30 ratio**: The 30-day implied volatility (IV) should be elevated compared to the 30-day realized volatility (RV).
3.  **Liquidity**: The 30-day average trading volume should be high.

## Timing Discipline

The strategy follows a strict timing discipline:

*   **Entry**: ~15 minutes before the close on the session before the earnings announcement.
*   **Exit**: ~15 minutes after the open on the session after the earnings announcement.