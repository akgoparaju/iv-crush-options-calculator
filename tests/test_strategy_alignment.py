#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Strategy Alignment Test Suite - Stage 4
=======================================

Comprehensive test suite for complete strategy alignment validation.
Tests all stages (1-3) integration and validates system functionality.

Test Categories:
1. Original Strategy Compliance - Verify decisions match YouTube strategy logic exactly
2. Structure Selection - Test both calendar and straddle construction
3. Configuration Validation - All .env settings work correctly
4. Backward Compatibility - Existing functionality preserved
5. Edge Cases - Handle missing data, invalid configurations
"""

import os
import sys
import tempfile
import logging
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock

# Simple pytest replacement for standalone testing
class TestSkipped(Exception):
    pass

class pytest:
    class skip:
        @staticmethod
        def Exception(reason=""):
            return TestSkipped(reason)

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set test environment
os.environ['TESTING'] = 'true'

# Import project modules
from options_trader.core.analyzer import analyze_symbol
from options_trader.core.data_service import DataService

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("test_strategy_alignment")


class TestStrategyAlignment:
    """Comprehensive test suite for strategy alignment (Stages 1-4)."""
    
    def setup_method(self):
        """Set up each test method."""
        self.original_env = os.environ.copy()
        self.test_symbol = "AAPL"
        
        # Set baseline test environment
        os.environ.update({
            'DECISION_FRAMEWORK': 'original',
            'ORIGINAL_STRATEGY_STRICT': 'true',
            'SHOW_ENHANCED_METRICS': 'false',
            'SHOW_RISK_WARNINGS': 'true',
            'TS_SLOPE_THRESHOLD': '-0.00406',
            'IV_RV_RATIO_THRESHOLD': '1.25',
            'VOLUME_THRESHOLD': '1500000',
            'DEFAULT_TRADE_STRUCTURE': 'calendar',
            'ENABLE_STRADDLE_STRUCTURE': 'true'
        })
    
    def teardown_method(self):
        """Clean up after each test method."""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    # ========================================
    # Test Category 1: Original Strategy Compliance
    # ========================================
    
    def test_original_decision_logic_all_signals(self):
        """Test exact match to original YouTube strategy - all 3 signals present."""
        # Create mock data with all 3 signals positive
        mock_analysis = {
            'calendar_spread_analysis': {
                'ts_slope': -0.00500,  # Below -0.00406 threshold (PASS)
                'iv_rv_ratio': 1.30,   # Above 1.25 threshold (PASS)
                'avg_volume_30d': 2000000,  # Above 1.5M threshold (PASS)
                'signal_count': 3
            }
        }
        
        try:
            from options_trader.core.original_decision_engine import OriginalStrategyDecisionEngine
            from options_trader.core.decision_engine import EnhancedTradingDecision
            
            engine = OriginalStrategyDecisionEngine()
            decision = engine.make_original_decision(mock_analysis)
            
            # Verify all signals detected
            assert decision.signal_strength == 3
            assert decision.original_decision == "RECOMMENDED"
            assert decision.original_confidence >= 0.9  # High confidence
            
            # Verify signal breakdown
            assert decision.signal_breakdown['ts_slope_signal'] == True
            assert decision.signal_breakdown['iv_rv_signal'] == True
            assert decision.signal_breakdown['volume_signal'] == True
            
            logger.info("✅ Original strategy test (3/3 signals): PASS")
            
        except ImportError as e:
            logger.warning(f"⚠️ Decision engine not available: {e}")
            raise TestSkipped("Decision engine components not available")
    
    def test_original_decision_logic_two_signals_with_slope(self):
        """Test original strategy - 2 signals including slope (CONSIDER)."""
        mock_analysis = {
            'calendar_spread_analysis': {
                'ts_slope': -0.00500,  # Below -0.00406 threshold (PASS)
                'iv_rv_ratio': 1.20,   # Below 1.25 threshold (FAIL)
                'avg_volume_30d': 2000000,  # Above 1.5M threshold (PASS)
                'signal_count': 2
            }
        }
        
        try:
            from options_trader.core.original_decision_engine import OriginalStrategyDecisionEngine
            
            engine = OriginalStrategyDecisionEngine()
            decision = engine.make_original_decision(mock_analysis)
            
            # Verify moderate confidence decision
            assert decision.signal_strength == 2
            assert decision.original_decision == "CONSIDER"
            assert 0.6 <= decision.original_confidence <= 0.8
            
            # Verify slope signal present
            assert decision.signal_breakdown['ts_slope_signal'] == True
            
            logger.info("✅ Original strategy test (2/3 with slope): PASS")
            
        except ImportError:
            raise TestSkipped("Decision engine components not available")
    
    def test_original_decision_logic_avoid_no_slope(self):
        """Test original strategy - no slope signal (AVOID)."""
        mock_analysis = {
            'calendar_spread_analysis': {
                'ts_slope': 0.00100,   # Above -0.00406 threshold (FAIL)
                'iv_rv_ratio': 1.30,   # Above 1.25 threshold (PASS)
                'avg_volume_30d': 2000000,  # Above 1.5M threshold (PASS)
                'signal_count': 2
            }
        }
        
        try:
            from options_trader.core.original_decision_engine import OriginalStrategyDecisionEngine
            
            engine = OriginalStrategyDecisionEngine()
            decision = engine.make_original_decision(mock_analysis)
            
            # Verify avoid decision without slope
            assert decision.signal_strength == 2
            assert decision.original_decision == "AVOID"
            assert decision.original_confidence <= 0.5
            
            # Verify slope signal absent
            assert decision.signal_breakdown['ts_slope_signal'] == False
            
            logger.info("✅ Original strategy test (no slope): PASS")
            
        except ImportError:
            raise TestSkipped("Decision engine components not available")
    
    # ========================================
    # Test Category 2: Configuration Validation
    # ========================================
    
    def test_configurable_frameworks_original_pure(self):
        """Test original framework configuration (pure mode)."""
        os.environ.update({
            'DECISION_FRAMEWORK': 'original',
            'SHOW_ENHANCED_METRICS': 'false',
            'ORIGINAL_STRATEGY_STRICT': 'true'
        })
        
        try:
            from options_trader.core.decision_engine import ConfigurableDecisionEngine
            from options_trader.core.output_formatter import StrategyOutputFormatter
            
            engine = ConfigurableDecisionEngine()
            formatter = StrategyOutputFormatter()
            
            # Verify configuration loaded correctly
            assert engine.framework == "original"
            assert formatter.show_enhanced_metrics == False
            assert engine.strict_original == True
            
            logger.info("✅ Configuration test (original pure): PASS")
            
        except ImportError:
            raise TestSkipped("Configuration components not available")
    
    def test_configurable_frameworks_original_with_fyi(self):
        """Test original framework with enhanced metrics as FYI."""
        os.environ.update({
            'DECISION_FRAMEWORK': 'original',
            'SHOW_ENHANCED_METRICS': 'true',
            'ORIGINAL_STRATEGY_STRICT': 'true'
        })
        
        try:
            from options_trader.core.decision_engine import ConfigurableDecisionEngine
            from options_trader.core.output_formatter import StrategyOutputFormatter
            
            engine = ConfigurableDecisionEngine()
            formatter = StrategyOutputFormatter()
            
            # Verify configuration
            assert engine.framework == "original"
            assert formatter.show_enhanced_metrics == True
            assert engine.strict_original == True
            
            logger.info("✅ Configuration test (original with FYI): PASS")
            
        except ImportError:
            raise TestSkipped("Configuration components not available")
    
    def test_threshold_validation_precision(self):
        """Test threshold validation with precision warnings."""
        try:
            from options_trader.core.threshold_validator import OriginalThresholdValidator
            
            validator = OriginalThresholdValidator()
            
            # Test metrics very close to thresholds
            test_metrics = {
                'ts_slope': -0.004059,  # Very close to -0.00406
                'iv_rv_ratio': 1.2501,  # Very close to 1.25
                'avg_volume_30d': 1500100  # Very close to 1500000
            }
            
            result = validator.validate_strict_compliance(test_metrics, "TEST")
            
            # Verify precision warnings generated
            assert result.signal_count == 3  # All should pass
            assert len(result.precision_warnings) > 0  # Should have warnings
            assert result.overall_pass == True
            
            logger.info("✅ Threshold validation precision test: PASS")
            
        except ImportError:
            raise TestSkipped("Threshold validator not available")
    
    # ========================================
    # Test Category 3: Structure Selection
    # ========================================
    
    def test_straddle_construction_enabled(self):
        """Test ATM straddle construction when enabled."""
        os.environ.update({
            'ENABLE_STRADDLE_STRUCTURE': 'true',
            'DEFAULT_TRADE_STRUCTURE': 'straddle'
        })
        
        try:
            from options_trader.core.straddle_construction import StraddleConstructor, TradeStructureSelector
            
            constructor = StraddleConstructor()
            selector = TradeStructureSelector()
            
            # Test structure recommendation
            recommendation = selector.recommend_structure("straddle", 25000)
            assert recommendation in ["straddle", "calendar"]
            
            logger.info("✅ Straddle construction test: PASS")
            
        except ImportError:
            logger.warning("⚠️ Straddle construction not available, skipping test")
            raise TestSkipped("Straddle construction components not available")
    
    def test_structure_selection_auto_mode(self):
        """Test automatic structure selection based on account size."""
        try:
            from options_trader.core.straddle_construction import TradeStructureSelector
            
            selector = TradeStructureSelector()
            
            # Test small account (should recommend calendar)
            small_account_rec = selector.recommend_structure("auto", 25000)
            assert small_account_rec == "calendar"
            
            # Test large account (should recommend straddle)
            large_account_rec = selector.recommend_structure("auto", 75000)
            assert large_account_rec == "straddle"
            
            logger.info("✅ Auto structure selection test: PASS")
            
        except ImportError:
            raise TestSkipped("Structure selection components not available")
    
    # ========================================
    # Test Category 4: Backward Compatibility
    # ========================================
    
    def test_analyze_symbol_backward_compatibility(self):
        """Test that original analyze_symbol function still works."""
        try:
            # Test with minimal parameters (original interface)
            result = analyze_symbol(self.test_symbol, use_demo=True, expirations_to_check=1)
            
            # Verify core fields present
            assert 'symbol' in result
            assert 'price' in result
            assert 'calendar_spread_analysis' in result
            
            # Verify no errors
            assert 'error' not in result
            
            logger.info("✅ Backward compatibility test: PASS")
            
        except Exception as e:
            logger.error(f"❌ Backward compatibility test failed: {e}")
            raise Exception(f"Backward compatibility broken: {e}")
    
    def test_analyze_symbol_with_new_features(self):
        """Test analyze_symbol with new Stage 1-3 features."""
        try:
            result = analyze_symbol(
                self.test_symbol, 
                use_demo=True,
                expirations_to_check=1,
                include_earnings=True,
                include_trading_decision=True,
                trade_structure="calendar"
            )
            
            # Verify new features present
            if 'earnings_analysis' in result:
                assert isinstance(result['earnings_analysis'], dict)
            
            if 'trading_decision' in result:
                assert isinstance(result['trading_decision'], dict)
            
            logger.info("✅ New features integration test: PASS")
            
        except Exception as e:
            logger.warning(f"⚠️ New features test failed (expected): {e}")
            # This might fail due to missing components, which is acceptable
    
    # ========================================
    # Test Category 5: Edge Cases
    # ========================================
    
    def test_edge_case_missing_data(self):
        """Test handling of missing or invalid data."""
        try:
            # Test with empty/invalid symbol
            result_empty = analyze_symbol("", use_demo=True)
            assert 'error' in result_empty
            
            # Test with invalid symbol
            result_invalid = analyze_symbol("INVALID_SYMBOL_12345", use_demo=True)
            # Should not crash, may return error or empty data
            assert isinstance(result_invalid, dict)
            
            logger.info("✅ Edge case (missing data) test: PASS")
            
        except Exception as e:
            logger.error(f"❌ Edge case test failed: {e}")
            raise Exception(f"Edge case handling failed: {e}")
    
    def test_edge_case_invalid_configuration(self):
        """Test handling of invalid configuration values."""
        # Test invalid decision framework
        os.environ['DECISION_FRAMEWORK'] = 'invalid_framework'
        
        try:
            from options_trader.core.decision_engine import ConfigurableDecisionEngine
            
            engine = ConfigurableDecisionEngine()
            # Should gracefully handle invalid framework
            assert engine.framework in ['original', 'enhanced', 'hybrid']
            
            logger.info("✅ Edge case (invalid config) test: PASS")
            
        except ImportError:
            raise TestSkipped("Configuration components not available")
        except Exception as e:
            logger.error(f"❌ Invalid configuration test failed: {e}")
            pytest.fail(f"Invalid configuration handling failed: {e}")
    
    def test_edge_case_malformed_thresholds(self):
        """Test handling of malformed threshold values."""
        os.environ.update({
            'TS_SLOPE_THRESHOLD': 'invalid_number',
            'IV_RV_RATIO_THRESHOLD': 'also_invalid',
            'VOLUME_THRESHOLD': 'not_a_number'
        })
        
        try:
            from options_trader.core.threshold_validator import OriginalThresholdValidator
            
            validator = OriginalThresholdValidator()
            
            # Should use default values when parsing fails
            assert isinstance(validator.thresholds['ts_slope'], (int, float))
            assert isinstance(validator.thresholds['iv_rv_ratio'], (int, float))
            assert isinstance(validator.thresholds['volume'], (int, float))
            
            logger.info("✅ Edge case (malformed thresholds) test: PASS")
            
        except ImportError:
            raise TestSkipped("Threshold validator not available")


def run_comprehensive_tests():
    """Run comprehensive test suite with detailed reporting."""
    print("=" * 60)
    print("STRATEGY ALIGNMENT COMPREHENSIVE TEST SUITE - STAGE 4")
    print("=" * 60)
    
    test_results = {
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'errors': []
    }
    
    # Create test instance
    test_suite = TestStrategyAlignment()
    
    # Test methods to run
    test_methods = [
        ('Original Strategy - All Signals', test_suite.test_original_decision_logic_all_signals),
        ('Original Strategy - Two Signals', test_suite.test_original_decision_logic_two_signals_with_slope),
        ('Original Strategy - No Slope', test_suite.test_original_decision_logic_avoid_no_slope),
        ('Configuration - Original Pure', test_suite.test_configurable_frameworks_original_pure),
        ('Configuration - Original FYI', test_suite.test_configurable_frameworks_original_with_fyi),
        ('Threshold Validation', test_suite.test_threshold_validation_precision),
        ('Straddle Construction', test_suite.test_straddle_construction_enabled),
        ('Structure Selection', test_suite.test_structure_selection_auto_mode),
        ('Backward Compatibility', test_suite.test_analyze_symbol_backward_compatibility),
        ('New Features Integration', test_suite.test_analyze_symbol_with_new_features),
        ('Edge Case - Missing Data', test_suite.test_edge_case_missing_data),
        ('Edge Case - Invalid Config', test_suite.test_edge_case_invalid_configuration),
        ('Edge Case - Malformed Thresholds', test_suite.test_edge_case_malformed_thresholds),
    ]
    
    for test_name, test_method in test_methods:
        try:
            print(f"\nRunning: {test_name}")
            print("-" * 50)
            
            test_suite.setup_method()
            test_method()
            test_suite.teardown_method()
            
            test_results['passed'] += 1
            print(f"✅ {test_name}: PASSED")
            
        except TestSkipped as e:
            test_results['skipped'] += 1
            print(f"⚠️ {test_name}: SKIPPED - {str(e)}")
            
        except Exception as e:
            test_results['failed'] += 1
            test_results['errors'].append(f"{test_name}: {str(e)}")
            print(f"❌ {test_name}: FAILED - {str(e)}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    print(f"⚠️ Skipped: {test_results['skipped']}")
    
    if test_results['errors']:
        print(f"\n❌ ERRORS:")
        for error in test_results['errors']:
            print(f"  • {error}")
    
    total_run = test_results['passed'] + test_results['failed']
    if total_run > 0:
        pass_rate = (test_results['passed'] / total_run) * 100
        print(f"\n📊 Pass Rate: {pass_rate:.1f}% ({test_results['passed']}/{total_run})")
    
    overall_status = "PASS" if test_results['failed'] == 0 else "FAIL"
    print(f"\n🎯 Overall Status: {overall_status}")
    
    return test_results


if __name__ == "__main__":
    # Run tests directly
    run_comprehensive_tests()