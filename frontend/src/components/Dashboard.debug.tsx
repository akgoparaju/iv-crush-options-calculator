import React, { useState } from 'react'
import { Button } from './ui/Button'
import { Card } from './ui/Card'
import { Input } from './ui/Input'
import { Checkbox } from './ui/Checkbox'
import { useAnalysis } from '@/hooks/useAnalysis'
import { AnalysisRequest } from '@/types/api'

interface AnalysisFormData {
  symbol: string
  includeEarnings: boolean
  includeTrades: boolean
  includePositionSizing: boolean
  useDemo: boolean
  expirations: number
}

function DebugDashboard() {
  const [formData, setFormData] = useState<AnalysisFormData>({
    symbol: 'AAPL',
    includeEarnings: true,
    includeTrades: true,
    includePositionSizing: false,
    useDemo: true,
    expirations: 2,
  })

  const analysisMutation = useAnalysis()

  const handleInputChange = (field: keyof AnalysisFormData, value: string | boolean | number) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const request: AnalysisRequest = {
      symbol: formData.symbol,
      include_earnings: formData.includeEarnings,
      include_trade_construction: formData.includeTrades,
      include_position_sizing: formData.includePositionSizing,
      use_demo: formData.useDemo,
      expirations_to_check: formData.expirations,
    }

    console.log('DEBUG: API Base URL:', import.meta.env.VITE_API_URL || 'http://localhost:8000')
    console.log('DEBUG: Making API request with:', request)
    
    try {
      await analysisMutation.mutateAsync(request)
      console.log('DEBUG: API response received:', analysisMutation.data)
    } catch (error) {
      console.error('DEBUG: API request failed:', error)
    }
  }

  const isAnalyzing = analysisMutation.isPending
  const analysisResult = analysisMutation.data
  const hasError = analysisMutation.error

  return (
    <div className="min-h-screen bg-slate-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">
            Debug Dashboard - Position Sizing Issue
          </h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Configuration Panel */}
          <Card>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Stock Symbol
                </label>
                <Input
                  placeholder="Enter symbol (e.g., AAPL)"
                  value={formData.symbol}
                  onChange={(e) => handleInputChange('symbol', e.target.value)}
                />
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-slate-900">Analysis Modules</h3>
                
                <Checkbox
                  id="earnings"
                  checked={formData.includeEarnings}
                  onChange={(checked) => handleInputChange('includeEarnings', checked)}
                  label="Earnings Calendar Analysis"
                />
                
                <Checkbox
                  id="trades"
                  checked={formData.includeTrades}
                  onChange={(checked) => handleInputChange('includeTrades', checked)}
                  label="Trade Construction"
                />
                
                <Checkbox
                  id="position-sizing"
                  checked={formData.includePositionSizing}
                  onChange={(checked) => handleInputChange('includePositionSizing', checked)}
                  label="Position Sizing"
                  disabled={!formData.includeTrades}
                />
                
                <Checkbox
                  id="demo"
                  checked={formData.useDemo}
                  onChange={(checked) => handleInputChange('useDemo', checked)}
                  label="Use Demo Data"
                />
              </div>

              <Button type="submit" disabled={isAnalyzing || !formData.symbol} className="w-full">
                {isAnalyzing ? 'Analyzing...' : 'Run Analysis'}
              </Button>
            </form>
          </Card>

          {/* Results Panel */}
          <Card>
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Debug Results</h3>
            
            {hasError && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-800 font-medium">Error occurred:</p>
                <pre className="text-red-600 text-sm mt-2 whitespace-pre-wrap">
                  {JSON.stringify(hasError, null, 2)}
                </pre>
              </div>
            )}

            {isAnalyzing && (
              <div className="text-center py-8">
                <p className="text-slate-600">Running analysis...</p>
              </div>
            )}

            {analysisResult && (
              <div className="space-y-4">
                <div className="text-sm text-slate-600">
                  Status: {analysisResult.success ? '✅ Success' : '❌ Failed'}
                </div>
                
                <div className="text-sm text-slate-600">
                  Position Sizing Enabled: {formData.includePositionSizing ? '✅ Yes' : '❌ No'}
                </div>

                <div className="text-sm text-slate-600">
                  Position Sizing Data: {analysisResult.position_sizing ? '✅ Present' : '❌ Missing'}
                </div>

                <details className="border rounded-lg p-4 bg-slate-50">
                  <summary className="cursor-pointer text-sm font-medium text-slate-700">
                    View Full Response
                  </summary>
                  <pre className="mt-3 text-xs bg-white p-3 rounded border overflow-x-auto max-h-96">
                    {JSON.stringify(analysisResult, null, 2)}
                  </pre>
                </details>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}

export default DebugDashboard