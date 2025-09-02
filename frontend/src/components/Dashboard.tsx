import React, { useState, useCallback, useRef } from 'react'
import { AlertTriangle, TrendingUp, BarChart3, Settings, RefreshCw, LineChart, Download } from 'lucide-react'
import { Button } from './ui/Button'
import { Card } from './ui/Card'
import { Input } from './ui/Input'
import { Checkbox } from './ui/Checkbox'
import { Alert } from './ui/Alert'
import { LoadingSpinner } from './ui/LoadingSpinner'
import { useAnalysis, useHealthCheck, useSymbolValidation } from '@/hooks/useAnalysis'
import { AnalysisRequest, AnalysisResponse } from '@/types/api'

// Phase 3 Chart Components
import PnLScenarioChart from './charts/PnLScenarioChart'
import GreeksChart from './charts/GreeksChart'
import ChartExporter from './charts/ChartExporter'
import MobileChartWrapper from './charts/MobileChartWrapper'
import ChartComparison from './charts/ChartComparison'
import { generatePnLScenarios, generateGreeksTimeSeries } from '@/utils/chartUtils'

interface AnalysisFormData {
  symbol: string
  includeEarnings: boolean
  includeTrades: boolean
  includePositionSizing: boolean
  includeTradingDecision: boolean
  useDemo: boolean
  expirations: number
  accountSize: number
  riskPerTrade: number
}

