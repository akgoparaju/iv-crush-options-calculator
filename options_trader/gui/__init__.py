#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI Interface Components
========================

FreeSimpleGUI-based interface for options trading analysis:
- Main application window with multi-panel layout
- Real-time analysis results display
- Calendar spread recommendations and trading signals
- Debug panel for development and troubleshooting
"""

from .interface import run_gui, build_layout

__all__ = [
    "run_gui",
    "build_layout"
]