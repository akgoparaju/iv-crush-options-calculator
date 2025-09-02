import React, { useState, useEffect, useMemo, useCallback } from 'react'
import {
  ComposedChart,
  AreaChart,
  LineChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Cell
} from 'recharts'
import { ZoomIn, ZoomOut, RotateCcw, Download, Settings } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { PnLScenarioProps, ChartInteraction, ChartTooltipData } from '@/types/charts'
import { 
  defaultChartTheme, 
  formatChartCurrency, 
  formatChartPercentage, 
  getPnLColor,
  generateChartGradients 
} from '@/utils/chartTheme'
import { generatePnLScenarios, convertToSurfaceData, smoothData } from '@/utils/chartUtils'

interface PnLChartData {
  priceChange: number
  price: number
  pnl: number
  pnlAtExpiration: number
  probability: number
  ivCrushLow: number
  ivCrushMedium: number
  ivCrushHigh: number
}

export const PnLScenarioChart: React.FC<PnLScenarioProps> = ({
  scenarios,
  currentPrice,
  strategy,
  strikePrice,
  interactionEnabled = true,
  height = 400,
  width
}) => {
  const [selectedTimeFrame, setSelectedTimeFrame] = useState(0) // Index in daysToExpiration array
  const [showIVCrush, setShowIVCrush] = useState(false)
  const [chartType, setChartType] = useState<'line' | 'area' | 'heatmap'>('area')
  const [interaction, setInteraction] = useState<ChartInteraction>({
    zoomLevel: 1.0,
    panOffset: [0, 0],
    isHovering: false
  })

  // Process scenario data for chart display
  const chartData = useMemo(() => {
    if (!scenarios || scenarios.length === 0) return []
    
    return scenarios.map(scenario => ({
      priceChange: scenario.priceChange,
      price: scenario.absolutePrice,
      pnl: scenario.pnlValues[selectedTimeFrame] || 0,
      pnlAtExpiration: scenario.pnlValues[scenario.pnlValues.length - 1] || 0,
      probability: scenario.probability || 0,
      ivCrushLow: scenario.ivCrushScenarios.low,
      ivCrushMedium: scenario.ivCrushScenarios.medium,
      ivCrushHigh: scenario.ivCrushScenarios.high
    }))
  }, [scenarios, selectedTimeFrame])

  // Calculate key metrics for display
  const metrics = useMemo(() => {
    if (chartData.length === 0) {
      return { maxProfit: 0, maxLoss: 0, breakevens: [], probabilityOfProfit: 0 }
    }

    const pnlValues = chartData.map(d => d.pnl)
    const maxProfit = Math.max(...pnlValues)
    const maxLoss = Math.min(...pnlValues)
    
    // Find breakeven points (where P&L crosses zero)
    const breakevens: number[] = []
    for (let i = 1; i < chartData.length; i++) {
      const prev = chartData[i - 1]
      const curr = chartData[i]
      if ((prev.pnl <= 0 && curr.pnl > 0) || (prev.pnl > 0 && curr.pnl <= 0)) {
        // Linear interpolation to find exact breakeven point
        const breakeven = prev.priceChange + 
          (0 - prev.pnl) * (curr.priceChange - prev.priceChange) / (curr.pnl - prev.pnl)
        breakevens.push(breakeven)
      }
    }
    
    // Calculate probability of profit
    const profitablePoints = chartData.filter(d => d.pnl > 0)
    const totalProbability = chartData.reduce((sum, d) => sum + d.probability, 0)
    const profitableProbability = profitablePoints.reduce((sum, d) => sum + d.probability, 0)
    const probabilityOfProfit = totalProbability > 0 ? profitableProbability / totalProbability : 0

    return { maxProfit, maxLoss, breakevens, probabilityOfProfit }
  }, [chartData])

  // Custom tooltip component
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || payload.length === 0) return null

    const data = payload[0].payload
    return (
      <div className="bg-white border border-slate-200 rounded-lg shadow-lg p-3 text-sm">
        <div className="font-semibold text-slate-900 mb-2">
          Price: {formatChartCurrency(data.price)} ({formatChartPercentage(data.priceChange)})
        </div>
        <div className="space-y-1">
          <div className={`flex justify-between ${data.pnl >= 0 ? 'text-success-600' : 'text-danger-600'}`}>
            <span>P&L:</span>
            <span className="font-medium">{formatChartCurrency(data.pnl)}</span>
          </div>
          {showIVCrush && (
            <>
              <div className="text-slate-600 text-xs border-t pt-1 mt-1">IV Crush Scenarios:</div>
              <div className="flex justify-between text-xs text-slate-600">
                <span>Low (10%):</span>
                <span>{formatChartCurrency(data.ivCrushLow)}</span>
              </div>
              <div className="flex justify-between text-xs text-slate-600">
                <span>Medium (20%):</span>
                <span>{formatChartCurrency(data.ivCrushMedium)}</span>
              </div>
              <div className="flex justify-between text-xs text-slate-600">
                <span>High (30%):</span>
                <span>{formatChartCurrency(data.ivCrushHigh)}</span>
              </div>
            </>
          )}
          <div className="flex justify-between text-xs text-slate-500 border-t pt-1">
            <span>Probability:</span>
            <span>{(data.probability * 100).toFixed(2)}%</span>
          </div>
        </div>
      </div>
    )
  }

  // Chart control handlers
  const handleZoomIn = () => {
    setInteraction(prev => ({ 
      ...prev, 
      zoomLevel: Math.min(prev.zoomLevel * 1.2, 5) 
    }))
  }

  const handleZoomOut = () => {
    setInteraction(prev => ({ 
      ...prev, 
      zoomLevel: Math.max(prev.zoomLevel / 1.2, 0.5) 
    }))
  }

  const handleReset = () => {
    setInteraction({
      zoomLevel: 1.0,
      panOffset: [0, 0],
      isHovering: false
    })
  }

  // Get available time frames from scenario data
  const timeFrames = useMemo(() => {
    if (!scenarios || scenarios.length === 0) return ['At Expiration']
    return scenarios[0].daysToExpiration.map(days => 
      days === 0 ? 'At Expiration' : `${days} days`
    )
  }, [scenarios])

  return (
    <Card className="p-6">
      <div className="flex flex-col space-y-4">
        {/* Chart Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">
              P&L Scenario Analysis
            </h3>
            <p className="text-sm text-slate-600">
              {strategy === 'calendar' ? 'Calendar Spread' : 'ATM Straddle'} • 
              Strike: {formatChartCurrency(strikePrice)} • 
              Current: {formatChartCurrency(currentPrice)}
            </p>
          </div>
          
          {interactionEnabled && (
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleZoomIn}
                disabled={interaction.zoomLevel >= 5}
              >
                <ZoomIn className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleZoomOut}
                disabled={interaction.zoomLevel <= 0.5}
              >
                <ZoomOut className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleReset}
              >
                <RotateCcw className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>

        {/* Chart Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
          <div className="flex flex-wrap items-center gap-3">
            {/* Time Frame Selector */}
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-slate-700">Time Frame:</label>
              <select
                value={selectedTimeFrame}
                onChange={(e) => setSelectedTimeFrame(Number(e.target.value))}
                className="text-sm border border-slate-300 rounded px-2 py-1"
              >
                {timeFrames.map((frame, index) => (
                  <option key={index} value={index}>
                    {frame}
                  </option>
                ))}
              </select>
            </div>

            {/* Chart Type Toggle */}
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-slate-700">View:</label>
              <select
                value={chartType}
                onChange={(e) => setChartType(e.target.value as 'line' | 'area' | 'heatmap')}
                className="text-sm border border-slate-300 rounded px-2 py-1"
              >
                <option value="area">Area Chart</option>
                <option value="line">Line Chart</option>
              </select>
            </div>
          </div>

          {/* Chart Options */}
          <div className="flex items-center space-x-3">
            <label className="flex items-center space-x-2 text-sm">
              <input
                type="checkbox"
                checked={showIVCrush}
                onChange={(e) => setShowIVCrush(e.target.checked)}
                className="rounded"
              />
              <span>Show IV Crush</span>
            </label>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 bg-slate-50 rounded-lg">
          <div className="text-center">
            <div className="text-xs text-slate-600">Max Profit</div>
            <div className="text-sm font-semibold text-success-600">
              {formatChartCurrency(metrics.maxProfit)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-slate-600">Max Loss</div>
            <div className="text-sm font-semibold text-danger-600">
              {formatChartCurrency(metrics.maxLoss)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-slate-600">Breakeven Range</div>
            <div className="text-sm font-semibold text-slate-700">
              {metrics.breakevens.length > 0 
                ? `${formatChartPercentage(Math.min(...metrics.breakevens))} to ${formatChartPercentage(Math.max(...metrics.breakevens))}`
                : 'N/A'
              }
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-slate-600">Win Rate</div>
            <div className="text-sm font-semibold text-primary-600">
              {formatChartPercentage(metrics.probabilityOfProfit * 100)}
            </div>
          </div>
        </div>

        {/* Chart */}
        <div className="relative">
          <ResponsiveContainer width="100%" height={height}>
            {chartType === 'area' ? (
              <AreaChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={defaultChartTheme.gridColor} />
                <XAxis 
                  dataKey="priceChange"
                  tickFormatter={(value) => `${value.toFixed(0)}%`}
                  stroke={defaultChartTheme.axisColor}
                />
                <YAxis 
                  tickFormatter={formatChartCurrency}
                  stroke={defaultChartTheme.axisColor}
                />
                <Tooltip content={<CustomTooltip />} />
                
                {/* Breakeven reference line */}
                <ReferenceLine y={0} stroke={defaultChartTheme.neutralColor} strokeDasharray="2 2" />
                
                {/* Current price reference line */}
                <ReferenceLine x={0} stroke={defaultChartTheme.textColor} strokeWidth={2} />
                
                {/* Main P&L area */}
                <Area
                  type="monotone"
                  dataKey="pnl"
                  stroke={defaultChartTheme.profitColor}
                  strokeWidth={2}
                  fill="url(#pnlGradient)"
                />
                
                {/* IV Crush scenarios */}
                {showIVCrush && (
                  <>
                    <Line
                      type="monotone"
                      dataKey="ivCrushLow"
                      stroke="#34d399"
                      strokeDasharray="5 5"
                      strokeWidth={1}
                      dot={false}
                      name="IV Crush (10%)"
                    />
                    <Line
                      type="monotone"
                      dataKey="ivCrushMedium"
                      stroke="#fbbf24"
                      strokeDasharray="5 5"
                      strokeWidth={1}
                      dot={false}
                      name="IV Crush (20%)"
                    />
                    <Line
                      type="monotone"
                      dataKey="ivCrushHigh"
                      stroke="#f87171"
                      strokeDasharray="5 5"
                      strokeWidth={1}
                      dot={false}
                      name="IV Crush (30%)"
                    />
                  </>
                )}

                {/* Gradient definitions */}
                <defs>
                  <linearGradient id="pnlGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={defaultChartTheme.profitColor} stopOpacity={0.3} />
                    <stop offset="50%" stopColor={defaultChartTheme.neutralColor} stopOpacity={0.1} />
                    <stop offset="100%" stopColor={defaultChartTheme.lossColor} stopOpacity={0.3} />
                  </linearGradient>
                </defs>
              </AreaChart>
            ) : (
              <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={defaultChartTheme.gridColor} />
                <XAxis 
                  dataKey="priceChange"
                  tickFormatter={(value) => `${value.toFixed(0)}%`}
                  stroke={defaultChartTheme.axisColor}
                />
                <YAxis 
                  tickFormatter={formatChartCurrency}
                  stroke={defaultChartTheme.axisColor}
                />
                <Tooltip content={<CustomTooltip />} />
                
                <ReferenceLine y={0} stroke={defaultChartTheme.neutralColor} strokeDasharray="2 2" />
                <ReferenceLine x={0} stroke={defaultChartTheme.textColor} strokeWidth={2} />
                
                <Line
                  type="monotone"
                  dataKey="pnl"
                  stroke={defaultChartTheme.profitColor}
                  strokeWidth={2}
                  dot={{ r: 2 }}
                  activeDot={{ r: 4, stroke: defaultChartTheme.profitColor, strokeWidth: 2, fill: '#fff' }}
                />
              </LineChart>
            )}
          </ResponsiveContainer>
        </div>

        {/* Chart Legend */}
        {showIVCrush && (
          <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-slate-600">
            <div className="flex items-center space-x-1">
              <div className="w-3 h-0.5 bg-green-400"></div>
              <span>IV Crush (10%)</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-0.5 bg-amber-400"></div>
              <span>IV Crush (20%)</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-0.5 bg-red-400"></div>
              <span>IV Crush (30%)</span>
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}

export default PnLScenarioChart