#!/usr/bin/env python3
"""Test Yahoo Finance data retrieval to check for accuracy issues."""

import sys
import os
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

def test_yahoo_data(symbol='CRM'):
    """Test Yahoo Finance data retrieval and check for issues."""
    print(f'Testing Yahoo Finance data retrieval for {symbol}...')
    print('='*60)
    
    ticker = yf.Ticker(symbol)
    
    # Get current price
    info = ticker.fast_info
    price = info.last_price
    print(f'Current Price: ${price:.2f}')
    
    # Get options expirations
    expirations = list(ticker.options[:5])
    print(f'\nAvailable expirations: {expirations}')
    
    if not expirations:
        print("No options expirations found!")
        return
    
    # Test multiple expirations
    all_ivs = {}
    print('\n' + '='*60)
    print('Checking IV data for each expiration:')
    print('='*60)
    
    for exp in expirations[:3]:  # Check first 3 expirations
        print(f'\nExpiration: {exp}')
        chain = ticker.option_chain(exp)
        
        calls = chain.calls
        puts = chain.puts
        
        # Find ATM strike
        atm_strike = min(calls['strike'], key=lambda x: abs(x - price))
        print(f'  ATM Strike: ${atm_strike}')
        
        # Get ATM options
        atm_call = calls[calls['strike'] == atm_strike].iloc[0]
        atm_put = puts[puts['strike'] == atm_strike].iloc[0]
        
        call_iv = atm_call['impliedVolatility']
        put_iv = atm_put['impliedVolatility']
        avg_iv = (call_iv + put_iv) / 2
        
        print(f'  Call IV: {call_iv:.6f} ({call_iv*100:.2f}%)')
        print(f'  Put IV: {put_iv:.6f} ({put_iv*100:.2f}%)')
        print(f'  Average IV: {avg_iv:.6f} ({avg_iv*100:.2f}%)')
        
        # Check for suspicious values
        if avg_iv < 0.05:  # Less than 5%
            print(f'  ⚠️  WARNING: Suspicious low IV detected! ({avg_iv*100:.2f}%)')
        
        all_ivs[exp] = avg_iv
    
    # Calculate term structure
    print('\n' + '='*60)
    print('Term Structure Analysis:')
    print('='*60)
    
    if len(all_ivs) >= 2:
        dates = list(all_ivs.keys())
        ivs = list(all_ivs.values())
        today = datetime.now().date()
        
        dtes = []
        for exp_str in dates:
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
            dte = (exp_date - today).days
            dtes.append(dte)
            print(f'{exp_str} ({dte} DTE): IV = {all_ivs[exp_str]*100:.2f}%')
        
        # Calculate slope between first and ~45 DTE (or second expiry)
        first_dte = dtes[0]
        first_iv = ivs[0]
        
        if first_dte < 45 and len(dtes) > 1:
            # Use second expiration or interpolate to 45 days
            if dtes[1] >= 45:
                # Interpolate
                slope = (ivs[1] - first_iv) / (dtes[1] - first_dte)
                iv_45 = first_iv + slope * (45 - first_dte)
                dte_45 = 45
            else:
                # Use second expiry
                iv_45 = ivs[1]
                dte_45 = dtes[1]
        else:
            # Use second expiry
            iv_45 = ivs[1] if len(ivs) > 1 else first_iv
            dte_45 = dtes[1] if len(dtes) > 1 else first_dte + 30
        
        ts_slope = (iv_45 - first_iv) / (dte_45 - first_dte) if dte_45 != first_dte else 0
        print(f'\nTerm Structure Slope: {ts_slope:.6f}')
        print(f'  Front ({first_dte}D): {first_iv*100:.2f}%')
        print(f'  Back (~{dte_45}D): {iv_45*100:.2f}%')
        print(f'  Slope Signal (< -0.00406): {"✅ PASS" if ts_slope <= -0.00406 else "❌ FAIL"}')
    
    # Calculate realized volatility
    print('\n' + '='*60)
    print('Realized Volatility Analysis:')
    print('='*60)
    
    hist = ticker.history(period='60d')
    if len(hist) > 30:
        # Close-to-close volatility
        returns = np.log(hist['Close'] / hist['Close'].shift(1)).dropna()
        rv30_cc = returns.tail(30).std() * np.sqrt(252)
        
        # Yang-Zhang volatility (simplified - using OHLC)
        hist30 = hist.tail(30)
        if len(hist30) > 1:
            o = np.log(hist30['Open'])
            h = np.log(hist30['High']) 
            l = np.log(hist30['Low'])
            c = np.log(hist30['Close'])
            
            # Simplified Yang-Zhang components
            hl = h - l
            co = c - o
            hl_var = np.mean(hl**2)
            co_var = np.var(co, ddof=1)
            
            # Rough Yang-Zhang estimate
            yz_var = hl_var * 0.5 + co_var * 0.5
            rv30_yz = np.sqrt(yz_var * 252)
            
            print(f'30-day RV (Close-to-Close): {rv30_cc:.4f} ({rv30_cc*100:.2f}%)')
            print(f'30-day RV (Yang-Zhang est): {rv30_yz:.4f} ({rv30_yz*100:.2f}%)')
            
            # Use front month IV for IV30 approximation
            if all_ivs:
                iv30 = list(all_ivs.values())[0]  # Use front month as proxy
                iv_rv_ratio_cc = iv30 / rv30_cc if rv30_cc > 0 else 0
                iv_rv_ratio_yz = iv30 / rv30_yz if rv30_yz > 0 else 0
                
                print(f'\nIV/RV Ratio (using Close-to-Close): {iv_rv_ratio_cc:.3f}')
                print(f'IV/RV Ratio (using Yang-Zhang): {iv_rv_ratio_yz:.3f}')
                print(f'IV/RV Signal (≥ 1.25): {"✅ PASS" if iv_rv_ratio_cc >= 1.25 else "❌ FAIL"}')
    
    # Check volume
    print('\n' + '='*60)
    print('Volume Analysis:')
    print('='*60)
    
    if 'Volume' in hist.columns:
        avg_vol = hist['Volume'].tail(30).mean()
        print(f'30-day Average Volume: {avg_vol:,.0f}')
        print(f'Volume Signal (≥ 1.5M): {"✅ PASS" if avg_vol >= 1_500_000 else "❌ FAIL"}')
    
    # Summary
    print('\n' + '='*60)
    print('DATA QUALITY ASSESSMENT:')
    print('='*60)
    
    suspicious_count = sum(1 for iv in all_ivs.values() if iv < 0.05)
    if suspicious_count > 0:
        print(f'⚠️  WARNING: {suspicious_count} expirations with suspicious IV < 5%')
        print('This suggests Yahoo Finance may be returning corrupted options data!')
        print('Recommend using data validation and Black-Scholes fallback.')
    else:
        print('✅ IV data appears reasonable (all > 5%)')

if __name__ == '__main__':
    # Test with multiple symbols
    symbols = ['CRM', 'AAPL', 'SPY']
    
    for symbol in symbols[:1]:  # Test CRM first
        test_yahoo_data(symbol)
        print('\n' + '='*80 + '\n')