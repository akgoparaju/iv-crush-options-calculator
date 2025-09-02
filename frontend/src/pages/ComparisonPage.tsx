import React, { useState, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Layers, Plus, X, Filter } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Alert } from '@/components/ui/Alert'
import { Badge } from '@/components/ui/Badge'

// Phase 3 Chart Components
import ChartComparison from '@/components/charts/ChartComparison'
import ChartExporter from '@/components/charts/ChartExporter'

// Utilities
import { generatePnLScenarios, generateGreeksTimeSeries } from '@/utils/chartUtils'

interface ComparisonSymbol {
  symbol: string
  currentPrice: number
  strike: number
  strategy: 'calendar' | 'straddle'
}

const ComparisonPage: React.FC = () => {
  const [searchParams] = useSearchParams()
  const initialSymbol = searchParams.get('symbol') || 'AAPL'
  
  const [symbols, setSymbols] = useState<ComparisonSymbol[]>([
    { symbol: initialSymbol, currentPrice: 150, strike: 150, strategy: 'calendar' },
    { symbol: 'GOOGL', currentPrice: 140, strike: 140, strategy: 'calendar' },
  ])
  
  const [newSymbol, setNewSymbol] = useState('')
  const [comparisonMode, setComparisonMode] = useState<'side-by-side' | 'overlay' | 'stacked'>('side-by-side')
  const [showFilters, setShowFilters] = useState(false)

  // Generate comparison data for all symbols
  const comparisonData = useMemo(() => {
    return symbols.map(sym => ({
      symbol: sym.symbol,
      scenarios: generatePnLScenarios(
        sym.currentPrice,
        sym.strike,
        sym.strategy,
        2.5, // Default net debit
        7.5, // Default max profit
        [30, 21, 14, 7, 3, 1, 0]
      ),
      greeksData: generateGreeksTimeSeries(
        sym.currentPrice,
        sym.strike,
        30, // Default expiration
        0.25, // Default volatility
        0.05  // Default risk-free rate
      ),
      currentPrice: sym.currentPrice,
      strikePrice: sym.strike,
      strategy: sym.strategy
    }))
  }, [symbols])

  // Add new symbol for comparison
  const handleAddSymbol = () => {
    if (newSymbol && symbols.length < 4) {
      setSymbols([...symbols, {
        symbol: newSymbol.toUpperCase(),
        currentPrice: 100 + Math.random() * 100, // Mock price
        strike: 100 + Math.random() * 100, // Mock strike
        strategy: 'calendar'
      }])
      setNewSymbol('')
    }
  }

  // Remove symbol from comparison
  const handleRemoveSymbol = (index: number) => {
    if (symbols.length > 1) {
      setSymbols(symbols.filter((_, i) => i !== index))
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-600">
              <Layers className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                Strategy Comparison
              </h1>
              <p className="text-sm text-slate-600">
                Compare multiple options strategies side by side
              </p>
            </div>
          </div>
          
          {/* View Mode Selector */}
          <div className="flex items-center space-x-2">
            <Button
              variant={comparisonMode === 'side-by-side' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setComparisonMode('side-by-side')}
            >
              Side by Side
            </Button>
            <Button
              variant={comparisonMode === 'overlay' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setComparisonMode('overlay')}
            >
              Overlay
            </Button>
            <Button
              variant={comparisonMode === 'stacked' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setComparisonMode('stacked')}
            >
              Stacked
            </Button>
          </div>
        </div>
      </div>

      {/* Symbol Management */}
      <Card>
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900">
              Symbols in Comparison
            </h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
            >
              <Filter className="h-4 w-4 mr-1" />
              {showFilters ? 'Hide' : 'Show'} Filters
            </Button>
          </div>

          {/* Current Symbols */}
          <div className="flex flex-wrap gap-2 mb-4">
            {symbols.map((sym, index) => (
              <Badge
                key={index}
                variant="primary"
                className="px-3 py-2 flex items-center space-x-2"
              >
                <span className="font-medium">{sym.symbol}</span>
                <span className="text-xs opacity-75">
                  ${sym.currentPrice.toFixed(2)}
                </span>
                {symbols.length > 1 && (
                  <button
                    onClick={() => handleRemoveSymbol(index)}
                    className="ml-2 hover:text-danger-500"
                  >
                    <X className="h-3 w-3" />
                  </button>
                )}
              </Badge>
            ))}
          </div>

          {/* Add Symbol */}
          {symbols.length < 4 && (
            <div className="flex items-center space-x-2">
              <Input
                type="text"
                placeholder="Add symbol (e.g., MSFT)"
                value={newSymbol}
                onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
                onKeyPress={(e) => e.key === 'Enter' && handleAddSymbol()}
                maxLength={5}
                className="max-w-xs"
              />
              <Button
                variant="primary"
                size="sm"
                onClick={handleAddSymbol}
                disabled={!newSymbol || symbols.length >= 4}
              >
                <Plus className="h-4 w-4 mr-1" />
                Add
              </Button>
            </div>
          )}

          {symbols.length >= 4 && (
            <Alert
              variant="warning"
              title="Maximum Symbols"
              description="You can compare up to 4 symbols at once for optimal visualization."
            />
          )}
        </div>
      </Card>

      {/* Comparison Chart */}
      <Card>
        <div className="p-6">
          <ChartComparison
            comparisons={comparisonData}
            mode={comparisonMode}
          />
        </div>
      </Card>

      {/* Comparison Summary */}
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">
            Comparison Summary
          </h3>
          
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-100">
                <tr>
                  <th className="px-4 py-2 text-left">Symbol</th>
                  <th className="px-4 py-2 text-right">Current Price</th>
                  <th className="px-4 py-2 text-right">Strike</th>
                  <th className="px-4 py-2 text-center">Strategy</th>
                  <th className="px-4 py-2 text-right">Max Profit</th>
                  <th className="px-4 py-2 text-right">Max Loss</th>
                  <th className="px-4 py-2 text-right">Win Rate</th>
                </tr>
              </thead>
              <tbody>
                {symbols.map((sym, index) => {
                  // Calculate metrics from scenarios
                  const scenarios = comparisonData[index]?.scenarios || []
                  const pnlValues = scenarios.flatMap(s => s.pnlValues)
                  const maxProfit = Math.max(...pnlValues)
                  const maxLoss = Math.min(...pnlValues)
                  const profitableCount = scenarios.filter(s => 
                    s.pnlValues.some(v => v > 0)
                  ).length
                  const winRate = (profitableCount / scenarios.length) * 100

                  return (
                    <tr key={index} className="border-b border-slate-200">
                      <td className="px-4 py-2 font-medium">{sym.symbol}</td>
                      <td className="px-4 py-2 text-right">
                        ${sym.currentPrice.toFixed(2)}
                      </td>
                      <td className="px-4 py-2 text-right">
                        ${sym.strike.toFixed(2)}
                      </td>
                      <td className="px-4 py-2 text-center">
                        <Badge variant="primary">
                          {sym.strategy}
                        </Badge>
                      </td>
                      <td className="px-4 py-2 text-right text-success-600">
                        ${maxProfit.toFixed(2)}
                      </td>
                      <td className="px-4 py-2 text-right text-danger-600">
                        ${maxLoss.toFixed(2)}
                      </td>
                      <td className="px-4 py-2 text-right">
                        {winRate.toFixed(1)}%
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Export Options */}
          <div className="mt-6 pt-4 border-t border-slate-200">
            <ChartExporter
              chartRef={React.createRef()}
              data={{
                timestamp: new Date().toISOString(),
                chartType: 'combined',
                data: {
                  pnlScenarios: comparisonData.flatMap(d => d.scenarios),
                  greeksTimeSeries: comparisonData.flatMap(d => d.greeksData)
                },
                config: {
                  theme: {
                    profitColor: '#10b981',
                    lossColor: '#ef4444',
                    neutralColor: '#64748b',
                    gridColor: '#e2e8f0',
                    textColor: '#374151',
                    backgroundColor: '#ffffff',
                    fontFamily: 'Inter, system-ui, sans-serif',
                    axisColor: '#6b7280'
                  },
                  dimensions: { width: 1200, height: 600 },
                  selectedMetrics: ['pnl', 'delta', 'theta', 'vega']
                },
                metadata: {
                  symbol: symbols.map(s => s.symbol).join(','),
                  currentPrice: symbols[0]?.currentPrice || 100,
                  strategy: 'comparison',
                  analysisDate: new Date().toLocaleDateString()
                }
              }}
              fileName={`comparison_${symbols.map(s => s.symbol).join('_')}`}
            />
          </div>
        </div>
      </Card>
    </div>
  )
}

export default ComparisonPage