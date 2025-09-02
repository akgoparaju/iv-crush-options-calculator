import { AnalysisResult } from '../types/api'

// Offline demo data for PWA functionality
export interface OfflineDataService {
  getSymbols: () => string[]
  getAnalysis: (symbol: string) => Promise<AnalysisResult>
  getMarketData: (symbol: string) => Promise<any>
  storeAnalysis: (symbol: string, analysis: AnalysisResult) => Promise<void>
  getCachedAnalysis: (symbol: string) => Promise<AnalysisResult | null>
  clearCache: () => Promise<void>
  syncPendingData: () => Promise<void>
}

class OfflineDataManager implements OfflineDataService {
  private dbName = 'options-calculator-offline'
  private version = 1
  private db: IDBDatabase | null = null

  constructor() {
    this.initDB()
  }

  private async initDB(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version)
      
      request.onerror = () => reject(request.error)
      request.onsuccess = () => {
        this.db = request.result
        resolve()
      }
      
      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result
        
        // Create object stores
        if (!db.objectStoreNames.contains('analyses')) {
          const analysisStore = db.createObjectStore('analyses', { keyPath: 'symbol' })
          analysisStore.createIndex('timestamp', 'timestamp', { unique: false })
        }
        
        if (!db.objectStoreNames.contains('market-data')) {
          const marketStore = db.createObjectStore('market-data', { keyPath: 'symbol' })
          marketStore.createIndex('timestamp', 'timestamp', { unique: false })
        }
        
