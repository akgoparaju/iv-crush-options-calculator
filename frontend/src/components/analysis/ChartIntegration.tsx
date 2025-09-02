import React, { useState, useRef, useMemo } from 'react'
import { LineChart, Download, TrendingUp, Activity, Layers, Maximize2 } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'

// Phase 3 Chart Components
import PnLScenarioChart from '@/components/charts/PnLScenarioChart'
import GreeksChart from '@/components/charts/GreeksChart'
import ChartExporter from '@/components/charts/ChartExporter'
import MobileChartWrapper from '@/components/charts/MobileChartWrapper'
import ChartComparison from '@/components/charts/ChartComparison'

// Utilities
import { generatePnLScenarios, generateGreeksTimeSeries } from '@/utils/chartUtils'

interface ChartIntegrationProps {
  analysisData: any // Will be properly typed with AnalysisResponse
  symbol: string
  currentPrice: number
  tradeData?: any // Trade construction data
  comparisonSymbols?: string[] // For multi-symbol comparison
  isMobile?: boolean
}

export const ChartIntegration: React.FC<ChartIntegrationProps> = ({
  analysisData,
  symbol,
  currentPrice,
  tradeData,
  comparisonSymbols = [],
  isMobile = false
}) => {
  const [activeChart, setActiveChart] = useState<'pnl' | 'greeks' | 'comparison'>('pnl')
  const [fullscreenChart, setFullscreenChart] = useState(false)
  const chartContainerRef = useRef<HTMLDivElement>(null)

  // Extract trade parameters from analysis data
  const tradeParams = useMemo(() => {
    if (!tradeData?.calendar_trade) {
      return {
        strike: currentPrice,
        netDebit: 1,
        maxProfit: 5,
        expiration: 30
      }
    }
    
    return {
      strike: tradeData.calendar_trade.strike,
      netDebit: tradeData.calendar_trade.net_debit,
      maxProfit: tradeData.calendar_trade.max_profit || 5,
      expiration: tradeData.calendar_trade.days_to_expiration || 30
    }
  }, [tradeData, currentPrice])

  // Generate scenario data
  const scenarioData = useMemo(() => {
    return generatePnLScenarios(
      currentPrice,
      tradeParams.strike,
      'calendar',
      tradeParams.netDebit,
      tradeParams.maxProfit,
      [30, 21, 14, 7, 3, 1, 0]
    )
  }, [currentPrice, tradeParams])

  // Generate Greeks data
  const greeksData = useMemo(() => {
    return generateGreeksTimeSeries(
      currentPrice,
      tradeParams.strike,
      tradeParams.expiration,
      0.25, // Default volatility
      0.05  // Default risk-free rate
    )
  }, [currentPrice, tradeParams])

  // Export data configuration
  const exportData = useMemo(() => ({
    timestamp: new Date().toISOString(),
    chartType: activeChart === 'pnl' ? 'pnl_scenario' : activeChart === 'greeks' ? 'greeks_timeseries' : 'combined',
    data: {
      pnlScenarios: activeChart === 'pnl' ? scenarioData : [],
      greeksTimeSeries: activeChart === 'greeks' ? greeksData : []
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
      dimensions: { width: 800, height: 400 },
      selectedMetrics: activeChart === 'greeks' ? ['delta', 'gamma', 'theta', 'vega'] : ['pnl']
    },
    metadata: {
      symbol,
      currentPrice,
      strategy: 'calendar',
      analysisDate: new Date().toLocaleDateString()
    }
  }), [activeChart, scenarioData, greeksData, symbol, currentPrice])

  // Generate comparison data for multiple symbols
  const comparisonData = useMemo(() => {
    const symbols = [symbol, ...comparisonSymbols].slice(0, 3) // Limit to 3 for display
    
    return symbols.map(sym => ({
      symbol: sym,
      scenarios: scenarioData,
      greeksData: greeksData,
      currentPrice: currentPrice,
      strikePrice: tradeParams.strike,
      strategy: 'calendar' as const
    }))
  }, [symbol, comparisonSymbols, scenarioData, greeksData, currentPrice, tradeParams.strike])

  // Toggle fullscreen
  const handleFullscreen = () => {
    if (!fullscreenChart && chartContainerRef.current) {
      chartContainerRef.current.requestFullscreen()
      setFullscreenChart(true)
    } else if (document.fullscreenElement) {
      document.exitFullscreen()
      setFullscreenChart(false)
    }
  }

  return (
    <Card className="overflow-hidden">
      {/* Chart Header */}
      <div className="p-4 border-b border-slate-200 bg-slate-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <LineChart className="h-5 w-5 text-primary-600" />
            <h3 className="text-lg font-semibold text-slate-900">
              Interactive Analysis Charts
            </h3>
            {tradeData && (
              <Badge variant="success">
                Trade Data Available
              </Badge>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleFullscreen}
            >
              <Maximize2 className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Chart Navigation */}
        <div className="mt-4 flex flex-wrap gap-2">
          <Button
            variant={activeChart === 'pnl' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setActiveChart('pnl')}
          >
            <TrendingUp className="h-4 w-4 mr-1" />
            P&L Scenarios
          </Button>
          <Button
            variant={activeChart === 'greeks' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setActiveChart('greeks')}
          >
            <Activity className="h-4 w-4 mr-1" />
            Greeks Analysis
          </Button>
          {comparisonSymbols.length > 0 && (
            <Button
              variant={activeChart === 'comparison' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setActiveChart('comparison')}
            >
              <Layers className="h-4 w-4 mr-1" />
              Compare ({comparisonSymbols.length + 1})
            </Button>
          )}
        </div>
      </div>

      {/* Chart Content */}
      <div ref={chartContainerRef} className="p-4">
        {activeChart === 'pnl' && (
          <MobileChartWrapper 
            title="P&L Scenario Analysis"
            config={{
              touchOptimized: isMobile,
              pinchZoom: true,
              swipePan: true,
              stackOnMobile: isMobile,
              simplifiedLayout: isMobile,
              minTouchTarget: 44
            }}
          >
            <PnLScenarioChart
              scenarios={scenarioData}
              currentPrice={currentPrice}
              strategy="calendar"
              strikePrice={tradeParams.strike}
              interactionEnabled={!isMobile}
              height={isMobile ? 300 : 400}
            />
          </MobileChartWrapper>
        )}

        {activeChart === 'greeks' && (
          <MobileChartWrapper 
            title="Greeks Time Series"
            config={{
              touchOptimized: isMobile,
              pinchZoom: true,
              swipePan: true,
              stackOnMobile: isMobile,
              simplifiedLayout: isMobile,
              minTouchTarget: 44
            }}
          >
            <GreeksChart
              greeksData={greeksData}
              selectedGreeks={['delta', 'gamma', 'theta', 'vega']}
              timeRange={30}
              currentPrice={currentPrice}
              strikePrice={tradeParams.strike}
              height={isMobile ? 300 : 400}
              interactive={!isMobile}
            />
          </MobileChartWrapper>
        )}

        {activeChart === 'comparison' && (
          <ChartComparison
            comparisons={comparisonData}
            mode={isMobile ? 'stacked' : 'side-by-side'}
          />
        )}

        {/* Export Section */}
        <div className="mt-6 pt-4 border-t border-slate-200">
          <ChartExporter
            chartRef={chartContainerRef}
            data={exportData}
            fileName={`${symbol}_${activeChart}_analysis`}
          />
        </div>
      </div>

      {/* Chart Information Footer */}
      <div className="px-4 pb-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="flex items-start space-x-2">
            <LineChart className="h-5 w-5 text-blue-600 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-sm font-medium text-blue-900">
                Chart Features
              </h4>
              <ul className="mt-1 text-xs text-blue-700 space-y-1">
                {activeChart === 'pnl' && (
                  <>
                    <li>• Interactive zoom and pan controls</li>
                    <li>• Time decay visualization across multiple dates</li>
                    <li>• IV crush scenario modeling</li>
                    <li>• Breakeven and probability calculations</li>
                  </>
                )}
                {activeChart === 'greeks' && (
                  <>
                    <li>• Real-time Greeks calculations</li>
                    <li>• Toggle individual Greek displays</li>
                    <li>• Price sensitivity analysis</li>
                    <li>• Time decay visualization</li>
                  </>
                )}
                {activeChart === 'comparison' && (
                  <>
                    <li>• Compare multiple strategies</li>
                    <li>• Side-by-side metric analysis</li>
                    <li>• Dynamic filtering options</li>
                    <li>• Unified risk assessment</li>
                  </>
                )}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}

export default ChartIntegration