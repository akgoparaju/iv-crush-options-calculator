import React, { useState, useCallback, useMemo } from 'react'
import { ChevronDown, ChevronRight, Info, Settings, TrendingUp, DollarSign, Shield } from 'lucide-react'
import { Card } from '../ui/Card'
import { Input } from '../ui/Input'
import { Button } from '../ui/Button'
import { Checkbox } from '../ui/Checkbox'
import { Select } from '../ui/Select'
import { Tooltip } from '../ui/Tooltip'
import { Badge } from '../ui/Badge'

interface AnalysisParameters {
  // Basic Parameters
  symbol: string
  expirations: number
  
  // Module Toggles
  includeEarnings: boolean
  includeTradeConstruction: boolean
  includePositionSizing: boolean
  includeTradingDecision: boolean
  
  // Advanced Options
  tradeStructure: 'calendar' | 'straddle' | 'auto'
  accountSize: number
  riskPerTrade: number
  useDemo: boolean
}

interface ParameterPreset {
  id: string
  name: string
  description: string
  parameters: Partial<AnalysisParameters>
  badge?: 'conservative' | 'moderate' | 'aggressive'
}

const PARAMETER_PRESETS: ParameterPreset[] = [
  {
    id: 'conservative',
    name: 'Conservative Analysis',
    description: 'Basic earnings and calendar spread analysis with lower risk settings',
    parameters: {
      includeEarnings: true,
      includeTradeConstruction: true,
      includePositionSizing: false,
      includeTradingDecision: false,
      tradeStructure: 'calendar',
      riskPerTrade: 0.01
    },
    badge: 'conservative'
  },
  {
    id: 'moderate',
    name: 'Moderate Analysis',
    description: 'Complete analysis with position sizing and moderate risk tolerance',
    parameters: {
      includeEarnings: true,
      includeTradeConstruction: true,
      includePositionSizing: true,
      includeTradingDecision: false,
      tradeStructure: 'auto',
      riskPerTrade: 0.02
    },
    badge: 'moderate'
  },
  {
    id: 'aggressive',
    name: 'Full Analysis Suite',
    description: 'All modules enabled with trading decisions and higher risk tolerance',
    parameters: {
      includeEarnings: true,
      includeTradeConstruction: true,
      includePositionSizing: true,
      includeTradingDecision: true,
      tradeStructure: 'straddle',
      riskPerTrade: 0.03
    },
    badge: 'aggressive'
  }
]

interface ParameterPanelProps {
  parameters: AnalysisParameters
  onParametersChange: (parameters: AnalysisParameters) => void
  onAnalyze: () => void
  isAnalyzing: boolean
  isValid: boolean
}

