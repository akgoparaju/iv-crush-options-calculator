import React, { useState, useMemo } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { GreeksChartProps } from '@/types/charts'
import {
  greeksColors,
  formatGreekValue,
  defaultChartTheme
} from '@/utils/chartTheme'

export const GreeksChart: React.FC<GreeksChartProps> = ({
  greeksData,
  selectedGreeks,
  timeRange,
  priceRange,
  currentPrice,
  strikePrice,
  height = 400,
  interactive = true
}) => {
  const [visibleGreeks, setVisibleGreeks] = useState(selectedGreeks)
  const [zoomDomain, setZoomDomain] = useState<[number, number] | null>(null)

  // Filter data based on time range and price range
  const filteredData = useMemo(() => {
    let filtered = [...greeksData]
    
    // Apply time range filter
    if (timeRange) {
      filtered = filtered.filter(d => d.daysToExpiration <= timeRange)
    }
    
    // Apply price range filter
    if (priceRange) {
      filtered = filtered.filter(
        d => d.underlyingPrice >= priceRange[0] && d.underlyingPrice <= priceRange[1]
      )
    }
    
    return filtered
  }, [greeksData, timeRange, priceRange])

  // Calculate min/max values for each Greek
  const greekBounds = useMemo(() => {
    const bounds: Record<string, { min: number; max: number }> = {}
    
    visibleGreeks.forEach(greek => {
      const values = filteredData.map(d => d[greek as keyof typeof d] as number)
      bounds[greek] = {
        min: Math.min(...values),
        max: Math.max(...values)
      }
    })
    
    return bounds
  }, [filteredData, visibleGreeks])

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || payload.length === 0) return null

    return (
      <div className="bg-white border border-slate-200 rounded-lg shadow-lg p-3 text-sm">
        <div className="font-semibold text-slate-900 mb-2">
          Price: ${label?.toFixed(2)}
        </div>
        <div className="space-y-1">
          {payload.map((entry: any) => (
            <div key={entry.dataKey} className="flex justify-between items-center gap-4">
              <span style={{ color: entry.color }} className="font-medium">
                {entry.name}:
              </span>
              <span className="font-mono text-xs">
                {formatGreekValue(entry.name, entry.value)}
              </span>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Toggle Greek visibility
  const toggleGreek = (greek: string) => {
    setVisibleGreeks(prev => {
      if (prev.includes(greek as any)) {
        return prev.filter(g => g !== greek)
      } else {
        return [...prev, greek as any]
      }
    })
  }

  // Reset zoom
  const handleResetZoom = () => {
    setZoomDomain(null)
  }

  // Handle chart click for zoom
  const handleChartClick = (e: any) => {
    if (!interactive || !e) return
    
    // Simple zoom implementation
    const { activeLabel } = e
    if (activeLabel && zoomDomain === null) {
      const zoomRange = 10 // ±$10 from clicked price
      setZoomDomain([activeLabel - zoomRange, activeLabel + zoomRange])
    }
  }

  return (
    <Card className="p-6">
      <div className="flex flex-col space-y-4">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">
              Greeks Analysis
            </h3>
            <p className="text-sm text-slate-600">
              Option sensitivities over price range • 
              Strike: ${strikePrice.toFixed(2)} • 
              Current: ${currentPrice.toFixed(2)}
            </p>
          </div>
          
          {interactive && zoomDomain && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleResetZoom}
            >
              Reset Zoom
            </Button>
          )}
        </div>

        {/* Greek Selection Buttons */}
        {interactive && (
          <div className="flex flex-wrap gap-2">
            {(['delta', 'gamma', 'theta', 'vega', 'rho'] as const).map(greek => (
              <Button
                key={greek}
                variant={visibleGreeks.includes(greek) ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => toggleGreek(greek)}
                style={{
                  borderColor: visibleGreeks.includes(greek) ? greeksColors[greek] : undefined,
                  color: visibleGreeks.includes(greek) ? greeksColors[greek] : undefined
                }}
              >
                {greek.charAt(0).toUpperCase() + greek.slice(1)}
              </Button>
            ))}
          </div>
        )}

        {/* Greeks Summary */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 bg-slate-50 rounded-lg">
          {visibleGreeks.map(greek => {
            const currentData = filteredData.find(
              d => Math.abs(d.underlyingPrice - currentPrice) < 0.5
            )
            const value = currentData ? currentData[greek as keyof typeof currentData] as number : 0
            
            return (
              <div key={greek} className="text-center">
                <div className="text-xs text-slate-600 capitalize">{greek}</div>
                <div 
                  className="text-sm font-semibold"
                  style={{ color: greeksColors[greek] }}
                >
                  {formatGreekValue(greek, value)}
                </div>
              </div>
            )
          })}
        </div>

        {/* Chart */}
        <div className="relative">
          <ResponsiveContainer width="100%" height={height}>
            <LineChart 
              data={filteredData} 
              margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
              onClick={handleChartClick}
            >
              <CartesianGrid strokeDasharray="3 3" stroke={defaultChartTheme.gridColor} />
              <XAxis 
                dataKey="underlyingPrice"
                domain={zoomDomain || ['dataMin', 'dataMax']}
                tickFormatter={(value) => `$${value.toFixed(0)}`}
                stroke={defaultChartTheme.axisColor}
              />
              <YAxis 
                stroke={defaultChartTheme.axisColor}
                tickFormatter={(value) => value.toFixed(3)}
              />
              <Tooltip content={<CustomTooltip />} />
              
              {/* Current price reference line */}
              <ReferenceLine 
                x={currentPrice} 
                stroke={defaultChartTheme.textColor} 
                strokeWidth={2}
                strokeDasharray="5 5"
                label="Current"
              />
              
              {/* Strike price reference line */}
              <ReferenceLine 
                x={strikePrice} 
                stroke={defaultChartTheme.neutralColor} 
                strokeWidth={1}
                strokeDasharray="3 3"
                label="Strike"
              />
              
              {/* Greek lines */}
              {visibleGreeks.includes('delta') && (
                <Line
                  type="monotone"
                  dataKey="delta"
                  stroke={greeksColors.delta}
                  strokeWidth={2}
                  dot={false}
                  name="Delta"
                />
              )}
              
              {visibleGreeks.includes('gamma') && (
                <Line
                  type="monotone"
                  dataKey="gamma"
                  stroke={greeksColors.gamma}
                  strokeWidth={2}
                  dot={false}
                  name="Gamma"
                />
              )}
              
              {visibleGreeks.includes('theta') && (
                <Line
                  type="monotone"
                  dataKey="theta"
                  stroke={greeksColors.theta}
                  strokeWidth={2}
                  dot={false}
                  name="Theta"
                />
              )}
              
              {visibleGreeks.includes('vega') && (
                <Line
                  type="monotone"
                  dataKey="vega"
                  stroke={greeksColors.vega}
                  strokeWidth={2}
                  dot={false}
                  name="Vega"
                />
              )}
              
              {visibleGreeks.includes('rho') && (
                <Line
                  type="monotone"
                  dataKey="rho"
                  stroke={greeksColors.rho}
                  strokeWidth={2}
                  dot={false}
                  name="Rho"
                />
              )}
              
              <Legend />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Time Decay Information */}
        <div className="text-xs text-slate-600 space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5" style={{ backgroundColor: greeksColors.theta }}></div>
            <span>Theta represents daily time decay (negative = losing value)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5" style={{ backgroundColor: greeksColors.delta }}></div>
            <span>Delta shows price sensitivity (0.5 = 50% of stock move)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5" style={{ backgroundColor: greeksColors.vega }}></div>
            <span>Vega indicates volatility sensitivity (per 1% IV change)</span>
          </div>
        </div>
      </div>
    </Card>
  )
}

export default GreeksChart