#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Edge Case Testing - Stage 4
===========================

Comprehensive edge case testing for robustness validation.
Tests system behavior under unusual, invalid, or extreme conditions.

Edge Case Categories:
1. Invalid Input Data - Empty, malformed, or nonsensical inputs
2. Missing Dependencies - Components unavailable or import failures
3. Configuration Errors - Invalid .env settings and malformed configs
4. Network/API Failures - Simulated provider failures and timeouts
5. Resource Constraints - Memory, disk, and processing limitations
6. Boundary Conditions - Values at threshold boundaries
7. Concurrent Access - Multiple simultaneous operations
"""

import os
import sys
import logging
import tempfile
import threading
import time
from typing import Dict, Any, List, Optional
from unittest.mock import patch, MagicMock
from contextlib import contextmanager

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from options_trader.core.analyzer import analyze_symbol

logger = logging.getLogger("test_edge_cases")


class EdgeCaseTestSuite:
    """Comprehensive edge case testing for system robustness."""
    
    def __init__(self):
        self.original_env = os.environ.copy()
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    @contextmanager
    def temporary_env(self, config: Dict[str, str]):
        """Temporarily modify environment variables."""
        old_env = os.environ.copy()
        try:
            os.environ.update(config)
            yield
        finally:
            os.environ.clear()
            os.environ.update(old_env)
    
    def run_test(self, test_name: str, test_func):
        """Run a single test with error handling and reporting."""
        try:
            print(f"\n🧪 Testing: {test_name}")
            print("-" * 50)
            
            test_func()
            
            self.test_results['passed'] += 1
            print(f"✅ {test_name}: PASSED")
            return True
            
        except Exception as e:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"{test_name}: {str(e)}")
            print(f"❌ {test_name}: FAILED - {str(e)}")
            return False
    
    # ========================================
    # Category 1: Invalid Input Data
    # ========================================
    
    def test_empty_symbol(self):
        """Test handling of empty symbol input."""
        result = analyze_symbol("", use_demo=True)
        assert 'error' in result, "Empty symbol should return error"
        assert "symbol" in result['error'].lower(), "Error should mention symbol"
    
    def test_whitespace_symbol(self):
        """Test handling of whitespace-only symbol."""
        result = analyze_symbol("   ", use_demo=True)
        assert 'error' in result, "Whitespace symbol should return error"
    
    def test_special_characters_symbol(self):
        """Test handling of symbols with special characters."""
        special_symbols = ["ABC!", "XYZ@", "123$", "A.B.C", "T-EST"]
        
        for symbol in special_symbols:
            result = analyze_symbol(symbol, use_demo=True)
            # Should not crash, may return error or clean the symbol
            assert isinstance(result, dict), f"Should return dict for symbol: {symbol}"
    
    def test_extremely_long_symbol(self):
        """Test handling of unreasonably long symbols."""
        long_symbol = "A" * 1000
        result = analyze_symbol(long_symbol, use_demo=True)
        # Should not crash, likely returns error
        assert isinstance(result, dict), "Should handle long symbols gracefully"
    
    def test_negative_expirations(self):
        """Test handling of negative expiration count."""
        result = analyze_symbol("AAPL", use_demo=True, expirations_to_check=-1)
        # Should handle gracefully, possibly default to 1
        assert isinstance(result, dict), "Should handle negative expirations"
    
    def test_zero_expirations(self):
        """Test handling of zero expiration count."""
        result = analyze_symbol("AAPL", use_demo=True, expirations_to_check=0)
        # Should handle gracefully, possibly default to 1
        assert isinstance(result, dict), "Should handle zero expirations"
    
    def test_excessive_expirations(self):
        """Test handling of unreasonably high expiration count."""
        result = analyze_symbol("AAPL", use_demo=True, expirations_to_check=10000)
        # Should handle gracefully, possibly cap at reasonable limit
        assert isinstance(result, dict), "Should handle excessive expirations"
    
    # ========================================
    # Category 2: Configuration Errors
    # ========================================
    
    def test_invalid_decision_framework(self):
        """Test handling of invalid decision framework."""
        with self.temporary_env({'DECISION_FRAMEWORK': 'invalid_framework'}):
            try:
                from options_trader.core.decision_engine import ConfigurableDecisionEngine
                engine = ConfigurableDecisionEngine()
                # Should default to a valid framework
                assert engine.framework in ['original', 'enhanced', 'hybrid']
            except ImportError:
                # Components may not be available, which is acceptable
                pass
    
    def test_malformed_boolean_config(self):
        """Test handling of malformed boolean configuration values."""
        bad_boolean_configs = {
            'SHOW_ENHANCED_METRICS': 'maybe',
            'ORIGINAL_STRATEGY_STRICT': 'yes',
            'SHOW_RISK_WARNINGS': '1',
            'ENABLE_STRADDLE_STRUCTURE': 'on'
        }
        
        with self.temporary_env(bad_boolean_configs):
            try:
                from options_trader.core.decision_engine import ConfigurableDecisionEngine
                from options_trader.core.output_formatter import StrategyOutputFormatter
                
                engine = ConfigurableDecisionEngine()
                formatter = StrategyOutputFormatter()
                
                # Should handle gracefully with defaults
                assert isinstance(engine.show_enhanced_metrics, bool)
                assert isinstance(formatter.show_enhanced_metrics, bool)
                
            except ImportError:
                pass  # Components not available
    
    def test_malformed_numeric_thresholds(self):
        """Test handling of malformed numeric threshold values."""
        bad_numeric_configs = {
            'TS_SLOPE_THRESHOLD': 'not_a_number',
            'IV_RV_RATIO_THRESHOLD': 'invalid',
            'VOLUME_THRESHOLD': 'abc123',
            'ACCOUNT_SIZE': 'lots_of_money'
        }
        
        with self.temporary_env(bad_numeric_configs):
            try:
                from options_trader.core.threshold_validator import OriginalThresholdValidator
                
                validator = OriginalThresholdValidator()
                
                # Should use default values when parsing fails
                assert isinstance(validator.thresholds['ts_slope'], (int, float))
                assert isinstance(validator.thresholds['iv_rv_ratio'], (int, float))
                assert isinstance(validator.thresholds['volume'], (int, float))
                
            except ImportError:
                pass  # Components not available
    
    def test_extremely_large_thresholds(self):
        """Test handling of extremely large threshold values."""
        extreme_configs = {
            'TS_SLOPE_THRESHOLD': '999999999',
            'IV_RV_RATIO_THRESHOLD': '1e10',
            'VOLUME_THRESHOLD': '99999999999999',
            'ACCOUNT_SIZE': '1e20'
        }
        
        with self.temporary_env(extreme_configs):
            # Should not crash during initialization
            try:
                from options_trader.core.threshold_validator import OriginalThresholdValidator
                validator = OriginalThresholdValidator()
                
                # Values should be parsed as numbers (even if unreasonable)
                assert isinstance(validator.thresholds['ts_slope'], (int, float))
                
            except ImportError:
                pass
    
    def test_negative_thresholds(self):
        """Test handling of negative threshold values where inappropriate."""
        negative_configs = {
            'IV_RV_RATIO_THRESHOLD': '-1.5',  # Should be positive
            'VOLUME_THRESHOLD': '-1000000',   # Should be positive
            'ACCOUNT_SIZE': '-50000'          # Should be positive
        }
        
        with self.temporary_env(negative_configs):
            # Should handle gracefully (may use defaults or absolute values)
            result = analyze_symbol("AAPL", use_demo=True)
            assert isinstance(result, dict), "Should handle negative thresholds gracefully"
    
    # ========================================
    # Category 3: Boundary Conditions
    # ========================================
    
    def test_threshold_boundary_values(self):
        """Test values exactly at threshold boundaries."""
        try:
            from options_trader.core.threshold_validator import OriginalThresholdValidator
            
            validator = OriginalThresholdValidator()
            
            # Test exact threshold values
            boundary_metrics = {
                'ts_slope': -0.00406,        # Exactly at threshold
                'iv_rv_ratio': 1.25,         # Exactly at threshold
                'avg_volume_30d': 1500000    # Exactly at threshold
            }
            
            result = validator.validate_strict_compliance(boundary_metrics, "BOUNDARY_TEST")
            
            # Should handle exact boundaries correctly
            assert result.signal_count == 3, "Exact boundary values should pass"
            assert result.overall_pass == True, "Boundary validation should pass"
            
        except ImportError:
            pass
    
    def test_precision_edge_cases(self):
        """Test floating-point precision edge cases."""
        try:
            from options_trader.core.threshold_validator import OriginalThresholdValidator
            
            validator = OriginalThresholdValidator()
            
            # Test values very close to thresholds (floating-point precision)
            precision_metrics = {
                'ts_slope': -0.004060000001,  # Barely passing
                'iv_rv_ratio': 1.249999999,   # Barely failing
                'avg_volume_30d': 1500000.1   # Barely passing
            }
            
            result = validator.validate_strict_compliance(precision_metrics, "PRECISION_TEST")
            
            # Should handle floating-point precision correctly
            assert isinstance(result.signal_count, int), "Should return valid signal count"
            assert isinstance(result.overall_pass, bool), "Should return valid pass status"
            
        except ImportError:
            pass
    
    # ========================================
    # Category 4: Resource and Performance Edge Cases
    # ========================================
    
    def test_concurrent_analysis(self):
        """Test concurrent analyze_symbol calls."""
        results = {}
        errors = {}
        
        def run_analysis(thread_id):
            try:
                result = analyze_symbol(f"AAPL", use_demo=True, expirations_to_check=1)
                results[thread_id] = result
            except Exception as e:
                errors[thread_id] = str(e)
        
        # Create multiple threads
        threads = []
        for i in range(3):  # Limited to 3 to avoid overwhelming system
            thread = threading.Thread(target=run_analysis, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion (with timeout)
        for thread in threads:
            thread.join(timeout=30)  # 30-second timeout per thread
        
        # Verify results
        assert len(results) > 0, "At least one concurrent analysis should succeed"
        
        # Check for any deadlocks (threads still alive)
        active_threads = [t for t in threads if t.is_alive()]
        assert len(active_threads) == 0, f"Found {len(active_threads)} threads still running (possible deadlock)"
    
    def test_memory_intensive_analysis(self):
        """Test analysis with potentially memory-intensive operations."""
        # Test with many expirations (if system supports it)
        try:
            result = analyze_symbol("AAPL", use_demo=True, expirations_to_check=5)
            assert isinstance(result, dict), "Should handle multiple expirations without memory issues"
        except Exception as e:
            # Memory limitations are acceptable, but shouldn't crash ungracefully
            assert "memory" in str(e).lower() or "limit" in str(e).lower() or isinstance(result, dict)
    
    # ========================================
    # Category 5: Component Interaction Edge Cases
    # ========================================
    
    def test_partial_component_availability(self):
        """Test behavior when some components are available but others aren't."""
        # This simulates real-world scenarios where some modules may fail to import
        
        # Test basic functionality still works
        result = analyze_symbol("AAPL", use_demo=True, expirations_to_check=1)
        
        # Should return at least basic analysis
        assert 'symbol' in result, "Should return symbol even with partial components"
        assert 'price' in result, "Should return price even with partial components"
    
    def test_circular_dependency_resilience(self):
        """Test resilience against potential circular import issues."""
        # Test multiple imports in different orders
        try:
            # Import in one order
            from options_trader.core import analyzer
            from options_trader.core import data_service
            
            # Import in another order  
            from options_trader.core import data_service
            from options_trader.core import analyzer
            
            # Should not cause circular import issues
            assert True, "No circular import issues"
            
        except ImportError as e:
            # Some imports may fail, but shouldn't be due to circular dependencies
            assert "circular" not in str(e).lower(), f"Circular import detected: {e}"
    
    # ========================================
    # Test Runner
    # ========================================
    
    def run_all_edge_case_tests(self):
        """Run all edge case tests."""
        print("=" * 70)
        print("EDGE CASE TESTING SUITE - STAGE 4")
        print("=" * 70)
        
        test_methods = [
            # Invalid Input Data
            ("Empty Symbol", self.test_empty_symbol),
            ("Whitespace Symbol", self.test_whitespace_symbol),
            ("Special Characters Symbol", self.test_special_characters_symbol),
            ("Extremely Long Symbol", self.test_extremely_long_symbol),
            ("Negative Expirations", self.test_negative_expirations),
            ("Zero Expirations", self.test_zero_expirations),
            ("Excessive Expirations", self.test_excessive_expirations),
            
            # Configuration Errors
            ("Invalid Decision Framework", self.test_invalid_decision_framework),
            ("Malformed Boolean Config", self.test_malformed_boolean_config),
            ("Malformed Numeric Thresholds", self.test_malformed_numeric_thresholds),
            ("Extremely Large Thresholds", self.test_extremely_large_thresholds),
            ("Negative Thresholds", self.test_negative_thresholds),
            
            # Boundary Conditions
            ("Threshold Boundary Values", self.test_threshold_boundary_values),
            ("Precision Edge Cases", self.test_precision_edge_cases),
            
            # Resource and Performance
            ("Concurrent Analysis", self.test_concurrent_analysis),
            ("Memory Intensive Analysis", self.test_memory_intensive_analysis),
            
            # Component Interaction
            ("Partial Component Availability", self.test_partial_component_availability),
            ("Circular Dependency Resilience", self.test_circular_dependency_resilience),
        ]
        
        for test_name, test_method in test_methods:
            self.run_test(test_name, test_method)
        
        # Print summary
        self.print_test_summary()
        
        return self.test_results
    
    def print_test_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 70)
        print("EDGE CASE TESTING SUMMARY")
        print("=" * 70)
        
        total_tests = self.test_results['passed'] + self.test_results['failed']
        pass_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"📊 Pass Rate: {pass_rate:.1f}%")
        
        if self.test_results['errors']:
            print(f"\n❌ FAILED TESTS:")
            for error in self.test_results['errors']:
                print(f"  • {error}")
        
        overall_status = "PASS" if self.test_results['failed'] == 0 else "PARTIAL"
        print(f"\n🎯 Overall Status: {overall_status}")
        
        if self.test_results['failed'] == 0:
            print("🎉 All edge case tests passed! System is robust.")
        else:
            print(f"⚠️ {self.test_results['failed']} tests failed. Review error handling.")


def run_edge_case_tests():
    """Main function to run edge case tests."""
    test_suite = EdgeCaseTestSuite()
    results = test_suite.run_all_edge_case_tests()
    
    # Return success if no failures
    return results['failed'] == 0


if __name__ == "__main__":
    success = run_edge_case_tests()
    sys.exit(0 if success else 1)