export const ParameterPanel: React.FC<ParameterPanelProps> = ({
  parameters,
  onParametersChange,
  onAnalyze,
  isAnalyzing,
  isValid
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [showPresets, setShowPresets] = useState(false)

  // Parameter change handler
  const handleParameterChange = useCallback(<K extends keyof AnalysisParameters>(
    field: K,
    value: AnalysisParameters[K]
  ) => {
    onParametersChange({
      ...parameters,
      [field]: value
    })
  }, [parameters, onParametersChange])

  // Apply preset
  const applyPreset = useCallback((preset: ParameterPreset) => {
    onParametersChange({
      ...parameters,
      ...preset.parameters
    })
    setShowPresets(false)
  }, [parameters, onParametersChange])

  // Validation and status
  const moduleCount = useMemo(() => {
    return [
      parameters.includeEarnings,
      parameters.includeTradeConstruction,
      parameters.includePositionSizing,
      parameters.includeTradingDecision
    ].filter(Boolean).length
  }, [parameters])

  const currentPreset = useMemo(() => {
    return PARAMETER_PRESETS.find(preset => {
      return Object.entries(preset.parameters).every(([key, value]) => {
        return parameters[key as keyof AnalysisParameters] === value
      })
    })
  }, [parameters])

  return (
    <div className="space-y-4">
      {/* Header with Preset Selection */}
      <Card className="p-3 sm:p-4 lg:p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Settings className="h-5 w-5 text-primary-600" />
            <h2 className="text-lg font-semibold text-slate-900">
              Analysis Configuration
            </h2>
            {currentPreset && (
              <Badge variant={currentPreset.badge}>
                {currentPreset.name}
              </Badge>
            )}
          </div>
          
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowPresets(!showPresets)}
            className="text-sm"
          >
            {showPresets ? 'Hide' : 'Show'} Presets
            {showPresets ? <ChevronDown className="h-4 w-4 ml-1" /> : <ChevronRight className="h-4 w-4 ml-1" />}
          </Button>
        </div>

        {/* Preset Selection */}
        {showPresets && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-6 p-3 sm:p-4 bg-slate-50 rounded-lg">
            {PARAMETER_PRESETS.map((preset) => (
              <div
                key={preset.id}
                className="border rounded-lg p-3 cursor-pointer hover:bg-white hover:shadow-sm transition-all active:scale-95 touch-manipulation"
                onClick={() => applyPreset(preset)}
              >
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-2 space-y-1 sm:space-y-0">
                  <h3 className="font-medium text-slate-900 text-sm sm:text-base">{preset.name}</h3>
                  <Badge variant={preset.badge} size="sm">
                    {preset.badge}
                  </Badge>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">{preset.description}</p>
              </div>
            ))}
          </div>
        )}

        {/* Basic Parameters Section */}
        <div className="space-y-4">
          <div className="flex items-center space-x-2 pb-2 border-b border-slate-200">
            <TrendingUp className="h-4 w-4 text-primary-600" />
            <h3 className="font-medium text-slate-900">Basic Parameters</h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Stock Symbol"
              name="symbol"
              value={parameters.symbol}
              onChange={(e) => handleParameterChange('symbol', e.target.value.toUpperCase())}
              placeholder="Enter symbol (e.g., AAPL)"
              icon={<TrendingUp className="h-4 w-4" />}
              required
              className="uppercase"
            />
            
            <div className="space-y-1">
              <label className="block text-sm font-medium text-slate-700">
                Expirations to Check
                <Tooltip content="Number of option expiration cycles to analyze">
                  <Info className="h-3 w-3 ml-1 inline text-slate-400" />
                </Tooltip>
              </label>
              <Select
                value={parameters.expirations.toString()}
                onChange={(value) => handleParameterChange('expirations', parseInt(value))}
                options={[
                  { value: '1', label: '1 Expiration' },
                  { value: '2', label: '2 Expirations (Recommended)' },
                  { value: '3', label: '3 Expirations' },
                  { value: '4', label: '4 Expirations' },
                  { value: '5', label: '5 Expirations (Max)' }
                ]}
              />
            </div>
          </div>
        </div>

        {/* Analysis Modules Section */}
        <div className="space-y-4 mt-6">
          <div className="flex items-center justify-between pb-2 border-b border-slate-200">
            <div className="flex items-center space-x-2">
              <Shield className="h-4 w-4 text-primary-600" />
              <h3 className="font-medium text-slate-900">Analysis Modules</h3>
              <Badge variant="info" size="sm">
                {moduleCount} of 4 enabled
              </Badge>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
            <Checkbox
              id="earnings"
              checked={parameters.includeEarnings}
              onChange={(checked) => handleParameterChange('includeEarnings', checked)}
              label="Earnings Calendar Analysis"
              description="Trading windows, BMO/AMC detection, and earnings timing"
            />
            
            <Checkbox
              id="trades"
              checked={parameters.includeTradeConstruction}
              onChange={(checked) => handleParameterChange('includeTradeConstruction', checked)}
              label="Trade Construction"
              description="Calendar spreads, P&L analysis, and Greeks calculations"
            />
            
            <Checkbox
              id="position-sizing"
              checked={parameters.includePositionSizing}
              onChange={(checked) => handleParameterChange('includePositionSizing', checked)}
              label="Position Sizing"
              description="Kelly criterion and risk management analysis"
              disabled={!parameters.includeTradeConstruction}
            />
            
            <Checkbox
              id="trading-decision"
              checked={parameters.includeTradingDecision}
              onChange={(checked) => handleParameterChange('includeTradingDecision', checked)}
              label="Trading Decisions"
              description="Automated decision engine with signal analysis"
              disabled={!parameters.includePositionSizing}
            />
          </div>
        </div>

        {/* Advanced Options Section */}
        <div className="mt-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm w-full justify-between p-2"
          >
            <div className="flex items-center space-x-2">
              <DollarSign className="h-4 w-4 text-primary-600" />
              <span className="font-medium">Advanced Options</span>
            </div>
            {showAdvanced ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </Button>

          {showAdvanced && (
            <div className="mt-4 space-y-4 p-3 sm:p-4 bg-slate-50 rounded-lg">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="block text-sm font-medium text-slate-700">
                    Trade Structure
                    <Tooltip content="Calendar spreads are lower risk, straddles have higher profit potential">
                      <Info className="h-3 w-3 ml-1 inline text-slate-400" />
                    </Tooltip>
                  </label>
                  <Select
                    value={parameters.tradeStructure}
                    onChange={(value) => handleParameterChange('tradeStructure', value as any)}
                    options={[
                      { value: 'calendar', label: 'Calendar (Conservative)' },
                      { value: 'straddle', label: 'Straddle (Aggressive)' },
                      { value: 'auto', label: 'Auto-Select' }
                    ]}
                  />
                </div>

                <Input
                  label="Account Size ($)"
                  name="accountSize"
                  type="number"
                  value={parameters.accountSize}
                  onChange={(e) => handleParameterChange('accountSize', parseFloat(e.target.value) || 100000)}
                  placeholder="100000"
                  min="1000"
                  step="1000"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Risk Per Trade (%)"
                  name="riskPerTrade"
                  type="number"
                  value={parameters.riskPerTrade * 100}
                  onChange={(e) => handleParameterChange('riskPerTrade', (parseFloat(e.target.value) || 2) / 100)}
                  placeholder="2.0"
                  min="0.1"
                  max="10.0"
                  step="0.1"
                />

                <div className="flex items-center space-x-4 pt-2 sm:pt-6">
                  <Checkbox
                    id="demo"
                    checked={parameters.useDemo}
                    onChange={(checked) => handleParameterChange('useDemo', checked)}
                    label="Demo Mode"
                    description="Use synthetic data for testing"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Analysis Button */}
        <div className="mt-6 pt-4 border-t border-slate-200">
          <Button
            onClick={onAnalyze}
            variant="primary"
            size="lg"
            fullWidth
            loading={isAnalyzing}
            disabled={!isValid || isAnalyzing}
            className="text-base"
          >
            {isAnalyzing ? 'Running Analysis...' : 'Run Analysis'}
          </Button>
          
          {!isValid && (
            <p className="text-sm text-danger-600 mt-2 text-center">
              Please enter a valid stock symbol to continue
            </p>
          )}
        </div>
      </Card>
    </div>
  )
}

export default ParameterPanel