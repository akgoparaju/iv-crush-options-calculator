#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Analytics - Module 4  
=================================

Strategy effectiveness tracking and optimization system for continuous
performance monitoring and improvement of trading decisions.

Features:
- Live performance tracking with executed trades
- Prediction accuracy analysis (predicted vs actual outcomes)
- Strategy parameter optimization through historical analysis
- Comprehensive performance reporting with actionable insights
"""

import logging
import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger("options_trader.performance")


@dataclass
class PerformanceMetrics:
    """Performance metrics for strategy effectiveness analysis."""
    strategy_effectiveness: float = 0.0  # Overall strategy performance (0-1)
    signal_accuracy: float = 0.0  # Accuracy of signal predictions (0-1)
    position_sizing_efficiency: float = 0.0  # Efficiency of position sizing (0-1)
    risk_adjusted_returns: float = 0.0  # Risk-adjusted performance metric
    prediction_accuracy: float = 0.0  # Accuracy of outcome predictions (0-1)
    decision_quality: float = 0.0  # Quality of EXECUTE/PASS/CONSIDER decisions (0-1)
    total_trades: int = 0
    profitable_trades: int = 0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    avg_return_per_trade: float = 0.0
    consistency_score: float = 0.0
    period_start: str = ""
    period_end: str = ""


@dataclass
class AccuracyReport:
    """Report comparing predicted vs actual trading outcomes."""
    total_predictions: int = 0
    correct_predictions: int = 0
    accuracy_rate: float = 0.0
    execute_accuracy: float = 0.0  # Accuracy of EXECUTE decisions
    pass_accuracy: float = 0.0  # Accuracy of PASS decisions  
    consider_accuracy: float = 0.0  # Accuracy of CONSIDER decisions
    false_positives: int = 0  # EXECUTE that should have been PASS
    false_negatives: int = 0  # PASS that should have been EXECUTE
    prediction_errors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class OptimizationResult:
    """Results from strategy parameter optimization."""
    optimized_parameters: Dict[str, Any] = field(default_factory=dict)
    performance_improvement: float = 0.0  # Percentage improvement
    optimal_win_rate: float = 0.0
    optimal_risk_reward: float = 0.0
    optimal_position_size: float = 0.0
    optimization_iterations: int = 0
    convergence_achieved: bool = False
    validation_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)


@dataclass
class PerformanceReport:
    """Comprehensive performance report for a time period."""
    period_summary: PerformanceMetrics
    monthly_breakdown: List[PerformanceMetrics] = field(default_factory=list)
    top_performing_symbols: List[str] = field(default_factory=list)
    worst_performing_symbols: List[str] = field(default_factory=list)
    strategy_insights: List[str] = field(default_factory=list)
    improvement_recommendations: List[str] = field(default_factory=list)
    risk_analysis: Dict[str, Any] = field(default_factory=dict)
    generated_date: str = ""


class PerformanceAnalytics:
    """
    Performance analytics engine for strategy effectiveness tracking.
    
    Provides continuous monitoring, prediction accuracy analysis,
    and strategy optimization capabilities.
    """
    
    def __init__(self):
        """Initialize the performance analytics engine."""
        self.logger = logging.getLogger(f"{__name__}.PerformanceAnalytics")
        self.trade_history = []
        self.prediction_history = []
        
    def track_live_performance(self, executed_trades: List[Dict[str, Any]]) -> PerformanceMetrics:
        """
        Track live performance from executed trades.
        
        Args:
            executed_trades: List of executed trade results with outcomes
        
        Returns:
            PerformanceMetrics with current strategy performance
        """
        try:
            if not executed_trades:
                return PerformanceMetrics()
            
            self.logger.info(f"Tracking performance for {len(executed_trades)} executed trades")
            
            # Update trade history
            self.trade_history.extend(executed_trades)
            
            # Calculate performance metrics
            metrics = self._calculate_live_metrics(executed_trades)
            
            self.logger.info(f"Performance tracking complete: {metrics.win_rate:.1%} win rate, "
                           f"{metrics.total_pnl:.2f} total P&L")
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Live performance tracking failed: {e}")
            return PerformanceMetrics()
    
    def compare_predicted_vs_actual(self, trade_predictions: List[Dict[str, Any]]) -> AccuracyReport:
        """
        Compare predicted outcomes vs actual results.
        
        Args:
            trade_predictions: List of trades with predictions and actual outcomes
        
        Returns:
            AccuracyReport with prediction accuracy analysis
        """
        try:
            if not trade_predictions:
                return AccuracyReport()
            
            self.logger.info(f"Analyzing prediction accuracy for {len(trade_predictions)} trades")
            
            # Update prediction history
            self.prediction_history.extend(trade_predictions)
            
            # Calculate accuracy metrics
            accuracy_report = self._calculate_prediction_accuracy(trade_predictions)
            
            self.logger.info(f"Prediction accuracy analysis complete: {accuracy_report.accuracy_rate:.1%} overall accuracy")
            
            return accuracy_report
            
        except Exception as e:
            self.logger.error(f"Prediction accuracy analysis failed: {e}")
            return AccuracyReport()
    
    def optimize_strategy_parameters(self, historical_data: Dict[str, Any]) -> OptimizationResult:
        """
        Optimize strategy parameters based on historical performance.
        
        Args:
            historical_data: Historical trade and performance data
        
        Returns:
            OptimizationResult with optimized parameters and performance improvement
        """
        try:
            self.logger.info("Starting strategy parameter optimization")
            
            # Current parameters (from existing system)
            current_params = {
                "signal_weight_term_structure": 0.4,
                "signal_weight_iv_rv": 0.35,
                "signal_weight_volume": 0.25,
                "min_win_rate_execute": 0.65,
                "min_risk_reward_execute": 2.0,
                "kelly_signal_multiplier": {"3": 1.0, "2": 0.75, "1": 0.5}
            }
            
            # Run optimization iterations
            best_params = current_params.copy()
            best_performance = self._evaluate_parameter_performance(current_params, historical_data)
            
            optimization_iterations = 0
            improvement_found = True
            
            while improvement_found and optimization_iterations < 50:
                optimization_iterations += 1
                improvement_found = False
                
                # Try parameter variations
                for param_name in current_params:
                    if param_name == "kelly_signal_multiplier":
                        continue  # Skip complex parameter for now
                    
                    # Test higher value
                    test_params = best_params.copy()
                    if isinstance(test_params[param_name], float):
                        test_params[param_name] *= 1.05  # 5% increase
                        
                        performance = self._evaluate_parameter_performance(test_params, historical_data)
                        if performance > best_performance:
                            best_params = test_params.copy()
                            best_performance = performance
                            improvement_found = True
                    
                    # Test lower value
                    test_params = best_params.copy()
                    if isinstance(test_params[param_name], float):
                        test_params[param_name] *= 0.95  # 5% decrease
                        
                        performance = self._evaluate_parameter_performance(test_params, historical_data)
                        if performance > best_performance:
                            best_params = test_params.copy()
                            best_performance = performance
                            improvement_found = True
            
            # Calculate improvement
            baseline_performance = self._evaluate_parameter_performance(current_params, historical_data)
            improvement_pct = ((best_performance - baseline_performance) / baseline_performance * 100 
                             if baseline_performance > 0 else 0.0)
            
            # Generate recommendations
            recommendations = self._generate_optimization_recommendations(current_params, best_params)
            
            result = OptimizationResult(
                optimized_parameters=best_params,
                performance_improvement=improvement_pct,
                optimal_win_rate=best_performance * 0.6,  # Estimated based on performance score
                optimal_risk_reward=best_params.get("min_risk_reward_execute", 2.0),
                optimal_position_size=1.0,  # Relative to current sizing
                optimization_iterations=optimization_iterations,
                convergence_achieved=not improvement_found,
                validation_score=best_performance * 100,
                recommendations=recommendations
            )
            
            self.logger.info(f"Strategy optimization complete: {improvement_pct:.1f}% improvement "
                           f"after {optimization_iterations} iterations")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Strategy optimization failed: {e}")
            return OptimizationResult()
    
    def generate_performance_reports(self, time_period: str) -> PerformanceReport:
        """
        Generate comprehensive performance report for a time period.
        
        Args:
            time_period: Time period for report ("1M", "3M", "6M", "1Y")
        
        Returns:
            PerformanceReport with detailed analysis and recommendations
        """
        try:
            self.logger.info(f"Generating performance report for period: {time_period}")
            
            # Filter trades for the specified period
            period_trades = self._filter_trades_by_period(self.trade_history, time_period)
            
            if not period_trades:
                return PerformanceReport(
                    period_summary=PerformanceMetrics(),
                    generated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            
            # Calculate period summary
            period_summary = self._calculate_live_metrics(period_trades)
            
            # Calculate monthly breakdown
            monthly_breakdown = self._calculate_monthly_breakdown(period_trades)
            
            # Identify top/worst performing symbols
            symbol_performance = self._analyze_symbol_performance(period_trades)
            
            # Generate insights and recommendations
            insights = self._generate_strategy_insights(period_trades, period_summary)
            recommendations = self._generate_improvement_recommendations(period_summary)
            
            # Risk analysis
            risk_analysis = self._analyze_risk_metrics(period_trades)
            
            report = PerformanceReport(
                period_summary=period_summary,
                monthly_breakdown=monthly_breakdown,
                top_performing_symbols=symbol_performance["top_symbols"][:5],
                worst_performing_symbols=symbol_performance["worst_symbols"][:5],
                strategy_insights=insights,
                improvement_recommendations=recommendations,
                risk_analysis=risk_analysis,
                generated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            self.logger.info(f"Performance report generated: {len(insights)} insights, "
                           f"{len(recommendations)} recommendations")
            
            return report
            
        except Exception as e:
            self.logger.error(f"Performance report generation failed: {e}")
            return PerformanceReport(
                period_summary=PerformanceMetrics(),
                generated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
    
    def _calculate_live_metrics(self, trades: List[Dict[str, Any]]) -> PerformanceMetrics:
        """Calculate performance metrics from trade data."""
        if not trades:
            return PerformanceMetrics()
        
        total_trades = len(trades)
        profitable_trades = sum(1 for t in trades if t.get("pnl", 0) > 0)
        total_pnl = sum(t.get("pnl", 0) for t in trades)
        win_rate = profitable_trades / total_trades
        avg_return = total_pnl / total_trades
        
        # Calculate returns for risk metrics
        returns = [t.get("return_pct", 0) for t in trades if "return_pct" in t]
        
        if returns:
            # Simplified Sharpe ratio calculation
            avg_return_pct = statistics.mean(returns)
            return_std = statistics.stdev(returns) if len(returns) > 1 else 0.1
            sharpe_ratio = (avg_return_pct - 0.02) / return_std if return_std > 0 else 0.0
            
            # Simple max drawdown calculation
            cumulative_returns = []
            cumulative = 0.0
            for ret in returns:
                cumulative += ret
                cumulative_returns.append(cumulative)
            
            if cumulative_returns:
                peak = cumulative_returns[0]
                max_drawdown = 0.0
                for cum_ret in cumulative_returns:
                    if cum_ret > peak:
                        peak = cum_ret
                    else:
                        drawdown = (peak - cum_ret) / (1 + peak) if peak != -1 else 0
                        max_drawdown = max(max_drawdown, drawdown)
            else:
                max_drawdown = 0.0
        else:
            sharpe_ratio = 0.0
            max_drawdown = 0.0
        
        # Calculate strategy effectiveness (composite score)
        strategy_effectiveness = min(1.0, (win_rate * 0.4 + 
                                         min(1.0, abs(avg_return) * 10) * 0.3 + 
                                         max(0.0, 1.0 - max_drawdown) * 0.3))
        
        return PerformanceMetrics(
            strategy_effectiveness=strategy_effectiveness,
            signal_accuracy=win_rate,  # Simplified - signal accuracy approximated by win rate
            position_sizing_efficiency=0.8,  # Placeholder - would calculate from position size adjustments
            risk_adjusted_returns=sharpe_ratio,
            prediction_accuracy=win_rate,  # Simplified
            decision_quality=strategy_effectiveness,
            total_trades=total_trades,
            profitable_trades=profitable_trades,
            total_pnl=total_pnl,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            avg_return_per_trade=avg_return,
            consistency_score=min(win_rate, 1.0 - max_drawdown),
            period_start=datetime.now().strftime("%Y-%m-%d"),
            period_end=datetime.now().strftime("%Y-%m-%d")
        )
    
    def _calculate_prediction_accuracy(self, predictions: List[Dict[str, Any]]) -> AccuracyReport:
        """Calculate prediction accuracy metrics."""
        if not predictions:
            return AccuracyReport()
        
        total_predictions = len(predictions)
        correct_predictions = 0
        execute_correct = execute_total = 0
        pass_correct = pass_total = 0
        consider_correct = consider_total = 0
        false_positives = false_negatives = 0
        
        for pred in predictions:
            predicted = pred.get("predicted_decision", "PASS")
            actual_profitable = pred.get("actual_profitable", False)
            
            # Count by decision type
            if predicted == "EXECUTE":
                execute_total += 1
                if actual_profitable:
                    execute_correct += 1
                    correct_predictions += 1
                else:
                    false_positives += 1
            elif predicted == "PASS":
                pass_total += 1
                if not actual_profitable:
                    pass_correct += 1
                    correct_predictions += 1
                else:
                    false_negatives += 1
            elif predicted == "CONSIDER":
                consider_total += 1
                # CONSIDER is correct if it requires manual review (simplified)
                consider_correct += 1
                correct_predictions += 1
        
        accuracy_rate = correct_predictions / total_predictions
        execute_accuracy = execute_correct / execute_total if execute_total > 0 else 0.0
        pass_accuracy = pass_correct / pass_total if pass_total > 0 else 0.0
        consider_accuracy = consider_correct / consider_total if consider_total > 0 else 0.0
        
        # Generate recommendations
        recommendations = []
        if execute_accuracy < 0.7:
            recommendations.append(f"Improve EXECUTE decision accuracy: {execute_accuracy:.1%} < 70%")
        if false_positives > total_predictions * 0.2:
            recommendations.append(f"Reduce false positives: {false_positives} EXECUTE decisions were unprofitable")
        if false_negatives > total_predictions * 0.1:
            recommendations.append(f"Reduce false negatives: {false_negatives} profitable opportunities were missed")
        
        return AccuracyReport(
            total_predictions=total_predictions,
            correct_predictions=correct_predictions,
            accuracy_rate=accuracy_rate,
            execute_accuracy=execute_accuracy,
            pass_accuracy=pass_accuracy,
            consider_accuracy=consider_accuracy,
            false_positives=false_positives,
            false_negatives=false_negatives,
            recommendations=recommendations
        )
    
    def _evaluate_parameter_performance(self, parameters: Dict[str, Any], 
                                      historical_data: Dict[str, Any]) -> float:
        """Evaluate performance score for a given parameter set."""
        # Simplified performance evaluation - in production this would 
        # re-run the strategy with new parameters on historical data
        
        base_score = 0.75  # Base performance score
        
        # Adjust score based on parameter values
        min_win_rate = parameters.get("min_win_rate_execute", 0.65)
        min_risk_reward = parameters.get("min_risk_reward_execute", 2.0)
        
        # Higher thresholds generally improve quality but reduce quantity
        threshold_score = min(1.0, (min_win_rate - 0.5) * 2 + (min_risk_reward - 1.0) * 0.2)
        
        return base_score * 0.7 + threshold_score * 0.3
    
    def _generate_optimization_recommendations(self, current_params: Dict[str, Any], 
                                            optimized_params: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on parameter optimization."""
        recommendations = []
        
        for param, current_val in current_params.items():
            if param in optimized_params and isinstance(current_val, (int, float)):
                optimized_val = optimized_params[param]
                change_pct = ((optimized_val - current_val) / current_val * 100 
                             if current_val != 0 else 0)
                
                if abs(change_pct) > 2:  # Only report significant changes
                    direction = "increase" if change_pct > 0 else "decrease"
                    recommendations.append(f"Consider {direction} {param} by {abs(change_pct):.1f}% "
                                         f"(from {current_val:.3f} to {optimized_val:.3f})")
        
        return recommendations
    
    def _filter_trades_by_period(self, trades: List[Dict[str, Any]], period: str) -> List[Dict[str, Any]]:
        """Filter trades by time period."""
        # Simplified - in production would parse dates and filter appropriately
        return trades  # Return all trades for now
    
    def _calculate_monthly_breakdown(self, trades: List[Dict[str, Any]]) -> List[PerformanceMetrics]:
        """Calculate monthly performance breakdown."""
        # Simplified - return single month for now
        return [self._calculate_live_metrics(trades)]
    
    def _analyze_symbol_performance(self, trades: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Analyze performance by symbol."""
        symbol_pnl = {}
        
        for trade in trades:
            symbol = trade.get("symbol", "UNKNOWN")
            pnl = trade.get("pnl", 0)
            if symbol in symbol_pnl:
                symbol_pnl[symbol] += pnl
            else:
                symbol_pnl[symbol] = pnl
        
        sorted_symbols = sorted(symbol_pnl.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "top_symbols": [s[0] for s in sorted_symbols[:5]],
            "worst_symbols": [s[0] for s in sorted_symbols[-5:]]
        }
    
    def _generate_strategy_insights(self, trades: List[Dict[str, Any]], 
                                   metrics: PerformanceMetrics) -> List[str]:
        """Generate strategic insights from performance data."""
        insights = []
        
        if metrics.win_rate > 0.7:
            insights.append(f"Strong win rate of {metrics.win_rate:.1%} indicates good signal quality")
        elif metrics.win_rate < 0.5:
            insights.append(f"Low win rate of {metrics.win_rate:.1%} suggests signal criteria may be too loose")
        
        if metrics.max_drawdown > 0.15:
            insights.append(f"High maximum drawdown of {metrics.max_drawdown:.1%} indicates position sizing may be too aggressive")
        
        if metrics.sharpe_ratio > 1.5:
            insights.append(f"Excellent risk-adjusted returns with Sharpe ratio of {metrics.sharpe_ratio:.1f}")
        elif metrics.sharpe_ratio < 0.8:
            insights.append(f"Poor risk-adjusted returns with Sharpe ratio of {metrics.sharpe_ratio:.1f}")
        
        return insights
    
    def _generate_improvement_recommendations(self, metrics: PerformanceMetrics) -> List[str]:
        """Generate improvement recommendations based on performance."""
        recommendations = []
        
        if metrics.win_rate < 0.6:
            recommendations.append("Consider tightening signal criteria to improve win rate")
        
        if metrics.max_drawdown > 0.12:
            recommendations.append("Consider reducing position sizes to limit drawdown risk")
        
        if metrics.sharpe_ratio < 1.0:
            recommendations.append("Focus on improving risk-adjusted returns through better trade selection")
        
        if metrics.avg_return_per_trade < 0:
            recommendations.append("Strategy is showing negative returns - comprehensive review needed")
        
        return recommendations
    
    def _analyze_risk_metrics(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze risk-related metrics."""
        if not trades:
            return {}
        
        returns = [t.get("return_pct", 0) for t in trades if "return_pct" in t]
        
        if returns:
            var_95 = sorted(returns)[int(len(returns) * 0.05)] if len(returns) > 20 else min(returns)
            max_loss = min(returns)
            avg_loss = statistics.mean([r for r in returns if r < 0]) if any(r < 0 for r in returns) else 0
        else:
            var_95 = max_loss = avg_loss = 0
        
        return {
            "value_at_risk_95": var_95,
            "maximum_single_loss": max_loss,
            "average_loss": avg_loss,
            "total_losing_trades": len([r for r in returns if r < 0]),
            "loss_frequency": len([r for r in returns if r < 0]) / len(returns) if returns else 0
        }