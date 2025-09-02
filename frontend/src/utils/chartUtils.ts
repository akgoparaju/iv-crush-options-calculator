import { PnLScenario, GreeksTimeSeries, PnLSurfaceData, ChartDataPoint, ChartExportData } from '@/types/charts'
import * as d3 from 'd3'

/**
 * Calculate P&L scenarios for different price points and time decay
 */
export const generatePnLScenarios = (
  currentPrice: number,
  strikePrice: number,
  strategy: 'calendar' | 'straddle',
  netDebit: number,
  maxProfit: number,
  daysToExpiration: number[] = [30, 21, 14, 7, 3, 1, 0]
): PnLScenario[] => {
  const priceRange = 0.3 // ±30% from current price
  const priceStep = 0.02 // 2% increments
  const scenarios: PnLScenario[] = []

  // Generate price points from -30% to +30%
  for (let change = -priceRange; change <= priceRange; change += priceStep) {
    const absolutePrice = currentPrice * (1 + change)
    const priceChange = change * 100 // Convert to percentage
    
    // Calculate P&L for each time point
    const pnlValues = daysToExpiration.map(days => {
      return calculatePnLForPriceAndTime(
        absolutePrice,
        strikePrice,
        strategy,
        netDebit,
        days,
        currentPrice
      )
    })

    // Calculate IV crush scenarios
    const basePnL = pnlValues[0] // Current P&L
    const ivCrushScenarios = {
      high: basePnL * 0.7,   // 30% IV crush
      medium: basePnL * 0.8, // 20% IV crush
      low: basePnL * 0.9     // 10% IV crush
    }

    // Estimate probability using normal distribution
    const probability = calculatePriceProbability(priceChange)

    scenarios.push({
      priceChange,
      absolutePrice,
      daysToExpiration,
      pnlValues,
      ivCrushScenarios,
      probability
    })
  }

  return scenarios
}

/**
 * Calculate P&L for a specific price and time combination
 */
const calculatePnLForPriceAndTime = (
  price: number,
  strike: number,
  strategy: 'calendar' | 'straddle',
  netDebit: number,
  daysToExpiration: number,
  currentPrice: number
): number => {
  const moneyness = price / strike
  const timeValue = Math.max(0, daysToExpiration / 30) // Simplified time decay
  
  if (strategy === 'calendar') {
    // Calendar spread P&L calculation
    if (daysToExpiration === 0) {
      // At expiration, only intrinsic value
      return Math.min(Math.max(0, Math.abs(price - strike)) - netDebit, 
                     strike * 0.05 - netDebit) // Max profit cap
    } else {
      // Time value considerations
      const distanceFromStrike = Math.abs(moneyness - 1)
      const optimalDistance = 0.05 // 5% from strike is optimal
      
      if (distanceFromStrike <= optimalDistance) {
        return (strike * 0.05 - netDebit) * (timeValue * 0.8 + 0.2)
      } else {
        return -netDebit * (1 - timeValue * 0.5)
      }
    }
  } else {
    // Straddle P&L calculation
    const intrinsicValue = Math.abs(price - strike)
    const breakeven = strike * 0.15 // Typical straddle breakeven range
    
    if (intrinsicValue > breakeven) {
      return -(intrinsicValue - breakeven) // Loss beyond breakeven
    } else {
      return netDebit * (1 - intrinsicValue / breakeven) // Profit within range
    }
  }
}

/**
 * Calculate probability of price occurrence using normal distribution
 */
const calculatePriceProbability = (priceChangePercent: number): number => {
  // Assume 20% annual volatility, adjust for time frame
  const volatility = 0.20
  const timeFrame = 30 / 365 // 30 days
  const adjustedVol = volatility * Math.sqrt(timeFrame)
  
  // Normal distribution probability
  const standardScore = Math.abs(priceChangePercent / 100) / adjustedVol
  return Math.exp(-0.5 * standardScore * standardScore) / Math.sqrt(2 * Math.PI)
}

/**
 * Generate Greeks time series data
 */
export const generateGreeksTimeSeries = (
  currentPrice: number,
  strikePrice: number,
  daysToExpiration: number,
  volatility: number = 0.25,
  riskFreeRate: number = 0.05
): GreeksTimeSeries[] => {
  const timeSeries: GreeksTimeSeries[] = []
  const priceRange = 0.2 // ±20% price range
  const pricePoints = 21 // Number of price points
  
  for (let i = 0; i < pricePoints; i++) {
    const priceMultiplier = 1 + (priceRange * (2 * i / (pricePoints - 1) - 1))
    const underlyingPrice = currentPrice * priceMultiplier
    
    // Calculate Greeks using simplified Black-Scholes approximations
    const greeks = calculateGreeks(
      underlyingPrice,
      strikePrice,
      daysToExpiration / 365,
      volatility,
      riskFreeRate
    )
    
    timeSeries.push({
      daysToExpiration,
      underlyingPrice,
      ...greeks
    })
  }
  
  return timeSeries
}

/**
 * Simplified Greeks calculations (Black-Scholes approximations)
 */