        if (!db.objectStoreNames.contains('pending-sync')) {
          db.createObjectStore('pending-sync', { keyPath: 'id', autoIncrement: true })
        }
      }
    })
  }

  getSymbols(): string[] {
    return [
      'AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META', 'NFLX',
      'UBER', 'LYFT', 'SNAP', 'TWTR', 'ZOOM', 'SHOP', 'SQ', 'PYPL',
      'AMD', 'INTC', 'CRM', 'ADBE', 'ORCL', 'IBM', 'CSCO', 'HPQ',
      'BA', 'CAT', 'DE', 'MMM', 'GE', 'F', 'GM', 'FORD'
    ]
  }

  async getAnalysis(symbol: string): Promise<AnalysisResult> {
    // Try to get cached analysis first
    const cached = await this.getCachedAnalysis(symbol)
    if (cached && this.isRecentData(cached.timestamp)) {
      return cached
    }

    // Generate demo analysis if not cached or stale
    const analysis = this.generateDemoAnalysis(symbol)
    await this.storeAnalysis(symbol, analysis)
    return analysis
  }

  async getMarketData(symbol: string): Promise<any> {
    if (!this.db) await this.initDB()

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['market-data'], 'readonly')
      const store = transaction.objectStore('market-data')
      const request = store.get(symbol)

      request.onsuccess = () => {
        const data = request.result
        if (data && this.isRecentData(data.timestamp)) {
          resolve(data.data)
        } else {
          // Generate demo market data
          const demoData = this.generateDemoMarketData(symbol)
          resolve(demoData)
        }
      }

      request.onerror = () => reject(request.error)
    })
  }

  async storeAnalysis(symbol: string, analysis: AnalysisResult): Promise<void> {
    if (!this.db) await this.initDB()

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['analyses'], 'readwrite')
      const store = transaction.objectStore('analyses')
      const data = {
        symbol,
        ...analysis,
        timestamp: new Date().toISOString()
      }

      const request = store.put(data)
      request.onsuccess = () => resolve()
      request.onerror = () => reject(request.error)
    })
  }

  async getCachedAnalysis(symbol: string): Promise<AnalysisResult | null> {
    if (!this.db) await this.initDB()

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['analyses'], 'readonly')
      const store = transaction.objectStore('analyses')
      const request = store.get(symbol)

      request.onsuccess = () => {
        const data = request.result
        if (data) {
          const { symbol: _, ...analysis } = data
          resolve(analysis)
        } else {
          resolve(null)
        }
      }

      request.onerror = () => reject(request.error)
    })
  }

  async clearCache(): Promise<void> {
    if (!this.db) await this.initDB()

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['analyses', 'market-data'], 'readwrite')
      
      const analysisStore = transaction.objectStore('analyses')
      const marketStore = transaction.objectStore('market-data')
      
      const clearAnalyses = analysisStore.clear()
      const clearMarket = marketStore.clear()

      transaction.oncomplete = () => resolve()
      transaction.onerror = () => reject(transaction.error)
    })
  }

  async syncPendingData(): Promise<void> {
    if (!navigator.onLine) return

    if (!this.db) await this.initDB()

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['pending-sync'], 'readwrite')
      const store = transaction.objectStore('pending-sync')
      const request = store.getAll()

      request.onsuccess = async () => {
        const pendingItems = request.result
        
        for (const item of pendingItems) {
          try {
            // Attempt to sync each pending item
            await fetch('/api/analysis', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(item.data)
            })
            
            // Remove from pending if successful
            await this.removePendingItem(item.id)
          } catch (error) {
            console.log('Failed to sync item:', item.id, error)
            // Keep in pending for next sync attempt
          }
        }
        
        resolve()
      }

      request.onerror = () => reject(request.error)
    })
  }

  private async removePendingItem(id: number): Promise<void> {
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['pending-sync'], 'readwrite')
      const store = transaction.objectStore('pending-sync')
      const request = store.delete(id)

      request.onsuccess = () => resolve()
      request.onerror = () => reject(request.error)
    })
  }

  private generateDemoAnalysis(symbol: string): AnalysisResult {
    const basePrice = this.getBasePriceForSymbol(symbol)
    const strike = Math.round(basePrice / 5) * 5 // Round to nearest $5
    
    return {
      success: true,
      symbol,
      current_price: basePrice + (Math.random() - 0.5) * 10,
      timestamp: new Date().toISOString(),
      offline_mode: true,
      
      analysis: {
        term_structure: {
          slope: -0.008 + Math.random() * 0.012, // Random slope around threshold
          front_iv: 0.25 + Math.random() * 0.15,
          back_iv: 0.22 + Math.random() * 0.12,
          meets_threshold: Math.random() > 0.4
        },
        
        iv_rank: {
          current: Math.random() * 100,
          percentile: Math.random() * 100,
          high_52w: 45 + Math.random() * 40,
          low_52w: 10 + Math.random() * 15
        },
        
        volume_analysis: {
          avg_volume: 1000000 + Math.random() * 5000000,
          meets_threshold: Math.random() > 0.3
        },
        
        calendar_trade: {
          strike,
          net_debit: 1.5 + Math.random() * 3,
          max_profit: 3 + Math.random() * 8,
          max_loss: 1.5 + Math.random() * 3,
          probability_of_profit: 0.55 + Math.random() * 0.3,
          days_to_expiration: 25 + Math.floor(Math.random() * 15),
          breakeven_lower: strike - 2 - Math.random() * 3,
          breakeven_upper: strike + 2 + Math.random() * 3
        },
        
        greeks: {
          delta: -0.1 + Math.random() * 0.2,
          gamma: 0.01 + Math.random() * 0.04,
          theta: -0.05 - Math.random() * 0.1,
          vega: 0.08 + Math.random() * 0.15,
          rho: -0.02 + Math.random() * 0.04
        },
        
        risk_metrics: {
          kelly_fraction: Math.random() * 0.05,
          win_rate: 0.6 + Math.random() * 0.25,
          avg_win: 100 + Math.random() * 200,
          avg_loss: -50 - Math.random() * 100,
          profit_factor: 1.2 + Math.random() * 0.8,
          sharpe_ratio: 0.8 + Math.random() * 0.7
        }
      },
      
      earnings: {
        next_earnings: this.getNextEarningsDate(),
        days_until: Math.floor(Math.random() * 30) + 1,
        earnings_move: 0.05 + Math.random() * 0.1
      },
      
      charts: {
        pnl_scenarios: this.generatePnLScenarios(basePrice, strike),
        greeks_evolution: this.generateGreeksEvolution(),
        iv_surface: this.generateIVSurface(basePrice)
      }
    }
  }

  private generateDemoMarketData(symbol: string): any {
    const basePrice = this.getBasePriceForSymbol(symbol)
    
    return {
      symbol,
      price: basePrice + (Math.random() - 0.5) * 10,
      change: (Math.random() - 0.5) * 5,
      change_percent: (Math.random() - 0.5) * 0.05,
      volume: Math.floor(1000000 + Math.random() * 10000000),
      market_cap: Math.floor(50000000000 + Math.random() * 500000000000),
      pe_ratio: 15 + Math.random() * 30,
      timestamp: new Date().toISOString()
    }
  }

  private getBasePriceForSymbol(symbol: string): number {
    const prices: { [key: string]: number } = {
      'AAPL': 175, 'GOOGL': 125, 'MSFT': 330, 'TSLA': 250, 'AMZN': 140,
      'NVDA': 420, 'META': 485, 'NFLX': 440, 'UBER': 65, 'LYFT': 45,
      'SNAP': 35, 'TWTR': 55, 'ZOOM': 85, 'SHOP': 65, 'SQ': 75,
      'PYPL': 85, 'AMD': 115, 'INTC': 45, 'CRM': 215, 'ADBE': 485
    }
    
    return prices[symbol] || (50 + Math.random() * 200)
  }

  private getNextEarningsDate(): string {
    const now = new Date()
    const daysUntil = Math.floor(Math.random() * 30) + 1
    const earningsDate = new Date(now.getTime() + daysUntil * 24 * 60 * 60 * 1000)
    return earningsDate.toISOString().split('T')[0]
  }

  private generatePnLScenarios(basePrice: number, strike: number): any[] {
    const scenarios = []
    const priceRange = basePrice * 0.3
    
    for (let i = 0; i < 21; i++) {
      const price = basePrice - priceRange/2 + (i * priceRange / 20)
      const distance = Math.abs(price - strike) / strike
      const maxPnL = 5 + Math.random() * 3
      const pnl = maxPnL * Math.exp(-distance * 5) - 2.5 + Math.random() * 0.5
      
      scenarios.push({
        underlying_price: Math.round(price * 100) / 100,
        pnl: Math.round(pnl * 100) / 100,
        days_to_expiration: 30 - Math.floor(i / 3)
      })
    }
    
    return scenarios
  }

  private generateGreeksEvolution(): any[] {
    const evolution = []
    
    for (let days = 30; days >= 0; days--) {
      const timeDecay = 1 - (30 - days) / 30
      evolution.push({
        days_to_expiration: days,
        delta: 0.1 * timeDecay + Math.random() * 0.05,
        gamma: 0.03 * timeDecay + Math.random() * 0.01,
        theta: -0.08 * (1 - timeDecay) - Math.random() * 0.02,
        vega: 0.12 * timeDecay + Math.random() * 0.03
      })
    }
    
    return evolution
  }

  private generateIVSurface(basePrice: number): any[] {
    const surface = []
    const strikes = []
    
    // Generate strikes around current price
    for (let i = -10; i <= 10; i++) {
      strikes.push(basePrice + i * 5)
    }
    
    const expirations = [7, 14, 21, 30, 45, 60, 90]
    
    for (const expiration of expirations) {
      for (const strike of strikes) {
        const moneyness = strike / basePrice
        const timeEffect = Math.sqrt(expiration / 30)
        const baseIV = 0.25
        const skew = moneyness < 1 ? (1 - moneyness) * 0.3 : (moneyness - 1) * 0.1
        const iv = baseIV + skew + (Math.random() - 0.5) * 0.05
        
        surface.push({
          strike,
          expiration,
          implied_volatility: Math.max(0.05, iv * timeEffect),
          moneyness: moneyness - 1,
          time_to_expiration: expiration
        })
      }
    }
    
    return surface
  }

  private isRecentData(timestamp: string, maxAgeMinutes: number = 15): boolean {
    const dataTime = new Date(timestamp).getTime()
    const now = Date.now()
    const maxAge = maxAgeMinutes * 60 * 1000
    
    return (now - dataTime) < maxAge
  }
}

// Export singleton instance
export const offlineDataService = new OfflineDataManager()

export default offlineDataService