#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Options Trading Calculator - Modular Architecture
================================================

Advanced options calculator with earnings volatility strategies and IV crush analysis.
Educational tool for financial research featuring calendar spreads, straddle analysis, 
and term structure modeling.

This package provides:
- Earnings calendar integration with timing windows
- Multi-provider data sourcing with fallbacks  
- Advanced volatility analysis (Yang-Zhang RV, term structure)
- Calendar spread construction and P&L modeling
- Position sizing with fractional Kelly methodology
- Production-ready trading decision framework

DISCLAIMER: 
This software is provided solely for educational and research purposes. 
It is not intended to provide investment advice, and no investment recommendations are made herein. 
The developers are not financial advisors and accept no responsibility for any financial decisions 
or losses resulting from the use of this software. Always consult a professional financial advisor 
before making any investment decisions.
"""

__version__ = "2.0.0"
__author__ = "Trading Calculator Team"

# Import what's available from core
from .core import *

__all__ = []
__all__.extend(getattr(__import__(f"{__name__}.core"), "core").__all__)