const calculateGreeks = (
  spot: number,
  strike: number,
  timeToExpiry: number,
  volatility: number,
  riskFreeRate: number
) => {
  const d1 = (Math.log(spot / strike) + (riskFreeRate + 0.5 * volatility * volatility) * timeToExpiry) / 
             (volatility * Math.sqrt(timeToExpiry))
  const d2 = d1 - volatility * Math.sqrt(timeToExpiry)
  
  // Standard normal CDF approximation
  const N = (x: number) => 0.5 * (1 + erf(x / Math.sqrt(2)))
  const n = (x: number) => Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI)
  
  return {
    delta: N(d1),
    gamma: n(d1) / (spot * volatility * Math.sqrt(timeToExpiry)),
    theta: -(spot * n(d1) * volatility) / (2 * Math.sqrt(timeToExpiry)) - 
           riskFreeRate * strike * Math.exp(-riskFreeRate * timeToExpiry) * N(d2),
    vega: spot * n(d1) * Math.sqrt(timeToExpiry) / 100, // Per 1% vol change
    rho: strike * timeToExpiry * Math.exp(-riskFreeRate * timeToExpiry) * N(d2) / 100
  }
}

/**
 * Error function approximation for normal distribution
 */
const erf = (x: number): number => {
  // Abramowitz and Stegun approximation
  const a1 =  0.254829592
  const a2 = -0.284496736
  const a3 =  1.421413741
  const a4 = -1.453152027
  const a5 =  1.061405429
  const p  =  0.3275911

  const sign = x >= 0 ? 1 : -1
  x = Math.abs(x)

  const t = 1.0 / (1.0 + p * x)
  const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x)

  return sign * y
}

/**
 * Convert P&L scenarios to surface plot data
 */
export const convertToSurfaceData = (scenarios: PnLScenario[]): PnLSurfaceData => {
  if (scenarios.length === 0) {
    return {
      priceChanges: [],
      daysToExpiration: [],
      pnlMatrix: []
    }
  }

  const priceChanges = scenarios.map(s => s.priceChange)
  const daysToExpiration = scenarios[0].daysToExpiration
  
  // Create 2D matrix: rows = price changes, columns = days
  const pnlMatrix = scenarios.map(scenario => scenario.pnlValues)
  
  // Calculate metadata
  const allPnLValues = pnlMatrix.flat()
  const maxProfit = Math.max(...allPnLValues)
  const maxLoss = Math.min(...allPnLValues)
  
  // Find breakeven points (closest to 0)
  const breakeven = scenarios
    .filter(s => Math.min(...s.pnlValues.map(Math.abs)) < Math.abs(maxProfit) * 0.05)
    .map(s => s.priceChange)
  
  // Estimate probability of profit
  const profitableScenarios = scenarios.filter(s => 
    s.pnlValues.some(pnl => pnl > 0)
  ).length
  const probabilityOfProfit = profitableScenarios / scenarios.length

  return {
    priceChanges,
    daysToExpiration,
    pnlMatrix,
    metadata: {
      breakeven,
      maxProfit,
      maxLoss,
      probabilityOfProfit
    }
  }
}

/**
 * Generate chart export data
 */
export const generateExportData = (
  scenarios: PnLScenario[],
  greeksData: GreeksTimeSeries[],
  metadata: any
): ChartExportData => ({
  timestamp: new Date().toISOString(),
  chartType: 'combined',
  data: {
    pnlScenarios: scenarios,
    greeksTimeSeries: greeksData
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
    selectedMetrics: ['pnl', 'delta', 'theta']
  },
  metadata: {
    symbol: metadata.symbol || 'UNKNOWN',
    currentPrice: metadata.currentPrice || 0,
    strategy: metadata.strategy || 'calendar',
    analysisDate: new Date().toLocaleDateString()
  }
})

/**
 * Smooth data using moving average for better chart display
 */
export const smoothData = (data: ChartDataPoint[], windowSize: number = 3): ChartDataPoint[] => {
  if (data.length < windowSize) return data
  
  const smoothed: ChartDataPoint[] = []
  
  for (let i = 0; i < data.length; i++) {
    const start = Math.max(0, i - Math.floor(windowSize / 2))
    const end = Math.min(data.length, start + windowSize)
    const window = data.slice(start, end)
    
    const avgY = window.reduce((sum, point) => sum + point.y, 0) / window.length
    
    smoothed.push({
      ...data[i],
      y: avgY
    })
  }
  
  return smoothed
}

/**
 * Find optimal chart bounds for better visualization
 */
export const getOptimalBounds = (data: ChartDataPoint[]): { xMin: number; xMax: number; yMin: number; yMax: number } => {
  if (data.length === 0) {
    return { xMin: 0, xMax: 100, yMin: 0, yMax: 100 }
  }
  
  const xValues = data.map(d => d.x)
  const yValues = data.map(d => d.y)
  
  const xMin = Math.min(...xValues)
  const xMax = Math.max(...xValues)
  const yMin = Math.min(...yValues)
  const yMax = Math.max(...yValues)
  
  // Add 5% padding
  const xPadding = (xMax - xMin) * 0.05
  const yPadding = (yMax - yMin) * 0.05
  
  return {
    xMin: xMin - xPadding,
    xMax: xMax + xPadding,
    yMin: yMin - yPadding,
    yMax: yMax + yPadding
  }
}