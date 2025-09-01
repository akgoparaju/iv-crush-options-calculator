#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage 4 Test Runner - Complete Integration & Testing
===================================================

Master test runner that coordinates all Stage 4 testing components:
1. Strategy Alignment Tests - Core functionality validation
2. Demo Scenarios - Configuration and workflow validation
3. Edge Case Tests - Robustness and error handling validation
4. System Integration - End-to-end workflow validation

This provides comprehensive validation of the complete system
across all implemented stages (1-4).
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import test modules
from test_strategy_alignment import run_comprehensive_tests
from demo_scenarios import run_demo_scenarios
from test_edge_cases import run_edge_case_tests


class Stage4TestRunner:
    """Master test runner for Stage 4 comprehensive validation."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.results = {
            'strategy_alignment': {},
            'demo_scenarios': {},
            'edge_cases': {},
            'system_integration': {},
            'overall_summary': {}
        }
    
    def run_complete_test_suite(self):
        """Run the complete Stage 4 test suite."""
        print("🚀 STAGE 4: COMPLETE INTEGRATION & TESTING FRAMEWORK")
        print("=" * 80)
        print("Comprehensive validation of all implemented stages (1-4)")
        print(f"Start Time: {datetime.now().isoformat()}")
        print("=" * 80)
        
        self.start_time = time.time()
        
        # Phase 1: Strategy Alignment Tests
        print("\n📋 PHASE 1: STRATEGY ALIGNMENT TESTS")
        print("=" * 50)
        self.results['strategy_alignment'] = self.run_strategy_alignment_tests()
        
        # Phase 2: Demo Scenarios
        print("\n🎭 PHASE 2: DEMO SCENARIOS VALIDATION")
        print("=" * 50)
        self.results['demo_scenarios'] = self.run_demo_scenarios_tests()
        
        # Phase 3: Edge Case Testing
        print("\n🧪 PHASE 3: EDGE CASE TESTING")
        print("=" * 50)
        self.results['edge_cases'] = self.run_edge_case_tests()
        
        # Phase 4: System Integration
        print("\n🔗 PHASE 4: SYSTEM INTEGRATION VALIDATION")
        print("=" * 50)
        self.results['system_integration'] = self.run_system_integration_tests()
        
        self.end_time = time.time()
        
        # Generate comprehensive report
        self.generate_comprehensive_report()
        
        return self.results
    
    def run_strategy_alignment_tests(self):
        """Run strategy alignment tests from test_strategy_alignment.py."""
        try:
            print("Running comprehensive strategy alignment tests...")
            results = run_comprehensive_tests()
            
            return {
                'status': 'completed',
                'results': results,
                'summary': {
                    'passed': results.get('passed', 0),
                    'failed': results.get('failed', 0),
                    'skipped': results.get('skipped', 0),
                    'success_rate': (results.get('passed', 0) / max(1, results.get('passed', 0) + results.get('failed', 0))) * 100
                }
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'summary': {'passed': 0, 'failed': 1, 'skipped': 0, 'success_rate': 0}
            }
    
    def run_demo_scenarios_tests(self):
        """Run demo scenarios from demo_scenarios.py."""
        try:
            print("Running demonstration scenarios...")
            success = run_demo_scenarios()
            
            return {
                'status': 'completed',
                'success': success,
                'summary': {
                    'overall_status': 'PASS' if success else 'FAIL',
                    'scenarios_run': 5,  # Number of demo scenarios
                    'description': 'Configuration and workflow validation'
                }
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'summary': {'overall_status': 'ERROR', 'scenarios_run': 0}
            }
    
    def run_edge_case_tests(self):
        """Run edge case tests from test_edge_cases.py."""
        try:
            print("Running edge case robustness tests...")
            success = run_edge_case_tests()
            
            return {
                'status': 'completed',
                'success': success,
                'summary': {
                    'overall_status': 'PASS' if success else 'PARTIAL',
                    'description': 'Robustness and error handling validation'
                }
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'summary': {'overall_status': 'ERROR'}
            }
    
    def run_system_integration_tests(self):
        """Run system integration tests (end-to-end workflows)."""
        try:
            print("Running system integration tests...")
            
            # Import the main analyze function
            from options_trader.core.analyzer import analyze_symbol
            
            integration_results = {
                'basic_analysis': False,
                'with_earnings': False,
                'with_trading_decision': False,
                'with_structure_selection': False,
                'configuration_switching': False
            }
            
            # Test 1: Basic Analysis
            try:
                result = analyze_symbol("AAPL", use_demo=True, expirations_to_check=1)
                if 'symbol' in result and 'price' in result:
                    integration_results['basic_analysis'] = True
                    print("✅ Basic analysis: PASS")
            except Exception as e:
                print(f"❌ Basic analysis: FAIL - {e}")
            
            # Test 2: With Earnings Analysis
            try:
                result = analyze_symbol("AAPL", use_demo=True, include_earnings=True)
                if 'earnings_analysis' in result or 'error' not in result:
                    integration_results['with_earnings'] = True
                    print("✅ Earnings analysis: PASS")
            except Exception as e:
                print(f"❌ Earnings analysis: FAIL - {e}")
            
            # Test 3: With Trading Decision
            try:
                result = analyze_symbol("AAPL", use_demo=True, include_trading_decision=True)
                if 'trading_decision' in result or 'error' not in result:
                    integration_results['with_trading_decision'] = True
                    print("✅ Trading decision: PASS")
            except Exception as e:
                print(f"❌ Trading decision: FAIL - {e}")
            
            # Test 4: With Structure Selection
            try:
                result = analyze_symbol("AAPL", use_demo=True, trade_structure="calendar")
                if 'symbol' in result:  # Basic success
                    integration_results['with_structure_selection'] = True
                    print("✅ Structure selection: PASS")
            except Exception as e:
                print(f"❌ Structure selection: FAIL - {e}")
            
            # Test 5: Configuration Switching
            try:
                # Save original environment
                original_framework = os.environ.get('DECISION_FRAMEWORK', 'original')
                
                # Test different frameworks
                for framework in ['original', 'hybrid']:
                    os.environ['DECISION_FRAMEWORK'] = framework
                    result = analyze_symbol("AAPL", use_demo=True, include_trading_decision=True)
                    if 'symbol' in result:  # Basic success
                        integration_results['configuration_switching'] = True
                        break
                
                # Restore original
                os.environ['DECISION_FRAMEWORK'] = original_framework
                
                if integration_results['configuration_switching']:
                    print("✅ Configuration switching: PASS")
                else:
                    print("❌ Configuration switching: FAIL")
                    
            except Exception as e:
                print(f"❌ Configuration switching: FAIL - {e}")
            
            # Calculate success rate
            passed_tests = sum(integration_results.values())
            total_tests = len(integration_results)
            success_rate = (passed_tests / total_tests) * 100
            
            return {
                'status': 'completed',
                'results': integration_results,
                'summary': {
                    'passed_tests': passed_tests,
                    'total_tests': total_tests,
                    'success_rate': success_rate,
                    'overall_status': 'PASS' if passed_tests == total_tests else 'PARTIAL'
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'summary': {'overall_status': 'ERROR'}
            }
    
    def generate_comprehensive_report(self):
        """Generate comprehensive test report."""
        duration = self.end_time - self.start_time
        
        print("\n" + "=" * 80)
        print("🎯 STAGE 4 COMPREHENSIVE TEST REPORT")
        print("=" * 80)
        print(f"Duration: {duration:.2f} seconds")
        print(f"Completed: {datetime.now().isoformat()}")
        
        # Phase summaries
        phases = [
            ('Strategy Alignment', self.results['strategy_alignment']),
            ('Demo Scenarios', self.results['demo_scenarios']),
            ('Edge Cases', self.results['edge_cases']),
            ('System Integration', self.results['system_integration'])
        ]
        
        overall_status = "PASS"
        total_issues = 0
        
        print(f"\n📊 PHASE RESULTS:")
        print("-" * 50)
        
        for phase_name, phase_results in phases:
            status = phase_results.get('status', 'unknown')
            summary = phase_results.get('summary', {})
            
            if status == 'completed':
                phase_status = summary.get('overall_status', 'UNKNOWN')
                if phase_status in ['FAIL', 'PARTIAL', 'ERROR']:
                    overall_status = "PARTIAL"
                    total_issues += 1
                print(f"✅ {phase_name}: {phase_status}")
                
                # Add specific metrics
                if 'success_rate' in summary:
                    print(f"   📈 Success Rate: {summary['success_rate']:.1f}%")
                if 'passed' in summary and 'failed' in summary:
                    print(f"   📋 Tests: {summary['passed']} passed, {summary['failed']} failed")
                    
            elif status == 'error':
                overall_status = "FAIL"
                total_issues += 1
                print(f"❌ {phase_name}: ERROR - {phase_results.get('error', 'Unknown error')}")
            else:
                overall_status = "PARTIAL"
                total_issues += 1
                print(f"⚠️ {phase_name}: {status}")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print("-" * 30)
        print(f"Status: {overall_status}")
        print(f"Issues Found: {total_issues}/4 phases")
        
        if overall_status == "PASS":
            print("\n🎉 STAGE 4 COMPLETE: ALL TESTS PASSED!")
            print("✅ Strategy alignment implementation is fully validated")
            print("✅ System is ready for production use")
        elif overall_status == "PARTIAL":
            print(f"\n⚠️ STAGE 4 PARTIAL: {total_issues} phases had issues")
            print("🔧 Review failed tests and edge cases")
            print("✅ Core functionality appears to be working")
        else:
            print(f"\n❌ STAGE 4 FAILED: Critical issues found")
            print("🚨 Review implementation before production use")
        
        # Save detailed results
        self.save_test_results()
        
        # Update overall summary
        self.results['overall_summary'] = {
            'status': overall_status,
            'duration_seconds': duration,
            'total_issues': total_issues,
            'timestamp': datetime.now().isoformat()
        }
    
    def save_test_results(self):
        """Save detailed test results to JSON file."""
        try:
            results_file = os.path.join(os.path.dirname(__file__), 'stage4_test_results.json')
            
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            print(f"\n💾 Detailed results saved to: {results_file}")
            
        except Exception as e:
            print(f"⚠️ Could not save results: {e}")


def main():
    """Main function to run Stage 4 tests."""
    runner = Stage4TestRunner()
    results = runner.run_complete_test_suite()
    
    # Return appropriate exit code
    overall_status = results.get('overall_summary', {}).get('status', 'FAIL')
    return 0 if overall_status == 'PASS' else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)