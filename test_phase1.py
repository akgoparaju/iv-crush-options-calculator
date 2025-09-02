#!/usr/bin/env python3
"""
Phase 1 Implementation Test Script
Tests the basic analysis workflow integration between FastAPI backend and React frontend
"""

import requests
import json
import sys
import time
from typing import Dict, Any

def test_backend_health():
    """Test if the FastAPI backend is running and healthy"""
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Backend Health: {health_data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Backend Health Check Failed: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend Connection Failed: {e}")
        return False

def test_api_info():
    """Test the API info endpoint"""
    try:
        response = requests.get("http://localhost:8000/api", timeout=5)
        if response.status_code == 200:
            api_data = response.json()
            print(f"✅ API Info: {api_data.get('title', 'unknown')} v{api_data.get('version', 'unknown')}")
            return True
        else:
            print(f"❌ API Info Failed: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ API Info Request Failed: {e}")
        return False

def test_analysis_endpoint():
    """Test the main analysis endpoint with demo data"""
    try:
        # Test payload
        test_request = {
            "symbol": "AAPL",
            "include_earnings": True,
            "include_trade_construction": False,
            "include_position_sizing": False,
            "include_trading_decision": False,
            "use_demo": True,
            "expirations_to_check": 1,
            "account_size": 100000.0,
            "risk_per_trade": 0.02
        }
        
        print(f"🔍 Testing Analysis Endpoint with: {test_request['symbol']}")
        
        response = requests.post(
            "http://localhost:8000/api/analyze",
            json=test_request,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Analysis Success: {result.get('symbol')} from {result.get('data_source')}")
                
                # Check for expected modules
                modules_found = []
                if 'earnings_calendar' in result:
                    modules_found.append("earnings")
                if 'trade_construction' in result:
                    modules_found.append("trades")
                if 'position_sizing' in result:
                    modules_found.append("sizing")
                if 'trading_decision' in result:
                    modules_found.append("decision")
                
                print(f"📊 Modules Present: {', '.join(modules_found) if modules_found else 'basic analysis only'}")
                return True
            else:
                print(f"❌ Analysis Failed: {result.get('error', 'unknown error')}")
                return False
        else:
            print(f"❌ Analysis Request Failed: HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error Details: {error_data}")
            except:
                print(f"   Raw Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Analysis Request Failed: {e}")
        return False

def test_frontend_build():
    """Check if frontend assets can be built (development test)"""
    import os
    import subprocess
    
    frontend_dir = "frontend"
    if not os.path.exists(frontend_dir):
        print("⚠️  Frontend directory not found - skipping build test")
        return True
    
    try:
        print("🏗️  Testing Frontend Build Process...")
        
        # Check if node_modules exists
        if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
            print("⚠️  node_modules not found - run 'npm install' first")
            return False
        
        # Test TypeScript compilation
        result = subprocess.run(
            ["npm", "run", "type-check"],
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ TypeScript Compilation: Success")
            return True
        else:
            print(f"❌ TypeScript Compilation Failed:")
            print(f"   STDOUT: {result.stdout[:200]}...")
            print(f"   STDERR: {result.stderr[:200]}...")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Frontend Build Test Timeout")
        return False
    except FileNotFoundError:
        print("⚠️  npm not found - skipping frontend build test")
        return True
    except Exception as e:
        print(f"❌ Frontend Build Test Error: {e}")
        return False

def main():
    """Run all Phase 1 tests"""
    print("=" * 60)
    print("🚀 Phase 1 Implementation Test Suite")
    print("=" * 60)
    
    tests = [
        ("Backend Health Check", test_backend_health),
        ("API Info Endpoint", test_api_info),
        ("Analysis Endpoint", test_analysis_endpoint),
        ("Frontend Build", test_frontend_build)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 40)
        
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test Error: {e}")
            results.append((test_name, False))
        
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:<8} {test_name}")
        if success:
            passed += 1
    
    print("-" * 60)
    print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Phase 1 implementation is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        print("\nCommon issues:")
        print("- Backend not running: docker-compose up -d")
        print("- Frontend deps missing: cd frontend && npm install")
        print("- Port conflicts: check if port 8000/3000 are available")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test suite crashed: {e}")
        sys.exit(1)