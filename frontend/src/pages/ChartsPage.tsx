import React, { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { LineChart, BarChart3, TrendingUp, Activity } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Alert } from '@/components/ui/Alert'

// Phase 3 Chart Components
import PnLScenarioChart from '@/components/charts/PnLScenarioChart'
import GreeksChart from '@/components/charts/GreeksChart'
import ChartExporter from '@/components/charts/ChartExporter'
import MobileChartWrapper from '@/components/charts/MobileChartWrapper'

// Integration component
import ChartIntegration from '@/components/analysis/ChartIntegration'

// Utilities
import { generatePnLScenarios, generateGreeksTimeSeries } from '@/utils/chartUtils'
import { useAnalysis } from '@/hooks/useAnalysis'

const ChartsPage: React.FC = () => {
  const [searchParams] = useSearchParams()
  const symbol = searchParams.get('symbol') || 'AAPL'
  const [chartType, setChartType] = useState<'pnl' | 'greeks' | 'integrated'>('integrated')
  
  // Sample data for demonstration (would come from API in production)
  const sampleData = {
    symbol,
    currentPrice: 150.00,
    strike: 150.00,
    netDebit: 2.50,
    maxProfit: 7.50,
    expiration: 30,
    volatility: 0.25,
    riskFreeRate: 0.05
  }

  // Generate chart data
  const pnlScenarios = generatePnLScenarios(
    sampleData.currentPrice,
    sampleData.strike,
    'calendar',
    sampleData.netDebit,
    sampleData.maxProfit,
    [30, 21, 14, 7, 3, 1, 0]
  )

  const greeksData = generateGreeksTimeSeries(
    sampleData.currentPrice,
    sampleData.strike,
    sampleData.expiration,
    sampleData.volatility,
    sampleData.riskFreeRate
  )

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-600">
              <LineChart className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                Analysis Charts
              </h1>
              <p className="text-sm text-slate-600">
                Interactive P&L scenarios and Greeks visualization
              </p>
            </div>
          </div>
          
          {/* Chart Type Selector */}
          <div className="flex items-center space-x-2">
            <Button
              variant={chartType === 'integrated' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setChartType('integrated')}
            >
              <BarChart3 className="h-4 w-4 mr-1" />
              Integrated View
            </Button>
            <Button
              variant={chartType === 'pnl' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setChartType('pnl')}
            >
              <TrendingUp className="h-4 w-4 mr-1" />
              P&L Focus
            </Button>
            <Button
              variant={chartType === 'greeks' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setChartType('greeks')}
            >
              <Activity className="h-4 w-4 mr-1" />
              Greeks Focus
            </Button>
          </div>
        </div>
      </div>

      {/* Alert for Demo Data */}
      <Alert
        variant="info"
        title="Demo Mode"
        description={`Displaying sample chart data for ${symbol}. Run a full analysis from the dashboard to see real data.`}
      />

      {/* Chart Display Area */}
      {chartType === 'integrated' && (
        <ChartIntegration
          analysisData={sampleData}
          symbol={symbol}
          currentPrice={sampleData.currentPrice}
          tradeData={{
            calendar_trade: {
              strike: sampleData.strike,
              net_debit: sampleData.netDebit,
              max_profit: sampleData.maxProfit,
              days_to_expiration: sampleData.expiration
            }
          }}
          isMobile={window.innerWidth < 768}
        />
      )}

      {chartType === 'pnl' && (
        <Card>
          <div className="p-6">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-slate-900">
                P&L Scenario Analysis
              </h2>
              <p className="text-sm text-slate-600 mt-1">
                Profit and loss scenarios across price movements and time decay
              </p>
            </div>
            
            <MobileChartWrapper 
              title="P&L Scenarios"
              config={{
                touchOptimized: window.innerWidth < 768,
                pinchZoom: true,
                swipePan: true,
                stackOnMobile: true,
                simplifiedLayout: window.innerWidth < 768,
                minTouchTarget: 44
              }}
            >
              <PnLScenarioChart
                scenarios={pnlScenarios}
                currentPrice={sampleData.currentPrice}
                strategy="calendar"
                strikePrice={sampleData.strike}
                interactionEnabled={true}
                height={500}
              />
            </MobileChartWrapper>
          </div>
        </Card>
      )}

      {chartType === 'greeks' && (
        <Card>
          <div className="p-6">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-slate-900">
                Greeks Analysis
              </h2>
              <p className="text-sm text-slate-600 mt-1">
                Option sensitivities and risk metrics over price range
              </p>
            </div>
            
            <MobileChartWrapper 
              title="Greeks Time Series"
              config={{
                touchOptimized: window.innerWidth < 768,
                pinchZoom: true,
                swipePan: true,
                stackOnMobile: true,
                simplifiedLayout: window.innerWidth < 768,
                minTouchTarget: 44
              }}
            >
              <GreeksChart
                greeksData={greeksData}
                selectedGreeks={['delta', 'gamma', 'theta', 'vega']}
                timeRange={30}
                currentPrice={sampleData.currentPrice}
                strikePrice={sampleData.strike}
                height={500}
                interactive={true}
              />
            </MobileChartWrapper>
          </div>
        </Card>
      )}

      {/* Chart Information */}
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">
            Chart Features & Controls
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h4 className="font-medium text-slate-900 mb-2">
                Interactive Controls
              </h4>
              <ul className="text-sm text-slate-600 space-y-1">
                <li>• Click and drag to pan</li>
                <li>• Scroll to zoom in/out</li>
                <li>• Hover for detailed tooltips</li>
                <li>• Click legend items to toggle</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium text-slate-900 mb-2">
                Mobile Gestures
              </h4>
              <ul className="text-sm text-slate-600 space-y-1">
                <li>• Pinch to zoom</li>
                <li>• Swipe to navigate</li>
                <li>• Tap for tooltips</li>
                <li>• Double tap to reset</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium text-slate-900 mb-2">
                Export Options
              </h4>
              <ul className="text-sm text-slate-600 space-y-1">
                <li>• PDF reports with charts</li>
                <li>• High-res PNG images</li>
                <li>• Vector SVG graphics</li>
                <li>• JSON data export</li>
              </ul>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default ChartsPage