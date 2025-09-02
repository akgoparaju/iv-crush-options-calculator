import React, { useState, useMemo } from 'react'
import { Filter, TrendingUp, TrendingDown, Activity } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { PnLScenario, GreeksTimeSeries } from '@/types/charts'
import PnLScenarioChart from './PnLScenarioChart'
import GreeksChart from './GreeksChart'

interface ComparisonData {
  symbol: string
  scenarios: PnLScenario[]
  greeksData: GreeksTimeSeries[]
  currentPrice: number
  strikePrice: number
  strategy: 'calendar' | 'straddle'
}

interface ChartComparisonProps {
  comparisons: ComparisonData[]
  mode: 'side-by-side' | 'overlay' | 'stacked'
}

export const ChartComparison: React.FC<ChartComparisonProps> = ({
  comparisons,
  mode = 'side-by-side'
}) => {
  const [selectedMetric, setSelectedMetric] = useState<'pnl' | 'greeks'>('pnl')
  const [filters, setFilters] = useState({
    minProfit: -Infinity,
    maxLoss: Infinity,
    minProbability: 0,
    timeFrame: 30,
    priceRange: [-20, 20] as [number, number]
  })
  const [visibleComparisons, setVisibleComparisons] = useState<string[]>(
    comparisons.map(c => c.symbol)
  )

  // Apply filters to data
  const filteredComparisons = useMemo(() => {
    return comparisons
      .filter(comp => visibleComparisons.includes(comp.symbol))
      .map(comp => ({
        ...comp,
        scenarios: comp.scenarios.filter(scenario => {
          const maxProfit = Math.max(...scenario.pnlValues)
          const maxLoss = Math.min(...scenario.pnlValues)
          const probability = scenario.probability || 0
          
          return (
            maxProfit >= filters.minProfit &&
            maxLoss <= filters.maxLoss &&
            probability >= filters.minProbability &&
            scenario.priceChange >= filters.priceRange[0] &&
            scenario.priceChange <= filters.priceRange[1]
          )
        })
      }))
  }, [comparisons, visibleComparisons, filters])

  // Calculate comparison metrics
  const comparisonMetrics = useMemo(() => {
    return filteredComparisons.map(comp => {
      const pnlValues = comp.scenarios.flatMap(s => s.pnlValues)
      const maxProfit = Math.max(...pnlValues)
      const maxLoss = Math.min(...pnlValues)
      const avgProfit = pnlValues.reduce((a, b) => a + b, 0) / pnlValues.length
      
      // Calculate win rate
      const profitableScenarios = comp.scenarios.filter(s => 
        s.pnlValues.some(v => v > 0)
      ).length
      const winRate = (profitableScenarios / comp.scenarios.length) * 100
      
      // Greeks metrics
      const currentGreeks = comp.greeksData.find(
        g => Math.abs(g.underlyingPrice - comp.currentPrice) < 0.5
      )
      
      return {
        symbol: comp.symbol,
        maxProfit,
        maxLoss,
        avgProfit,
        winRate,
        delta: currentGreeks?.delta || 0,
        theta: currentGreeks?.theta || 0,
        vega: currentGreeks?.vega || 0
      }
    })
  }, [filteredComparisons])

  // Toggle comparison visibility
  const toggleComparison = (symbol: string) => {
    setVisibleComparisons(prev => {
      if (prev.includes(symbol)) {
        return prev.filter(s => s !== symbol)
      } else {
        return [...prev, symbol]
      }
    })
  }

  // Render charts based on mode
  const renderCharts = () => {
    switch (mode) {
      case 'side-by-side':
        return (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {filteredComparisons.map(comp => (
              <div key={comp.symbol}>
                {selectedMetric === 'pnl' ? (
                  <PnLScenarioChart
                    scenarios={comp.scenarios}
                    currentPrice={comp.currentPrice}
                    strategy={comp.strategy}
                    strikePrice={comp.strikePrice}
                    height={300}
                  />
                ) : (
                  <GreeksChart
                    greeksData={comp.greeksData}
                    selectedGreeks={['delta', 'theta', 'vega']}
                    timeRange={filters.timeFrame}
                    currentPrice={comp.currentPrice}
                    strikePrice={comp.strikePrice}
                    height={300}
                  />
                )}
              </div>
            ))}
          </div>
        )
      
      case 'stacked':
        return (
          <div className="space-y-4">
            {filteredComparisons.map(comp => (
              <div key={comp.symbol}>
                {selectedMetric === 'pnl' ? (
                  <PnLScenarioChart
                    scenarios={comp.scenarios}
                    currentPrice={comp.currentPrice}
                    strategy={comp.strategy}
                    strikePrice={comp.strikePrice}
                    height={250}
                  />
                ) : (
                  <GreeksChart
                    greeksData={comp.greeksData}
                    selectedGreeks={['delta', 'theta', 'vega']}
                    timeRange={filters.timeFrame}
                    currentPrice={comp.currentPrice}
                    strikePrice={comp.strikePrice}
                    height={250}
                  />
                )}
              </div>
            ))}
          </div>
        )
      
      case 'overlay':
        // For overlay mode, we'd need to combine data from multiple sources
        // This is a simplified implementation
        return (
          <div className="relative">
            <div className="absolute inset-0 opacity-50">
              {selectedMetric === 'pnl' && filteredComparisons[0] && (
                <PnLScenarioChart
                  scenarios={filteredComparisons[0].scenarios}
                  currentPrice={filteredComparisons[0].currentPrice}
                  strategy={filteredComparisons[0].strategy}
                  strikePrice={filteredComparisons[0].strikePrice}
                  height={400}
                />
              )}
            </div>
            {filteredComparisons[1] && (
              <div className="relative z-10">
                {selectedMetric === 'pnl' ? (
                  <PnLScenarioChart
                    scenarios={filteredComparisons[1].scenarios}
                    currentPrice={filteredComparisons[1].currentPrice}
                    strategy={filteredComparisons[1].strategy}
                    strikePrice={filteredComparisons[1].strikePrice}
                    height={400}
                  />
                ) : null}
              </div>
            )}
          </div>
        )
      
      default:
        return null
    }
  }

  return (
    <Card className="p-6">
      <div className="flex flex-col space-y-4">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
          <h3 className="text-lg font-semibold text-slate-900">
            Strategy Comparison
          </h3>
          <div className="flex items-center space-x-2">
            <Button
              variant={selectedMetric === 'pnl' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setSelectedMetric('pnl')}
            >
              P&L Analysis
            </Button>
            <Button
              variant={selectedMetric === 'greeks' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setSelectedMetric('greeks')}
            >
              Greeks
            </Button>
          </div>
        </div>

        {/* Comparison Selection */}
        <div className="flex flex-wrap gap-2">
          {comparisons.map(comp => (
            <Button
              key={comp.symbol}
              variant={visibleComparisons.includes(comp.symbol) ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => toggleComparison(comp.symbol)}
            >
              {comp.symbol}
            </Button>
          ))}
        </div>

        {/* Filters */}
        <div className="p-4 bg-slate-50 rounded-lg space-y-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
            <Filter className="h-4 w-4" />
            <span>Filters</span>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-slate-600">Min Profit</label>
              <input
                type="number"
                value={filters.minProfit === -Infinity ? '' : filters.minProfit}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  minProfit: e.target.value ? parseFloat(e.target.value) : -Infinity
                }))}
                className="w-full px-2 py-1 text-sm border border-slate-300 rounded"
                placeholder="Any"
              />
            </div>
            
            <div>
              <label className="text-xs text-slate-600">Max Loss</label>
              <input
                type="number"
                value={filters.maxLoss === Infinity ? '' : filters.maxLoss}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  maxLoss: e.target.value ? parseFloat(e.target.value) : Infinity
                }))}
                className="w-full px-2 py-1 text-sm border border-slate-300 rounded"
                placeholder="Any"
              />
            </div>
            
            <div>
              <label className="text-xs text-slate-600">Min Probability</label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={filters.minProbability}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  minProbability: parseFloat(e.target.value)
                }))}
                className="w-full px-2 py-1 text-sm border border-slate-300 rounded"
              />
            </div>
          </div>
          
          <div>
            <label className="text-xs text-slate-600">
              Price Range: {filters.priceRange[0]}% to {filters.priceRange[1]}%
            </label>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min="-50"
                max="0"
                value={filters.priceRange[0]}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  priceRange: [parseInt(e.target.value), prev.priceRange[1]]
                }))}
                className="flex-1"
              />
              <input
                type="range"
                min="0"
                max="50"
                value={filters.priceRange[1]}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  priceRange: [prev.priceRange[0], parseInt(e.target.value)]
                }))}
                className="flex-1"
              />
            </div>
          </div>
        </div>

        {/* Comparison Metrics */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-100">
              <tr>
                <th className="px-3 py-2 text-left">Symbol</th>
                <th className="px-3 py-2 text-right">Max Profit</th>
                <th className="px-3 py-2 text-right">Max Loss</th>
                <th className="px-3 py-2 text-right">Win Rate</th>
                <th className="px-3 py-2 text-right">Delta</th>
                <th className="px-3 py-2 text-right">Theta</th>
              </tr>
            </thead>
            <tbody>
              {comparisonMetrics.map(metric => (
                <tr key={metric.symbol} className="border-b border-slate-200">
                  <td className="px-3 py-2 font-medium">{metric.symbol}</td>
                  <td className="px-3 py-2 text-right text-success-600">
                    ${metric.maxProfit.toFixed(2)}
                  </td>
                  <td className="px-3 py-2 text-right text-danger-600">
                    ${metric.maxLoss.toFixed(2)}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {metric.winRate.toFixed(1)}%
                  </td>
                  <td className="px-3 py-2 text-right">
                    {metric.delta.toFixed(3)}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {metric.theta.toFixed(3)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Charts */}
        <div className="mt-4">
          {renderCharts()}
        </div>
      </div>
    </Card>
  )
}

export default ChartComparison