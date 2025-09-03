#!/usr/bin/env python3
"""Test term structure interpolation to understand IV30 calculation."""

import numpy as np
from scipy.interpolate import interp1d
from datetime import datetime, timedelta

def test_term_structure_interpolation():
    """Test how term structure interpolation affects IV30 calculation."""
    
    # Data from actual system output
    print("Testing Term Structure Interpolation")
    print("=" * 60)
    
    # Actual IVs from the system (from debug output)
    expirations = ['2025-09-05', '2025-09-12', '2025-09-19']
    ivs = [1.082, 0.652, 0.528]  # From ATM summary debug messages
    
    # Calculate days to expiry
    today = datetime(2025, 9, 3).date()
    dtes = []
    for exp_str in expirations:
        exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
        dte = (exp_date - today).days
        dtes.append(dte)
        print(f"{exp_str} ({dte} DTE): IV = {ivs[expirations.index(exp_str)]*100:.1f}%")
    
    # Create interpolation function (like the system does)
    print("\n" + "=" * 60)
    print("Interpolation Analysis:")
    print("=" * 60)
    
    # Linear interpolation
    spline = interp1d(dtes, ivs, kind='linear', fill_value="extrapolate")
    
    # Calculate IV at various points
    test_points = [2, 5, 9, 16, 30, 45]
    for dte in test_points:
        if dte <= max(dtes):
            iv = spline(dte)
            print(f"IV at {dte} days: {iv:.4f} ({iv*100:.2f}%)")
        else:
            # Extrapolation
            iv = spline(dte)
            print(f"IV at {dte} days: {iv:.4f} ({iv*100:.2f}%) [EXTRAPOLATED]")
    
    # Calculate IV30 specifically
    print("\n" + "=" * 60)
    print("IV30 Calculation:")
    print("=" * 60)
    
    iv30 = spline(30)
    print(f"IV30 (interpolated to 30 days): {iv30:.4f} ({iv30*100:.2f}%)")
    
    # Calculate term structure slope (front to 45D)
    print("\n" + "=" * 60)
    print("Term Structure Slope Calculation:")
    print("=" * 60)
    
    first_dte = dtes[0]
    first_iv = ivs[0]
    
    # System logic: if first < 45, use 45D, otherwise use second expiry
    if first_dte < 45:
        slope_end = 45
        iv_45 = spline(45)
    else:
        slope_end = dtes[1] if len(dtes) > 1 else first_dte + 15
        iv_45 = spline(slope_end)
    
    ts_slope = (iv_45 - first_iv) / (slope_end - first_dte)
    print(f"Front ({first_dte}D): {first_iv*100:.2f}%")
    print(f"Back ({slope_end}D): {iv_45*100:.2f}%")
    print(f"Slope: {ts_slope:.6f}")
    print(f"Slope Signal (< -0.00406): {'✅ PASS' if ts_slope <= -0.00406 else '❌ FAIL'}")
    
    # Show the problem
    print("\n" + "=" * 60)
    print("PROBLEM IDENTIFIED:")
    print("=" * 60)
    
    print(f"Front month IV (earnings): {ivs[0]*100:.2f}%")
    print(f"IV30 (interpolated): {iv30*100:.2f}%")
    print(f"Difference: {(ivs[0] - iv30)*100:.2f}%")
    print("\n⚠️  IV30 is much lower than front month IV due to interpolation!")
    print("This causes IV/RV ratio to be artificially low.")
    
    # What should be used instead
    print("\n" + "=" * 60)
    print("SUGGESTED FIX:")
    print("=" * 60)
    
    print("For earnings plays with imminent events (< 7 days):")
    print("- Use FRONT MONTH IV directly, not interpolated IV30")
    print("- Compare front month IV to 30-day realized volatility")
    print(f"- Corrected IV/RV ratio would use {ivs[0]*100:.2f}% instead of {iv30*100:.2f}%")
    
    # Calculate corrected IV/RV ratio
    rv30 = 0.4506  # From debug output
    corrected_ratio = ivs[0] / rv30
    interpolated_ratio = iv30 / rv30
    
    print(f"\nActual system IV/RV: {interpolated_ratio:.3f} (using IV30)")
    print(f"Corrected IV/RV: {corrected_ratio:.3f} (using front month IV)")
    print(f"Playbook threshold: ≥ 1.25")
    print(f"Corrected signal: {'✅ PASS' if corrected_ratio >= 1.25 else '❌ FAIL'}")

if __name__ == '__main__':
    test_term_structure_interpolation()