#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo Scenarios - Stage 4
========================

Demonstration scenarios for each configuration mode to validate
complete system functionality across all supported configurations.

Scenarios:
1. Original Pure - Minimal output, pure YouTube strategy
2. Original with FYI - Original strategy + enhanced metrics
3. Hybrid Mode - Original primary + enhanced secondary
4. Structure Comparison - Calendar vs Straddle analysis
5. Edge Case Scenarios - Error handling and recovery
"""

import os
import sys
import logging
import tempfile
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from options_trader.core.analyzer import analyze_symbol

logger = logging.getLogger("demo_scenarios")


class DemoScenarios:
    """Demo scenarios for comprehensive system validation."""
    
    # Configuration templates
    DEMO_CONFIGURATIONS = {
        "original_pure": {
            "name": "Original Pure Strategy",
            "description": "Pure YouTube strategy with minimal output",
            "config": {
                "DECISION_FRAMEWORK": "original",
                "SHOW_ENHANCED_METRICS": "false",
                "ORIGINAL_STRATEGY_STRICT": "true",
                "SHOW_RISK_WARNINGS": "true",
                "SHOW_THRESHOLD_DETAIL": "false",
                "SHOW_PRECISION_WARNINGS": "false",
                "DEFAULT_TRADE_STRUCTURE": "calendar"
            }
        },
        
        "original_with_fyi": {
            "name": "Original Strategy with Enhanced FYI",
            "description": "Original strategy primary + enhanced metrics as FYI",
            "config": {
                "DECISION_FRAMEWORK": "original",
                "SHOW_ENHANCED_METRICS": "true",
                "ORIGINAL_STRATEGY_STRICT": "true",
                "SHOW_RISK_WARNINGS": "true",
                "SHOW_THRESHOLD_DETAIL": "true",
                "SHOW_PRECISION_WARNINGS": "true",
                "DEFAULT_TRADE_STRUCTURE": "calendar"
            }
        },
        
        "hybrid_mode": {
            "name": "Hybrid Decision Framework",
            "description": "Hybrid mode with original primary + enhanced secondary",
            "config": {
                "DECISION_FRAMEWORK": "hybrid",
                "SHOW_ENHANCED_METRICS": "true",
                "ORIGINAL_STRATEGY_STRICT": "false",
                "SHOW_RISK_WARNINGS": "true",
                "SHOW_THRESHOLD_DETAIL": "true",
                "SHOW_CONFIDENCE_BREAKDOWN": "true",
                "DEFAULT_TRADE_STRUCTURE": "auto"
            }
        },
        
        "straddle_focused": {
            "name": "ATM Straddle Analysis",
            "description": "Straddle-focused analysis with risk warnings",
            "config": {
                "DECISION_FRAMEWORK": "original",
                "SHOW_ENHANCED_METRICS": "true",
                "DEFAULT_TRADE_STRUCTURE": "straddle",
                "ENABLE_STRADDLE_STRUCTURE": "true",
                "STRADDLE_RISK_WARNING": "true",
                "SHOW_TRADE_STRUCTURE": "true",
                "SHOW_RISK_WARNINGS": "true"
            }
        },
        
        "comprehensive_analysis": {
            "name": "Comprehensive Analysis Mode",
            "description": "All features enabled for maximum analysis",
            "config": {
                "DECISION_FRAMEWORK": "original",
                "SHOW_ENHANCED_METRICS": "true",
                "SHOW_RISK_WARNINGS": "true",
                "SHOW_THRESHOLD_DETAIL": "true",
                "SHOW_PRECISION_WARNINGS": "true",
                "SHOW_CONFIDENCE_BREAKDOWN": "true",
                "SHOW_TRADE_STRUCTURE": "true",
                "SHOW_TIMING_WINDOWS": "true",
                "ENABLE_STRADDLE_STRUCTURE": "true",
                "DEFAULT_TRADE_STRUCTURE": "auto"
            }
        }
    }
    
    @contextmanager
    def temporary_env(self, config: Dict[str, str]):
        """Temporarily set environment variables for testing."""
        old_env = os.environ.copy()
        try:
            # Update environment with scenario config
            os.environ.update(config)
            yield
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(old_env)
    
    def run_scenario(self, scenario_name: str, symbol: str = "AAPL") -> Dict[str, Any]:
        """Run a specific demo scenario."""
        if scenario_name not in self.DEMO_CONFIGURATIONS:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        scenario = self.DEMO_CONFIGURATIONS[scenario_name]
        
        print(f"\n{'='*60}")
        print(f"DEMO SCENARIO: {scenario['name']}")
        print(f"{'='*60}")
        print(f"Description: {scenario['description']}")
        print(f"Symbol: {symbol}")
        
        result = {}
        
        with self.temporary_env(scenario['config']):
            try:
                print(f"\nConfiguration:")
                for key, value in scenario['config'].items():
                    print(f"  {key} = {value}")
                
                print(f"\nRunning analysis...")
                
                # Run analysis with demo data
                analysis_result = analyze_symbol(
                    symbol,
                    use_demo=True,
                    expirations_to_check=2,
                    include_earnings=True,
                    include_trading_decision=True,
                    trade_structure=scenario['config'].get('DEFAULT_TRADE_STRUCTURE', 'calendar')
                )
                
                result = {
                    'scenario': scenario_name,
                    'status': 'success',
                    'symbol': symbol,
                    'config': scenario['config'],
                    'analysis': analysis_result
                }
                
                # Extract key metrics for summary
                if 'calendar_spread_analysis' in analysis_result:
                    cal_analysis = analysis_result['calendar_spread_analysis']
                    print(f"\n📊 Key Results:")
                    print(f"  Signal Count: {cal_analysis.get('signal_count', 0)}/3")
                    print(f"  Recommendation: {cal_analysis.get('recommendation', 'N/A')}")
                    print(f"  TS Slope: {cal_analysis.get('ts_slope', 'N/A')}")
                    print(f"  IV/RV Ratio: {cal_analysis.get('iv_rv_ratio', 'N/A')}")
                
                if 'trading_decision' in analysis_result:
                    decision = analysis_result['trading_decision']
                    print(f"  Decision: {decision.get('decision', 'N/A')}")
                    print(f"  Confidence: {decision.get('original_confidence', 0)*100:.1f}%")
                
                if 'trading_decision_display' in analysis_result:
                    print(f"\n💻 Formatted Output Preview:")
                    display_lines = str(analysis_result['trading_decision_display']).split('\n')
                    for line in display_lines[:10]:  # Show first 10 lines
                        print(f"  {line}")
                    if len(display_lines) > 10:
                        print(f"  ... ({len(display_lines)-10} more lines)")
                
                print(f"\n✅ Scenario '{scenario['name']}' completed successfully")
                
            except Exception as e:
                result = {
                    'scenario': scenario_name,
                    'status': 'error',
                    'error': str(e),
                    'config': scenario['config']
                }
                print(f"\n❌ Scenario '{scenario['name']}' failed: {e}")
        
        return result
    
    def run_all_scenarios(self, symbol: str = "AAPL") -> List[Dict[str, Any]]:
        """Run all demo scenarios and return results."""
        print("\n" + "="*80)
        print("COMPREHENSIVE DEMO SCENARIOS - STAGE 4 VALIDATION")
        print("="*80)
        
        results = []
        
        for scenario_name in self.DEMO_CONFIGURATIONS:
            try:
                result = self.run_scenario(scenario_name, symbol)
                results.append(result)
            except Exception as e:
                results.append({
                    'scenario': scenario_name,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Print summary
        self.print_scenario_summary(results)
        
        return results
    
    def print_scenario_summary(self, results: List[Dict[str, Any]]):
        """Print summary of all scenario results."""
        print(f"\n{'='*60}")
        print("DEMO SCENARIOS SUMMARY")
        print("="*60)
        
        success_count = sum(1 for r in results if r.get('status') == 'success')
        error_count = sum(1 for r in results if r.get('status') == 'error')
        
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed: {error_count}")
        print(f"📊 Success Rate: {success_count/(success_count+error_count)*100:.1f}%")
        
        if error_count > 0:
            print(f"\n❌ Failed Scenarios:")
            for result in results:
                if result.get('status') == 'error':
                    scenario_name = self.DEMO_CONFIGURATIONS.get(result['scenario'], {}).get('name', result['scenario'])
                    print(f"  • {scenario_name}: {result.get('error', 'Unknown error')}")
        
        print(f"\n🎯 Overall Status: {'PASS' if error_count == 0 else 'FAIL'}")
    
    def validate_configuration_scenarios(self) -> Dict[str, Any]:
        """Validate that all configuration scenarios are valid."""
        validation_results = {
            'valid_configs': 0,
            'invalid_configs': 0,
            'errors': []
        }
        
        print(f"\n{'='*50}")
        print("CONFIGURATION VALIDATION")
        print("="*50)
        
        for scenario_name, scenario in self.DEMO_CONFIGURATIONS.items():
            try:
                config = scenario['config']
                
                # Validate decision framework
                framework = config.get('DECISION_FRAMEWORK', 'original')
                if framework not in ['original', 'enhanced', 'hybrid']:
                    raise ValueError(f"Invalid DECISION_FRAMEWORK: {framework}")
                
                # Validate boolean values
                bool_keys = [
                    'SHOW_ENHANCED_METRICS', 'ORIGINAL_STRATEGY_STRICT', 
                    'SHOW_RISK_WARNINGS', 'ENABLE_STRADDLE_STRUCTURE'
                ]
                for key in bool_keys:
                    if key in config:
                        value = config[key].lower()
                        if value not in ['true', 'false']:
                            raise ValueError(f"Invalid boolean value for {key}: {value}")
                
                # Validate trade structure
                structure = config.get('DEFAULT_TRADE_STRUCTURE', 'calendar')
                if structure not in ['calendar', 'straddle', 'auto']:
                    raise ValueError(f"Invalid DEFAULT_TRADE_STRUCTURE: {structure}")
                
                validation_results['valid_configs'] += 1
                print(f"✅ {scenario['name']}: Valid")
                
            except Exception as e:
                validation_results['invalid_configs'] += 1
                validation_results['errors'].append(f"{scenario['name']}: {str(e)}")
                print(f"❌ {scenario['name']}: {str(e)}")
        
        return validation_results


def run_demo_scenarios():
    """Main function to run all demo scenarios."""
    demo = DemoScenarios()
    
    # First validate configurations
    print("Starting Stage 4 Demo Scenarios...")
    validation_results = demo.validate_configuration_scenarios()
    
    if validation_results['invalid_configs'] > 0:
        print(f"\n⚠️ Found {validation_results['invalid_configs']} invalid configurations")
        print("Fix configurations before running scenarios")
        return False
    
    # Run all scenarios
    results = demo.run_all_scenarios("AAPL")
    
    # Check overall success
    success_count = sum(1 for r in results if r.get('status') == 'success')
    total_count = len(results)
    
    if success_count == total_count:
        print(f"\n🎉 All {total_count} demo scenarios completed successfully!")
        print("✅ Stage 4 demo validation: PASS")
        return True
    else:
        print(f"\n⚠️ {total_count - success_count} scenarios failed out of {total_count}")
        print("❌ Stage 4 demo validation: PARTIAL")
        return False


if __name__ == "__main__":
    success = run_demo_scenarios()
    sys.exit(0 if success else 1)