const Dashboard: React.FC = () => {
  // Form state
  const [formData, setFormData] = useState<AnalysisFormData>({
    symbol: '',
    includeEarnings: true,
    includeTrades: false,
    includePositionSizing: false,
    includeTradingDecision: false,
    useDemo: false,
    expirations: 2,
    accountSize: 100000,
    riskPerTrade: 0.02
  })

  // Analysis state
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null)
  
  // Chart state (Phase 3 integration)
  const [showCharts, setShowCharts] = useState(true)
  const [chartView, setChartView] = useState<'pnl' | 'greeks' | 'comparison'>('pnl')
  const chartContainerRef = useRef<HTMLDivElement>(null)
  
  // API hooks
  const analysisMutation = useAnalysis()
  const { data: healthData, isLoading: healthLoading } = useHealthCheck()
  const { data: isSymbolValid, isLoading: symbolValidating } = useSymbolValidation(formData.symbol)

  // Form handlers
  const handleInputChange = useCallback((field: keyof AnalysisFormData, value: string | number | boolean) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }, [])

  const handleSymbolChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.toUpperCase().replace(/[^A-Z]/g, '')
    handleInputChange('symbol', value)
  }, [handleInputChange])

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.symbol || formData.symbol.length === 0) {
      return
    }

    const request: AnalysisRequest = {
      symbol: formData.symbol,
      include_earnings: formData.includeEarnings,
      include_trade_construction: formData.includeTrades,
      include_position_sizing: formData.includePositionSizing,
      include_trading_decision: formData.includeTradingDecision,
      use_demo: formData.useDemo,
      expirations_to_check: formData.expirations,
      account_size: formData.accountSize,
      risk_per_trade: formData.riskPerTrade
    }

    try {
      const result = await analysisMutation.mutateAsync(request)
      setAnalysisResult(result)
    } catch (error) {
      console.error('Analysis failed:', error)
    }
  }, [formData, analysisMutation])

  const clearResults = useCallback(() => {
    setAnalysisResult(null)
    analysisMutation.reset()
  }, [analysisMutation])

  // Helper functions
  const isFormValid = formData.symbol.length > 0 && !symbolValidating && isSymbolValid !== false
  const isAnalyzing = analysisMutation.isPending

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-600">
              <TrendingUp className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                Options Analysis Dashboard
              </h1>
              <p className="text-sm text-slate-600">
                Advanced earnings volatility and calendar spread analysis
              </p>
            </div>
          </div>
          
          {/* System Status */}
          <div className="flex items-center space-x-4">
            {healthLoading ? (
              <LoadingSpinner size="sm" />
            ) : healthData?.status === 'healthy' ? (
              <div className="flex items-center space-x-2 text-sm text-success-600">
                <div className="h-2 w-2 bg-success-500 rounded-full"></div>
                <span>System Online</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2 text-sm text-danger-600">
                <AlertTriangle className="h-4 w-4" />
                <span>System Issues</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Analysis Form */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <Card>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="flex items-center space-x-3">
                <BarChart3 className="h-5 w-5 text-primary-600" />
                <h2 className="text-lg font-semibold text-slate-900">
                  Analysis Configuration
                </h2>
              </div>

              {/* Symbol Input */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-700">
                  Stock Symbol
                </label>
                <Input
                  type="text"
                  placeholder="Enter symbol (e.g., AAPL)"
                  value={formData.symbol}
                  onChange={handleSymbolChange}
                  maxLength={5}
                  className={`uppercase ${
                    symbolValidating
                      ? 'border-warning-300'
                      : isSymbolValid === false
                      ? 'border-danger-300'
                      : isSymbolValid === true
                      ? 'border-success-300'
                      : ''
                  }`}
                />
                {symbolValidating && (
                  <p className="text-xs text-warning-600 flex items-center">
                    <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                    Validating symbol...
                  </p>
                )}
                {isSymbolValid === false && formData.symbol && (
                  <p className="text-xs text-danger-600">Invalid symbol</p>
                )}
                {isSymbolValid === true && (
                  <p className="text-xs text-success-600">Valid symbol</p>
                )}
              </div>

              {/* Analysis Options */}
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-slate-700">
                  Analysis Modules
                </h3>
                
                <div className="space-y-3">
                  <Checkbox
                    id="earnings"
                    checked={formData.includeEarnings}
                    onChange={(checked) => handleInputChange('includeEarnings', checked)}
                    label="Earnings Calendar Analysis"
                    description="Trading windows and earnings timing"
                  />
                  
                  <Checkbox
                    id="trades"
                    checked={formData.includeTrades}
                    onChange={(checked) => handleInputChange('includeTrades', checked)}
                    label="Trade Construction"
                    description="Calendar spreads and P&L analysis"
                  />
                  
                  <Checkbox
                    id="position-sizing"
                    checked={formData.includePositionSizing}
                    onChange={(checked) => handleInputChange('includePositionSizing', checked)}
                    label="Position Sizing"
                    description="Kelly criterion and risk management"
                    disabled={!formData.includeTrades}
                  />
                  
                  <Checkbox
                    id="trading-decision"
                    checked={formData.includeTradingDecision}
                    onChange={(checked) => handleInputChange('includeTradingDecision', checked)}
                    label="Trading Decisions"
                    description="Automated decision engine"
                    disabled={!formData.includePositionSizing}
                  />
                </div>
              </div>

              {/* Advanced Options */}
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-slate-700">
                  Advanced Options
                </h3>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-slate-600 mb-1">
                      Expirations
                    </label>
                    <Input
                      type="number"
                      min="1"
                      max="5"
                      value={formData.expirations}
                      onChange={(e) => handleInputChange('expirations', parseInt(e.target.value) || 1)}
                    />
                  </div>
                  
                  <div>
                    <label className="block text-xs text-slate-600 mb-1">
                      Account Size
                    </label>
                    <Input
                      type="number"
                      min="1000"
                      step="1000"
                      value={formData.accountSize}
                      onChange={(e) => handleInputChange('accountSize', parseFloat(e.target.value) || 100000)}
                    />
                  </div>
                </div>
                
                <Checkbox
                  id="demo"
                  checked={formData.useDemo}
                  onChange={(checked) => handleInputChange('useDemo', checked)}
                  label="Use Demo Data"
                  description="Test with synthetic data (no API required)"
                />
              </div>

              {/* Submit Button */}
              <div className="pt-4 border-t border-slate-200">
                <Button
                  type="submit"
                  variant="primary"
                  fullWidth
                  disabled={!isFormValid || isAnalyzing}
                  loading={isAnalyzing}
                >
                  {isAnalyzing ? 'Analyzing...' : 'Run Analysis'}
                </Button>
              </div>
            </form>
          </Card>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-2">
          <Card>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <Settings className="h-5 w-5 text-primary-600" />
                <h2 className="text-lg font-semibold text-slate-900">
                  Analysis Results
                </h2>
              </div>
              
              {analysisResult && (
                <Button
                  variant="ghost"
                  onClick={clearResults}
                  className="text-sm"
                >
                  Clear Results
                </Button>
              )}
            </div>

            {/* Results Display */}
            {analysisMutation.error && (
              <Alert
                variant="error"
                title="Analysis Failed"
                description={analysisMutation.error.message}
              />
            )}

            {isAnalyzing && (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <LoadingSpinner size="lg" className="mb-4" />
                  <p className="text-slate-600">
                    Running options analysis for {formData.symbol}...
                  </p>
                  <p className="text-xs text-slate-500 mt-2">
                    This may take a few seconds
                  </p>
                </div>
              </div>
            )}

            {analysisResult && !isAnalyzing && (
              <div className="space-y-6">
                {/* Success Message */}
                <Alert
                  variant="success"
                  title="Analysis Complete"
                  description={`Successfully analyzed ${analysisResult.symbol} with ${
                    Object.keys(analysisResult).length - 3
                  } modules enabled.`}
                />

                {/* Results Summary */}
                <div className="bg-slate-50 rounded-lg p-4">
                  <h3 className="font-medium text-slate-900 mb-2">
                    Analysis Summary
                  </h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-slate-600">Symbol:</span>
                      <span className="ml-2 font-medium">{analysisResult.symbol}</span>
                    </div>
                    <div>
                      <span className="text-slate-600">Timestamp:</span>
                      <span className="ml-2">{new Date(analysisResult.timestamp).toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-slate-600">Success:</span>
                      <span className={`ml-2 ${analysisResult.success ? 'text-success-600' : 'text-danger-600'}`}>
                        {analysisResult.success ? 'Yes' : 'No'}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-600">Data Source:</span>
                      <span className="ml-2">{analysisResult.data_source}</span>
                    </div>
                  </div>
                </div>

                {/* Chart Controls (Phase 3 Integration) */}
                {formData.includeTrades && (
                  <div className="border-t pt-4">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <LineChart className="h-5 w-5 text-primary-600" />
                        <h3 className="font-medium text-slate-900">
                          Analysis Charts
                        </h3>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Button
                          variant={chartView === 'pnl' ? 'primary' : 'ghost'}
                          size="sm"
                          onClick={() => setChartView('pnl')}
                        >
                          P&L Scenarios
                        </Button>
                        <Button
                          variant={chartView === 'greeks' ? 'primary' : 'ghost'}
                          size="sm"
                          onClick={() => setChartView('greeks')}
                        >
                          Greeks
                        </Button>
                        <Button
                          variant={chartView === 'comparison' ? 'primary' : 'ghost'}
                          size="sm"
                          onClick={() => setChartView('comparison')}
                        >
                          Compare
                        </Button>
                      </div>
                    </div>

                    {/* Chart Display Area */}
                    <div ref={chartContainerRef} className="space-y-4">
                      {chartView === 'pnl' && analysisResult && (
                        <MobileChartWrapper title="P&L Scenario Analysis">
                          <PnLScenarioChart
                            scenarios={generatePnLScenarios(
                              analysisResult.current_price || 100,
                              analysisResult.trade_construction?.calendar_trade?.strike || 100,
                              'calendar',
                              analysisResult.trade_construction?.calendar_trade?.net_debit || 1,
                              analysisResult.trade_construction?.calendar_trade?.max_profit || 5,
                              [30, 21, 14, 7, 3, 1, 0]
                            )}
                            currentPrice={analysisResult.current_price || 100}
                            strategy="calendar"
                            strikePrice={analysisResult.trade_construction?.calendar_trade?.strike || 100}
                            interactionEnabled={true}
                            height={400}
                          />
                        </MobileChartWrapper>
                      )}

                      {chartView === 'greeks' && analysisResult && (
                        <MobileChartWrapper title="Greeks Analysis">
                          <GreeksChart
                            greeksData={generateGreeksTimeSeries(
                              analysisResult.current_price || 100,
                              analysisResult.trade_construction?.calendar_trade?.strike || 100,
                              30,
                              0.25,
                              0.05
                            )}
                            selectedGreeks={['delta', 'gamma', 'theta', 'vega']}
                            timeRange={30}
                            currentPrice={analysisResult.current_price || 100}
                            strikePrice={analysisResult.trade_construction?.calendar_trade?.strike || 100}
                            height={400}
                            interactive={true}
                          />
                        </MobileChartWrapper>
                      )}

                      {chartView === 'comparison' && analysisResult && (
                        <ChartComparison
                          comparisons={[
                            {
                              symbol: analysisResult.symbol,
                              scenarios: generatePnLScenarios(
                                analysisResult.current_price || 100,
                                analysisResult.trade_construction?.calendar_trade?.strike || 100,
                                'calendar',
                                analysisResult.trade_construction?.calendar_trade?.net_debit || 1,
                                analysisResult.trade_construction?.calendar_trade?.max_profit || 5,
                                [30, 21, 14, 7, 3, 1, 0]
                              ),
                              greeksData: generateGreeksTimeSeries(
                                analysisResult.current_price || 100,
                                analysisResult.trade_construction?.calendar_trade?.strike || 100,
                                30,
                                0.25,
                                0.05
                              ),
                              currentPrice: analysisResult.current_price || 100,
                              strikePrice: analysisResult.trade_construction?.calendar_trade?.strike || 100,
                              strategy: 'calendar'
                            }
                          ]}
                          mode="side-by-side"
                        />
                      )}

                      {/* Export Controls */}
                      {chartContainerRef.current && (
                        <ChartExporter
                          chartRef={chartContainerRef}
                          data={{
                            timestamp: new Date().toISOString(),
                            chartType: chartView === 'pnl' ? 'pnl_scenario' : chartView === 'greeks' ? 'greeks_timeseries' : 'combined',
                            data: {
                              pnlScenarios: chartView === 'pnl' ? generatePnLScenarios(
                                analysisResult.current_price || 100,
                                analysisResult.trade_construction?.calendar_trade?.strike || 100,
                                'calendar',
                                analysisResult.trade_construction?.calendar_trade?.net_debit || 1,
                                analysisResult.trade_construction?.calendar_trade?.max_profit || 5,
                                [30, 21, 14, 7, 3, 1, 0]
                              ) : [],
                              greeksTimeSeries: chartView === 'greeks' ? generateGreeksTimeSeries(
                                analysisResult.current_price || 100,
                                analysisResult.trade_construction?.calendar_trade?.strike || 100,
                                30,
                                0.25,
                                0.05
                              ) : []
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
                              selectedMetrics: chartView === 'greeks' ? ['delta', 'gamma', 'theta', 'vega'] : ['pnl']
                            },
                            metadata: {
                              symbol: analysisResult.symbol,
                              currentPrice: analysisResult.current_price || 100,
                              strategy: 'calendar',
                              analysisDate: new Date().toLocaleDateString()
                            }
                          }}
                          fileName={`${analysisResult.symbol}_${chartView}_analysis`}
                        />
                      )}
                    </div>
                  </div>
                )}

                {/* Detailed Results */}
                <div className="space-y-4">
                  {!formData.includeTrades && (
                    <p className="text-sm text-slate-600">
                      Enable "Trade Construction" to view interactive P&L and Greeks charts.
                    </p>
                  )}
                  
                  {/* JSON Preview for Development */}
                  {import.meta.env.DEV && (
                    <details className="border rounded-lg p-4 bg-slate-50">
                      <summary className="cursor-pointer text-sm font-medium text-slate-700">
                        Debug: View Raw JSON Response
                      </summary>
                      <pre className="mt-3 text-xs bg-white p-3 rounded border overflow-x-auto">
                        {JSON.stringify(analysisResult, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            )}

            {!analysisResult && !isAnalyzing && !analysisMutation.error && (
              <div className="text-center py-12 text-slate-500">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-medium mb-2">Ready for Analysis</p>
                <p className="text-sm">
                  Configure your analysis parameters and click "Run Analysis" to begin.
                </p>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}

export default Dashboard